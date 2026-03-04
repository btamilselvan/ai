import os
import asyncio

from functools import partial
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from cricket_agent.utils.state import MyAppState
from cricket_agent.utils.nodes import llm_node, tool_node_wrapper

# create a session id for the conversation
# session_id = f"session-{random.randint(1000, 9999)}"

# 1 - load environment variables
load_dotenv()

# 2 - System prompt for the agent
SYSTEM_PROMPT = """
You are a helpful assistant that can answer cricket related questions. 
Greet the user and ask them how you can help. 
You can answer questions about cricket rules, players, teams, matches, and history. 
You can also provide live scores and updates if asked. 
Always be polite and informative in your responses.

Tailor your responses to the user's preferred team if mentioned in the conversation.
"""

# setup MCP Client
mcp_client = MultiServerMCPClient(
    {
        "rapidapi_cricbuzz": {
            "command": "npx",
            "transport": "stdio",
            "args": [
                "mcp-remote",
                "https://mcp.rapidapi.com",
                "--header", "x-api-host: cricbuzz-cricket.p.rapidapi.com",
                "--header", f"x-api-key: {os.getenv('RAPIDAPI_API_KEY')}"
            ],
        }
    }
)


async def create_graph():
    # setup tools
    tools = await mcp_client.get_tools()
    mcp_tool_node = ToolNode(tools)

    # setup model
    model = init_chat_model("deepseek-chat", temperature=0, max_tokens=2048)
    model_with_tools = model.bind_tools(tools)

    # Build graph
    graph = StateGraph(MyAppState)

    # Add nodes
    graph.add_node("llm", partial(
        llm_node, model_with_tools=model_with_tools, system_prompt=SYSTEM_PROMPT))
    # tools_condition would result "tools" or "END" so tool_name should be "tools"
    graph.add_node("tools", partial(tool_node_wrapper,
                   tool_node_remote=mcp_tool_node))

    # Configure edges
    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", tools_condition)
    # graph.add_conditional_edges("llm", planner_node, {"tool": "tools", "END": END})
    graph.add_edge("tools", "llm")

    # Compile
    agent = graph.compile()
    print(agent.get_graph().draw_ascii())
    return agent

agent = asyncio.run(create_graph())
