# # install
# docker run -d --name redis -p 6379:6379 -p 8001:8001 redis:latest

# connect
# docker exec -it redis redis-cli

# pip install redis redis-om

import redis
from dotenv import load_dotenv
from redis_om import JsonModel, Field, Migrator
import json
from redis.commands.json.path import Path
from database import Messages, convert_messages_to_dict, convert_messages_to_json
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

load_dotenv()


pool = redis.ConnectionPool(
    host='localhost', port=6379, db=0, max_connections=10)
r = redis.Redis(connection_pool=pool)

r.set('foo', 'bar')
print(r.get('foo'))

r.hset("thread-2", items=["role", "user", "message", "hello world"])
print(r.hgetall("thread-2"))


# class Message(JsonModel):
#     pass


messages: list[Messages] = []

messages.append(Messages(id=1, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="user",
                message="hello world", summary="greeting", tool=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Messages(id=2, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                message="hi there!", summary="greeting", tool=None, tool_call_id=None, created_at=datetime.now()))

# print(messages)


class MessageSchema(BaseModel):
    # This allows Pydantic to read data directly from the SQLAlchemy object
    # and not just from a dictionary.  This is important because it means we don't have to write a separate schema for the database models.
    # It allows Pydantic to "scrape" the data out of the database model so it can then be turned into the clean JSON that Redis requires.
    model_config = ConfigDict(from_attributes=True, title="MessageSchema")

    id: int
    thread_id: UUID
    role: str
    message: Optional[str] = None
    summary: Optional[str] = None
    tool: Optional[str] = None
    tool_call_id: Optional[str] = None
    created_at: datetime


# serialize the messages to json
# _serialized_messages = [m.dict() for m in messages]
_serialized_messages = [MessageSchema.model_validate(
    m).model_dump(mode='json') for m in messages]

print(f" convert the messages to json: {_serialized_messages}")
print(f" convert the messages to json: {convert_messages_to_json(messages)}")
print(f" convert the messages to dict: {convert_messages_to_dict(messages)}")

r.json().set("thread-5", "$", _serialized_messages)
print(f"thread-5: {r.json().get('thread-5', '$')}")

# messages = r.json().get("thread-5", "$")
# messages.append(Messages(id=2, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
#                 message="hi there!", summary="greeting", tool=None, tool_call_id=None, created_at=datetime.now()))

message = Messages(id=5, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                message="hi there!", summary="greeting", tool=None, tool_call_id=None, created_at=datetime.now())

# messages.append(MessageSchema.model_validate(message).model_dump(mode='json'))

# r.json().set("thread-4", "$", messages)

print(r.exists("thread-5"))

result = r.json().arrappend("thread-6", "$", MessageSchema.model_validate(message).model_dump(mode='json'))
print(f"result of appending message to redis: {result}")

print(f"messages from redis thread 6: {r.json().get("thread-6", "$")}")

