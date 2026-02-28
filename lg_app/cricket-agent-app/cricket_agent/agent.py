from functools import partial
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from typing_extensions import TypedDict
from cricket_agent.utils.tools import get_player_stats, get_preferred_team, get_team_rankings, get_upcoming_matches
from cricket_agent.utils.state import MyAppState
from cricket_agent.utils.nodes import llm_node, tool_tode, planner_node

# create a session id for the conversation
# session_id = f"session-{random.randint(1000, 9999)}"

#1 - load environment variables
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

# 3 - define the model
# model = init_chat_model("ollama:llama3.2", temperature=0, max_tokens=2048)
model = init_chat_model("deepseek-chat", temperature=0, max_tokens=2048)

# define tools
tools = [get_upcoming_matches, get_team_rankings, get_player_stats, get_preferred_team]

# map the tool name to the correspodning tool definition
tool_by_name = {tool.name.lower(): tool for tool in tools}

# bind tools to the model
model_with_tools = model.bind_tools(tools)

class GraphContext(TypedDict):
    thread_id: str

graph = StateGraph(MyAppState, context_schema=GraphContext)
# graph.add_node("llm", llm_node(model_with_tools, SYSTEM_PROMPT))
graph.add_node("llm", partial(llm_node, model_with_tools=model_with_tools, system_prompt=SYSTEM_PROMPT))
# graph.add_node("tool", tool_tode, retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0))
graph.add_node("tool", partial(tool_tode, tool_by_name=tool_by_name), retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0))
graph.add_node("planner", planner_node)

## entry point
graph.add_edge(START, "llm")
graph.add_conditional_edges("llm", planner_node, {"tool": "tool", "END": END})
graph.add_edge("tool", "llm")

# 7 - compile the agent
# config = {"configurable": {"thread_id": session_id}}

agent = graph.compile()

print(agent.get_graph().draw_ascii())