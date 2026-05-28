from pydantic import BaseModel
from typing import List, Dict, Any, Annotated
from langchain_core.messages import AnyMessage
import operator

class AppState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add]
    tournamanets: Dict[str, Any] = {}
    schedules: Dict[str, Any] = {}