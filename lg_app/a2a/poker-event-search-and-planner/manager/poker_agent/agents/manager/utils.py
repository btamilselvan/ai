from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage
from langchain_core.tools import tool


class ManagerAgentResponse(BaseModel):

    """ A structured response model for the Manager Agent to determine the next steps based on the LLM's output. """

    original_model_response: AIMessage = Field(
        description="The original response from the LLM which may contain tool calls and the text response.")

    next_action: Literal["tool_calls", "final_response", "respond_to_user", "delegate_to_planner"] = Field(
        description="The next action to be taken by the manager agent. It can be either 'tool_calls' if there are tool calls to be executed or 'final_response' if the response is final and can be sent back to the user.")


# class PlannerPayload(BaseModel):

#     """ A structured payload model for delegating tasks to the planner agent. """

#     task_description: str = Field(
#         description="A detailed description of the task that needs to be delegated to the planner agent.")


@tool("delegate_to_planner")
def delegate_to_planner_tool(task_description: str):
    """Use this tool when the user wants to check their calendar, see if they are free, 
    or book/schedule a poker tournament."""

    # This function body stays empty! It only exists so the LLM can emit the schema.

    pass
