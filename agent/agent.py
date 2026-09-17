import asyncio
import os
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from prompts import SYSTEM_PROMPT
from tools import create_tools

# Now os.getenv will successfully fetch it from your .env file
DATABASE_URL = "postgresql://pokpo:password@localhost:5432/my_app_db"



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
            mcp_tools_response = await session.list_tools()
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
                while True:
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
                    print(f"AI: {response.content}\n")
                    break

if __name__ == "__main__":
    asyncio.run(run_agent())