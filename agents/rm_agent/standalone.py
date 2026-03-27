# deprecated
import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from utils.rm_agent import RecipeManagerAgent
from mcp.client import sse
from mcp import ClientSession
from utils.mcp_tools import McpTools

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")

client = OpenAI(base_url="https://api.deepseek.com", api_key=DEEPSEEK_API_KEY)


async def main():
    print("Hello from rm-agent!")

    async with sse.sse_client(url=MCP_SERVER_URL) as (read, write):
        print("Connected to MCP server")
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to MCP session")

            mcp_tools = McpTools(client_session=session)

            tools = await mcp_tools.list_tools()
            print(f"Available tools: {len(tools)}")

            agent = RecipeManagerAgent(
                client=client, model="deepseek-chat", tools=tools)
            messages = [
                {"role": "user", "content": "Are there avocado toast recipes available in the system currently?"},]
            # messages = [
            #     {"role": "user", "content": "Hello"},]
            response = agent.call_llm(messages=messages)
            print(f"response: {response}")

            messages = messages + \
                [{"role": "assistant", "content": response.choices[0].message.content}]

            # check if tool call required
            if response.choices[0].message.tool_calls:
                print("Tool call required")
                for tool_call in response.choices[0].message.tool_calls:
                    print(f"Tool call: {tool_call}")
                    await mcp_tools.execute_tool(tool_call)

if __name__ == "__main__":
    asyncio.run(main())
