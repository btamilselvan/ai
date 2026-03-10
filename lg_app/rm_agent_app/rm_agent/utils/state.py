from typing_extensions import TypedDict
from typing import Annotated, List, Optional
import operator

from langchain_core.messages import AnyMessage


class RecipeAppState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    llm_calls: int
    tool_calls: int
