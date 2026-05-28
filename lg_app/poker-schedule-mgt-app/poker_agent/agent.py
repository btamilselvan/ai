from poker_agent.agents.manager.nodes import llm_node, tool_node_wrapper, conditional_node, planner_node
from langgraph.graph import StateGraph, START, END
import asyncio
from poker_agent.utils.app_state import AppState
from langchain_mcp_adapters.client import MultiServerMCPClient
import logging
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, tools_condition

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
                    handlers=[logging.StreamHandler()])

logger.info(
    "Poker Schedule Management Agent is starting up...")


async def create_graph():

    app = StateGraph(AppState)
    app.add_node("manager_node", llm_node)

    # tools_condition would result "tools" or "END" so tool_name should be "tools"
    app.add_node("tools", tool_node_wrapper)

    # planner node
    app.add_node("planner", planner_node)

    app.add_edge(START, "manager_node")
    # https://reference.langchain.com/python/langgraph.prebuilt/tool_node/tools_condition
    # tools_condition checks the last message from the LLM node for any tool calls. If there are tool calls, it goes to the "tools" node, otherwise it goes to END.
    # app.add_conditional_edges("manager_node", tools_condition)

    app.add_conditional_edges("manager_node", conditional_node, {
        "tools": "tools",
        "planner": "planner",
        "END": END
    })

    # tools node will execute the tool calls and then go back to the manager_node to get the next response from the LLM based on the tool results. This loop continues until there are no more tool calls required and the planner_node directs it to END.
    app.add_edge("tools", "manager_node")

    # if the conditional node directs to planner_node, it means the manager_node has determined that the task needs to be delegated to the planner agent.
    app.add_edge("planner", "manager_node")

    agent = app.compile()
    logger.info(agent.get_graph().draw_ascii())
    return agent

agent = asyncio.run(create_graph())
