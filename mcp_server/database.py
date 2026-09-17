import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os

# Define your PostgreSQL connection string
# Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE
DATABASE_URL = os.getenv("DATABASE_URL")

async def query_database():
    # 1. Configure the MCP server parameters
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres", DATABASE_URL],
        env=None
    )

    # 2. Connect to the MCP Server over stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection handshake
            await session.initialize()

            # 3. List available database tools exposed by the server
            tools_response = await session.list_tools()
            print("--- Available MCP Tools ---")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")

            # 4. Call the SQL query tool via MCP
            print("\n--- Running Query via MCP ---")
            result = await session.call_tool(
                name="query",
                arguments={"sql": "SELECT name, email FROM customers LIMIT 3;"}
            )
            
            # Print response
            for content in result.content:
                print(content.text)
