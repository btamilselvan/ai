from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class ChatModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    role: str
    content: str
    # validation_alias - used to name the field in the json input
    # serialization_alias - used to name the field in the json output
    thread_id: str = Field(alias="threadId")
    email: str
    timestampInUtcMillis: int | None = None

class ConversationHistory(BaseModel):
    pass