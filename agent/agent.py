import asyncio
import os
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agent.prompts import SYSTEM_PROMPT
from agent.tools import create_tools
from agent.sql_extraction import extract_generated_sql
from agent.sql_guard import UnsafeSQL, validate_sql
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()
MAX_AGENT_ROUNDS = 5

# Now os.getenv will successfully fetch it from your .env file
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL")

async def execute_generated_sql(session, raw_sql: str) -> str:
    """Validate and execute model-generated read-only SQL."""

    validated_sql = validate_sql(raw_sql)

    result = await session.call_tool(
        name="query",
        arguments={"sql": validated_sql},
    )

    parts = []

    for item in getattr(result, "content", []):
        text = getattr(item, "text", None)

        if text:
            parts.append(text)

    return "\n".join(parts)

async def run_agent():
    # 1. Establish your MCP connection
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres", DATABASE_URL],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize MCP session
            await session.initialize()

            # 2. List tools from MCP and adapt them into LangChain-compatible tool formats
            tools = create_tools(session)
            print("\n=== AVAILABLE TOOLS ===")

            for tool in tools:
                print(f"\nName: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Schema: {tool.args_schema}")
            # Bind the tools directly to the Ollama chat model
            print("Loading model via Ollama (llama3.2:3b)...")
            llm = ChatOllama(
                model="llama3.2:3b",
                temperature=0.3,

            )
            llm = llm.bind_tools(tools)
            # Setup initial conversation history
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            print("AI: Connected to MCP server and Ollama model ready. How can I help you?")

            while True:
                try:
                    user_input = input("You: ")
                except (KeyboardInterrupt, EOFError):
                    break

                if user_input.lower() in ["exit", "quit", "q"]:
                    print("AI: Goodbye!")
                    break
                messages.append(HumanMessage(content=user_input))

                # Agent loop to handle reasoning -> tool call -> response evaluation
                for round_number in range(MAX_AGENT_ROUNDS):
                    # Invoke model with current chat history and bound tools
                    response = llm.invoke(messages)
                    messages.append(response)

                    # Check if model requested any tool calls
                    if response.tool_calls:
                        print(f"\n[Model requested {len(response.tool_calls)} tool call(s)]")
                        for tool_call in response.tool_calls:
                            tool_name = tool_call["name"]
                            tool_args = tool_call["args"]
                            tool_call_id = tool_call["id"]
                            
                            print(f"\n[Executing MCP Tool '{tool_name}' with args {tool_args}]")
                            
                            # Execute via MCP session
                            selected_tool = next(
                                (
                                    tool
                                    for tool in tools
                                    if tool.name == tool_name
                                ),
                                None
                            )

                            if selected_tool is None:
                                raise RuntimeError(
                                    f"Unknown LangChain tool: {tool_name}"
                                )

                            tool_result = await selected_tool.ainvoke(
                                tool_args
                            )

                            print("Tool result:", tool_result)

                            messages.append(
                                ToolMessage(
                                    content=str(tool_result),
                                    tool_call_id=tool_call_id
                                )
                            )
                        
                        # Loop back so the model can read the tool output and write its final reply
                        continue
                    
                    # If no tool calls were requested, print the final text response
                    generated_sql = extract_generated_sql(response.content)

                    if generated_sql is None:
                        print(f"AI: {response.content}\n")
                        break

                    try:
                        query_result = await execute_generated_sql(
                            session,
                            generated_sql,
                        )
                    except UnsafeSQL as exc:
                        print(f"Rejected unsafe SQL: {exc}")

                        messages.append(
                            HumanMessage(
                                content=(
                                    "The generated SQL was rejected by the SQL safety validator. "
                                    f"Reason: {exc}. Generate a corrected read-only SELECT query."
                                )
                            )
                        )
                        continue
                    except Exception as exc:
                        print(f"Database error: {exc}")

                        messages.append(
                            HumanMessage(
                                content=(
                                    "The database query failed. "
                                    f"Error: {exc}. Generate a corrected query."
                                )
                            )
                        )
                        continue

                    messages.append(
                        HumanMessage(
                            content=(
                                "The validated SQL was executed. "
                                "Here is the database result:\n\n"
                                f"{query_result}\n\n"
                                "Explain the result clearly to the user. "
                                "Do not generate another SQL query unless necessary."
                            )
                        )
                    )

                else:
                    print("AI: Maximum agent rounds reached.")

if __name__ == "__main__":
    asyncio.run(run_agent())