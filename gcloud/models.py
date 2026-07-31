from pydantic import BaseModel


class MailMessage(BaseModel):
    message_id: str
    subject: str
    sender: str
    body: str | None
    received_on: str
