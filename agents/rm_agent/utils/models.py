from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone


class ChatRequest(BaseModel):
    """ User message """
    message: str


class ChatResponse(BaseModel):
    message: str
    role: str


class ToolFunctionInfo(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: ToolFunctionInfo


class ConversationModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, title="MessageSchema")
    id: Optional[int] = Field(default=None)
    thread_id: Optional[UUID] = Field(default=None)
    role: str
    content: Optional[str] = None
    summary: Optional[str] = Field(default=None)
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None
    created_at: datetime = Field(default=datetime.now(timezone.utc))


class AppState(BaseModel):
    thread_id: str
    user_message: str = ""
    messages: list[ConversationModel] = []
    current_agent_name: str = ""
    messages_count: int = 0
