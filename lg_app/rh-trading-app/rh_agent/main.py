import asyncio
from pydantic import BaseModel
from langchain_core.messages import AnyMessage, AIMessage, ToolMessage, HumanMessage
from typing import Annotated, List
import operator
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient


class AppState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add] = []


mcp_clients = MultiServerMCPClient(
    {
        "robinhood-trading": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "mcp-remote", "https://agent.robinhood.com/mcp/trading"],
        }
    }
)


async def init_model():
    print("initializing model")
    model = init_chat_model(
        "gemma4:e4b", temperature=0, max_tokens=2048, model_provider="ollama"
    )
    tools = await mcp_clients.get_tools()
    global model_with_tools
    model_with_tools = model.bind_tools(tools)
    print(f"found tools {model_with_tools}")


if __name__ == "__main__":
    asyncio.run(init_model())
