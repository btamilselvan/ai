from pydantic import BaseModel


class ChatRequest(BaseModel):
    """ User message """
    message: str


class ChatResponse(BaseModel):
    message: str
    role: str