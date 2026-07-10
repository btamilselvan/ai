from poker_agent.utils.app_state import AppState
from langchain_core.messages import AIMessage
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
import logging
from dotenv import load_dotenv
import asyncio
from langgraph.prebuilt import ToolNode
from poker_agent.agents.manager.utils import (
    ManagerAgentResponse,
    delegate_to_planner_tool,
)
from poker_agent.agents.manager.remote_tool import register_remote_agent
from typing import Literal

load_dotenv()

SYSTEM_PROMPT_WITH_PLANNER_AGENT_1 = """

You are an expert poker travel coordinator and the lead orchestrator of this application. Your goal is to help the user find live poker tournaments in the US and seamlessly integrate them into their personal schedule.

You have access to two distinct resources:
1. `poker tournament search` (MCP Tool): You must use this to look up tournament schedules, buy-ins, locations, and structures. Do not hallucinate or guess data.
2. The Planner Agent (Specialist): This is a separate autonomous agent that manages the user's personal calendar, checks for scheduling conflicts, and books slots.

CRITICAL INSTRUCTIONS FOR ROUTING:
- Whenever the user expresses an intent to attend a tournament, check their availability, or book a date (e.g., "Am I free for this?", "Book the Wynn event", "Add this to my calendar"), you MUST delegate the task to the Planner Agent. You must include a clear message that should be sent to the Planner Agent describing the user's request and the relevant tournament details. The planner agent message should be included as an argument in the `delegate_to_planner` tool call. The argument name should be `task_description`. The Planner Agent will handle all calendar-related tasks, including checking for conflicts and booking.
- To hand off control to the Planner Agent, explicitly state in your internal tracking that the Planner needs to be invoked, or set the execution flow to target the planner.
- Do not attempt to manage the calendar or resolve time-zone conflicts yourself. You are the poker data and communication expert; the Planner is the calendar domain expert.

Maintain a professional, helpful tone. When the Planner Agent returns its findings (such as conflicts or confirmation), synthesize those results and present them clearly to the user.
"""

SYSTEM_PROMPT_WITH_PLANNER_AGENT = """
You are an expert poker travel coordinator and the lead orchestrator of this application. Your goal is to help users find live poker tournaments in the US and seamlessly integrate them into their personal schedules.

To assist the user, you have access to external capabilities that allow you to search for real-time poker data and interact with the user's personal calendar. 

CRITICAL OPERATIONAL RULES:
1. Data Accuracy: When looking up tournament schedules, buy-ins, locations, and structures, always rely entirely on your external search capabilities. Do not hallucinate, guess, or estimate tournament data.
2. Calendar & Scheduling Delegation: You are the poker data and communication expert, not a scheduling system. You must never attempt to manually calculate availability, manage calendar slots, or resolve time-zone conflicts yourself. 
3. Handoff Trigger: Whenever the user wants to check their availability, add an event, or book a tournament (e.g., "Am I free?", "Book this", "Put it on my calendar"), you must immediately invoke the appropriate scheduling capability. You must construct a clear, detailed description of the user's request and the relevant tournament details to pass into that capability.

Maintain a professional, helpful tone. When the external systems return data (such as search results, scheduling conflicts, or booking confirmations), synthesize those results and present them clearly and elegantly to the user.

"""



def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


async def configure_model_and_tools():
    model = init_chat_model(
        "gemma4:e4b", temperature=0, max_tokens=2048, model_provider="ollama"
    )
    mcp_client = MultiServerMCPClient(
        {
            "poker_scout_mcp": {
                "transport": "streamable-http",
                "url": "http://localhost:8003/mcp",
            }
        }
    )
    
    planner_agent_tools = register_remote_agent("Planner Agent", "http://localhost:9000")
    
    tools = await mcp_client.get_tools(server_name="poker_scout_mcp")
    # filter non poker agent search tools
    tools = [tool for tool in tools if "poker_agent" in tool.name] + planner_agent_tools

    global tool_node
    tool_node = ToolNode(tools)

    logger.info(f"Retrieved tools for poker_scout_mcp: {tools}")
    model_with_tools = model.bind_tools(tools)
    return model_with_tools


configure_logging()
logger = logging.getLogger(__name__)

model_with_tools = asyncio.run(configure_model_and_tools())
model = init_chat_model(
    "gemma4:e4b", temperature=0, max_tokens=2048, model_provider="ollama"
)


def llm_node(app_state: AppState) -> AppState:
    """This node calls the LLM with the current messages and updates the state with the response."""

    manager_response = model_with_tools.invoke(
        [SYSTEM_PROMPT_WITH_PLANNER_AGENT] + app_state.messages
    )

    # manager_response = model.with_structured_output(ManagerAgentResponse).invoke(
    #     [SYSTEM_PROMPT] + app_state.messages)

    # logger.info(f"LLM response: {model_response}")
    logger.info(f"Manager response: {manager_response}")

    return AppState(messages=[manager_response])


def conditional_node(app_state: AppState) -> Literal["tools", "planner", "END"]:
    """
    This node checks the last message from the LLM node for any tool calls.
    If there are tool calls, it checks if it's a delegation to the planner agent or a regular tool call and routes accordingly.
    If there are no tool calls, it routes to END.
    """
    logger.info(
        f"Checking for tool calls in the last message: {app_state.messages[-1]}"
    )
    ai_message: AIMessage = app_state.messages[-1]

    if not ai_message.tool_calls:
        return "END"
    
    return "tools"

    # if ai_message.tool_calls[0]["name"] == "delegate_to_planner":
    #     logger.info(
    #         "Planner delegation tool call found. Routing to planner node for planner delegation."
    #     )
    #     return "planner"
    # else:
    #     logger.info(
    #         "Tool calls found, but not for planner delegation. Routing to tools node."
    #     )
    #     return "tools"


async def tool_node_wrapper(app_state: AppState):
    """This node executes the tool calls in the last message and updates the state with the results.
    It then routes back to the LLM node to get the next response based on the tool results.
    """

    # logger.info(f"Executing tool node wrapper with app_state: {app_state}")
    logger.info(f"Executing tool node wrapper with tool_node: {tool_node}")
    # https://reference.langchain.com/python/langgraph.prebuilt/tool_node/ToolNode
    # tool_node.ainvoke takes the current state as input and executes the tool calls in the last message.
    # It returns the results of the tool calls which can be used to update the state.
    result = await tool_node.ainvoke(app_state)
    logger.info(f"Tool node result: {result}")
    return result


async def planner_node(app_state: AppState):

    logger.info(f"Executing planner node with last message: {app_state.messages[-1]}")

    # retrieve the tool call arguments for delegation to planner from the last message
    ai_message: AIMessage = app_state.messages[-1]
    if (
        not ai_message.tool_calls
        or ai_message.tool_calls[0]["name"] != "delegate_to_planner"
    ):
        logger.error("No planner delegation tool call found in the last message.")
        return app_state

    task_description = ai_message.tool_calls[0]["args"].get("task_description", None)
    if not task_description:
        logger.error(
            "No task description found in the tool call arguments for planner delegation."
        )
        return app_state

    logger.info(f"Delegating to planner with task description: {task_description}")

    return app_state
