from pydantic import BaseModel, Field


class ChatModel(BaseModel):
    message: str
    # validation_alias - used to name the field in the json input
    # serialization_alias - used to name the field in the json output
    thread_id: str = Field(validation_alias="threadId", serialization_alias="threadId")
    email: str
