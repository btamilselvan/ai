## this script demonstrates the creation of a AI agent using LangGraph to answer cricket related questions with the help of some tools.
## The agent uses a state graph to manage the conversation flow and tool usage.
# The user queries are always directed to the llm_node and then to the planner_node
# The planner_node decides whether to call the tool or not based on the response from the llm_node.
#### Work flow 
# The agent has three main nodes: llm_node, tool_node, and planner_node.
# The user query is always routed to the llm node first, then to the planner node. 
# The planner node will check if the llm response contains any tool calls. 
# If llm response contains tool calls, the planner_node will route the control to the tool_node.
# The tool_node will execute the tool and return the result.
# The result will be appended to the messages list and the control will be routed back to the llm_node.
# The llm_node will generate a response based on the tool result and the user query.
# Then again the control will be routed to the planner node. and the planner node will return END since there are no more tools to make.

import operator, random
from typing import Optional, List, Literal, Annotated
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AnyMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import RetryPolicy, Command, interrupt
from typing_extensions import TypedDict
from cricket_tools import get_player_stats, get_preferred_team, get_team_rankings, get_upcoming_matches

# create a session id for the conversation
session_id = f"session-{random.randint(1000, 9999)}"

#1 - load environment variables
load_dotenv()

# 2 - System prompt for the agent
SYSTEM_PROMPT = """
You are a helpful assistant that can answer cricket related questions. 
Greet the user and ask them how you can help. 
You can answer questions about cricket rules, players, teams, matches, and history. 
You can also provide live scores and updates if asked. 
Always be polite and informative in your responses.
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

# 4 - define app state
class MyAppState(TypedDict):
    preferred_team: Optional[str]
    
    #conversation history
    # This tells LangGraph: "Don't overwrite 'messages', just append new ones"
    messages: Annotated[List[AnyMessage], operator.add]
    llm_calls: int
    tool_calls: int

# 5 - define nodes
# 5.1 - LLM node
def llm_node(state: MyAppState):
    """ Call LLM with the current messages and update the state with the response. """
    
    print("execute LLM Node \n")
    
    print(f"current state {state.get("preferred_team", None)}")
    # preferred_team = ""
    # Check if preferred_team is present in the state
    if not state.get("preferred_team"):
        print("No preferred team found. Requesting from user...\n")
        # Interrupt and ask for preferred team (at this point execution stops) control transferred to the caller.
        # When the user provides the team, the execution resumes and the node will be re-executed from the beginning.
        preferred_team = interrupt({"message": "Enter your preferred team:", "prompt": "Please enter your preferred team: "})
        print(f"User's preferred team: {preferred_team}\n")
        # Update state and re-execute the node (we can also resume the execution without re-executing but make sure to update the state with preferred_team)
        return Command(update={"preferred_team": preferred_team}, goto="llm")
        # state = {"preferred_team": preferred_team}
    
    llm_calls = state.get("llm_calls", 0) + 1
    messages = state.get("messages", []).copy()
    
    # Call the model with the system prompt and the current messages
    response = model_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + messages)
    
    print(f"LLM response: {response}\n")
    
    # Return both preferred_team and messages updates. This will be appended to the existing list of messages.
    return Command(update={"messages": [response], "llm_calls": llm_calls})
    # return MyAppState(messages=[response], llm_calls=llm_calls)

# 5.2 - tool node
# Always return the control to llm node
def tool_tode(state: MyAppState) -> Command[Literal["llm"]]:
    """ Execute tools based on the AI message containing tool calls. """
    
    print("execute Tools Node \n")
    
    try:
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        # print(f"Last message: {last_message}")
        # print("\n")

        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            print("No tool calls found in the last message.")
            return state
        
        tool_result = []
        tool_calls = 0
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"].lower()
            tool_args = tool_call["args"]

            print(f"Tool name: {tool_name}")
            # print(f"Tool args: {tool_args}")
            print("\n")
            
            tool_response = tool_by_name[tool_name].invoke(tool_args)

            print(f"Tool response: {tool_response}")
            tool_result.append(ToolMessage(content=str(tool_response), tool_call_id=tool_call["id"]))
            # print(f"tool result: {tool_result}")
            tool_calls = state.get("tool_calls", 0) + 1
            
            return Command(update={"messages": tool_result, "tool_calls": tool_calls}, goto="llm")
    except Exception as e:
        print(f"Error executing tools: {e}")
        tool_result.append(ToolMessage(content=f"Tool error occurred {str(e)}", tool_call_id=tool_call["id"]))
        return Command(update={"messages": tool_result, "tool_calls": tool_calls}, goto="llm")
    
    
  
    #return the new messages. this will be appended to the existing list of messages.
    return {"messages": tool_result, "tool_calls": tool_calls}

# 5.3 - conditional edge (decide whether to call the tool or not)
def planner_node(state: MyAppState) -> Literal["tool", "END"]:
    """ Decide whether to call the tool or not. """
    
    print("execute planner Node \n")
    
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    #if there are no tool calls required, end the conversation. the last_message (llm message will have a tool_calls attribute)
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool"
    else:
        return "END"

def handle_interrupt(chat_state: MyAppState) -> MyAppState:
    """ Handle interrupt by asking user for input and resuming execution. """
    
    # Check if we hit an interrupt
    if not chat_state.get("__interrupt__"):
        return chat_state
    
    print("Handling interrupt...\n")
    
    resume_map = {}
    # Extract interrupt details - handle multiple parallel interrupts
    for interrupt in chat_state['__interrupt__']:
        print(f"Interrupt type: {interrupt.id}")
        print(f"Interrupt value: {interrupt.value}")
        interrupt_value = interrupt.value
        if(isinstance(interrupt_value, dict)):
            prompt = interrupt_value.get("prompt", "Please provide input: ")
        else:
            prompt = str(interrupt_value)
        
        while(True):
            # Get user input
            user_response = input(prompt)
            if(len(user_response.strip()) > 0):
                break
        
        resume_map[interrupt.id] = user_response
    
    chat_state = agent.invoke(Command(resume=resume_map), config=config)
    
    # interrupt_value = chat_state['__interrupt__'][0].value
    # # Get the prompt message (with fallback)
    # if isinstance(interrupt_value, dict):
    #     prompt = interrupt_value.get("prompt", "Please provide input: ")
    # else:
    #     prompt = str(interrupt_value)
    # while(True):
        
    #     # Get user input
    #     user_response = input(prompt)
    #     if(len(user_response.strip()) > 0):
    #         break
        
    # # Resume execution with user's response
    # chat_state = agent.invoke(Command(resume=user_response), config=config)
    
    return chat_state

# 6 - build the agent graph
graph = StateGraph(MyAppState)
graph.add_node("llm", llm_node)
graph.add_node("tool", tool_tode, retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0))
graph.add_node("planner", planner_node)

## entry point
graph.add_edge(START, "llm")
graph.add_conditional_edges("llm", planner_node, {"tool": "tool", "END": END})
graph.add_edge("tool", "llm")

# 7 - compile the agent
config = {"configurable": {"thread_id": session_id}}
memory = InMemorySaver()
agent = graph.compile(checkpointer=memory)

# print(agent.get_graph().draw_ascii())

# 8 - invoke the agent with an initial message
chat_state: MyAppState = {"messages": [HumanMessage(content="Can you introduce yourself?")], "llm_calls": 0}

# First invocation - will hit the interrupt
chat_state = agent.invoke(chat_state, config=config)

# Check if we hit an interrupt
chat_state = handle_interrupt(chat_state)  # Handles if interrupt exists, otherwise returns as-is

# if chat_state.get("__interrupt__"):
#     print(f"Interrupt: {chat_state['__interrupt__'][0].value}\n")
#     user_team = input("Your preferred team: ")
#     # Resume with the user's input
#     chat_state = agent.invoke(Command(resume=user_team), config=config)

print(f"Agent: {chat_state['messages'][-1].content}")
print("\n")

# 9 - continue the conversation with user input
number_of_queries = 1
for i in range(number_of_queries):
    user_input = input("You: ")
    chat_state["messages"].append(HumanMessage(content=user_input))
    chat_state = agent.invoke(chat_state, config=config)
    chat_state = handle_interrupt(chat_state)  # Handles if interrupt exists, otherwise returns as-is

    # print(chat_state)
    print(f"Agent: {chat_state['messages'][-1].content}")
    # print("\n")
    # print(f"LLM calls so far: {chat_state['llm_calls']}")

print(f"total messages count {chat_state.get('messages', []).count}")
print(f"total llm calls count {chat_state.get('llm_calls', 0)}")
print(f"total tool calls count {chat_state.get('tool_calls', 0)}")

# memory.