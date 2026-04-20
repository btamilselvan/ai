# uv run python -m utils.mcp_test

from fastmcp import Client
from fastmcp.client.transports import SSETransport
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

API_KEY = os.getenv("MCP_SERVER_API_KEY")


sse_transport = SSETransport(url="http://localhost:8002/sse", headers={
    "x-api-key": API_KEY})
client = Client(transport=sse_transport)


async def main():
    async with client:
        await client.ping()
        print("ping...")
        tools = await client.list_tools()
        print(f"tools available {tools}")
        
        resources = await client.list_resources()
        print(f"resources available {resources}")

if __name__ == "__main__":
    asyncio.run(main())
