from pydantic import BaseModel
from typing import List, Dict, Any

class AppState(BaseModel):
    messages: List[Dict[str, Any]]
    tournamanets: Dict[str, Any] = {}
    schedules: Dict[str, Any] = {}