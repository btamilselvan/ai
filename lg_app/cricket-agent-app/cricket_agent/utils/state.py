import operator
from typing import Optional, Annotated, List
from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict

class MyAppState(TypedDict):
    preferred_team: Optional[str]
    
    #conversation history
    # This tells LangGraph: "Don't overwrite 'messages', just append new ones"
    messages: Annotated[List[AnyMessage], operator.add]
    llm_calls: int
    tool_calls: int