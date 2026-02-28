from cricket_agent.utils.state import MyAppState
from langgraph.types import interrupt, Command
from langchain.messages import SystemMessage, AIMessage, ToolMessage
from typing import Literal

# LLM Node
def llm_node(state: MyAppState, model_with_tools, system_prompt: str):
    """ Call LLM with the current messages and update the state with the response. """
    
    print("execute LLM Node \n")
    
    preferred_team = state.get("preferred_team", None)
    print(f"User's preferred team: {preferred_team}\n")

    # Check if preferred_team is present in the state
    if not state.get("preferred_team"):
        print("No preferred team found. Requesting from user...\n")
        # Interrupt and ask for preferred team (at this point execution stops) control transferred to the caller.
        # When the user provides the team, the execution resumes and the node will be re-executed from the beginning.
        preferred_team = interrupt({"message": "Enter your preferred team:", "prompt": "Please enter your preferred team: "})
        print(f"User's preferred team: {preferred_team}\n")
        # Update state and re-execute the node (we can also resume the execution without re-executing but make sure to update the state with preferred_team)
        # return Command(update={"preferred_team": preferred_team}, goto="llm")
        # state = {"preferred_team": preferred_team}
    
    llm_calls = state.get("llm_calls", 0) + 1
    messages = state.get("messages", []).copy()
    
    # Call the model with the system prompt and the current messages
    response = model_with_tools.invoke([SystemMessage(content=system_prompt)] + messages)
    
    # print(f"LLM response: {response}\n")
    
    # Return both preferred_team and messages updates. This will be appended to the existing list of messages.
    # return Command(update={"messages": [response], "llm_calls": llm_calls})
    return MyAppState(messages=[response], llm_calls=llm_calls, preferred_team=preferred_team)

# 5.2 - tool node
# Always return the control to llm node
def tool_tode(state: MyAppState, tool_by_name) -> Command[Literal["llm"]]:
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
