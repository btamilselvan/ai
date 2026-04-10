# used for local testing of redis commands and data structure for storing conversation messages in redis. not used in production code.
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
from database import Message, convert_messages_to_dict, convert_messages_to_json, MessageSchema
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


def get_messages_by_thread_id_from_redis(r: redis.Redis, thread_id: str):
    """ get messages by thread id from redis """
    if r.exists(thread_id):
        messages = r.json().get(thread_id, "$")
        print(
            f"messages retrieved from redis for thread_id {thread_id}: {messages}")
        return messages[0] if messages else []
    else:
        print(f"no messages found in redis for thread_id {thread_id}")
        return None

def __summarize_messages(r: redis.Redis, thread_id: str):
    """ summarize messages for a given thread id and save the summary to the database and redis """
    # get messages for the thread id from redis
    messages = get_messages_by_thread_id_from_redis(r, thread_id)
    # messages.reverse()
    if not messages:
        print(f"no messages found in redis for thread_id {thread_id}, skipping summarization")
        return
    messages_to_summarize = []
    # fetch first 5 message for summarization
    # make sure include the most recent assistant message in the messages to be summarized, as that would likely contain the most relevant information for summarization
    if len(messages) >= 7:
        index = 0
        while True:
            messages_to_summarize.append(messages[index])
            print(f"length of messages to summarize: {len(messages_to_summarize)}")
            print(f"length of original messages: {len(messages)}")
            index += 1
            if len(messages_to_summarize) >=5 and messages_to_summarize[-1]["role"] == "user":
                messages_to_summarize.remove(messages_to_summarize[-1])
                break
        print(f"messages to summarize: {messages_to_summarize} length: {len(messages_to_summarize)}")
    else:
        print(
            f"not enough messages to summarize for thread_id {thread_id}, skipping summarization")
        
    summary = Message(id=1, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="system",
                content="summary1", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now())
    
    summary_json = MessageSchema.model_validate(summary).model_dump(mode='json')
    
    trimmed_messages = [summary_json] + messages[len(messages_to_summarize):]
    print(f"messages list: {trimmed_messages}")

load_dotenv()


pool = redis.ConnectionPool(
    host='localhost', port=6379, db=0, max_connections=10)
r = redis.Redis(connection_pool=pool)

ret_val = r.set('foo1', 'bar1', nx=True)
print(f"set command return value: {ret_val}")
print(r.get('foo1'))

ret_val = r.set('foo2', 'bar2', nx=True)
print(f"set command return value: {ret_val}")

r.hset("thread-2", items=["role", "user", "message", "hello world"])
print(r.hgetall("thread-2"))


# class Message(JsonModel):
#     pass


messages: list[Message] = []

messages.append(Message(id=1, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="system",
                content="summary1", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=1, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="user",
                content="hello world", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=2, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                content="hi there!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=21, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="tool",
                content="hi there 21!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=22, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                content="hi there 22!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))

messages.append(Message(id=3, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="user",
                content="hello world3", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=4, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                content="hi there4!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=41, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="tool",
                content="tool call 11!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=42, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                content="processed tool input!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))

messages.append(Message(id=5, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="user",
                content="hello world5", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=6, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                content="hi there6!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))

messages.append(Message(id=7, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="user",
                content="hello world6", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=8, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                content="hi there8!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=9, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="user",
                content="hello world9", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=10, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                content="hi there10!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
# print(messages)

_serialized_messages = [MessageSchema.model_validate(
    m).model_dump(mode='json') for m in messages]

r.json().set("thread-11", "$", _serialized_messages)

__summarize_messages(r, "thread-11")


# class MessageSchema(BaseModel):
#     # This allows Pydantic to read data directly from the SQLAlchemy object
#     # and not just from a dictionary.  This is important because it means we don't have to write a separate schema for the database models.
#     # It allows Pydantic to "scrape" the data out of the database model so it can then be turned into the clean JSON that Redis requires.
#     model_config = ConfigDict(from_attributes=True, title="MessageSchema")

#     id: int
#     thread_id: UUID
#     role: str
#     message: Optional[str] = None
#     summary: Optional[str] = None
#     tool: Optional[str] = None
#     tool_call_id: Optional[str] = None
#     created_at: datetime


# serialize the messages to json
# _serialized_messages = [m.dict() for m in messages]
_serialized_messages = [MessageSchema.model_validate(
    m).model_dump(mode='json') for m in messages]

# print(f" convert the messages to json: {_serialized_messages}")
# print(f" convert the messages to json: {convert_messages_to_json(messages)}")
# print(f" convert the messages to dict: {convert_messages_to_dict(messages)}")

r.json().set("thread-5", "$", _serialized_messages)
# print(f"thread-5: {r.json().get('thread-5', '$')}")

# messages = r.json().get("thread-5", "$")
# messages.append(Messages(id=2, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
#                 content="hi there!", summary="greeting", tool=None, tool_call_id=None, created_at=datetime.now()))

message = Message(id=5, thread_id=UUID("12345678-1234-5678-1234-567812345678"), role="assistant",
                  content="hi there!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now())

# messages.append(MessageSchema.model_validate(message).model_dump(mode='json'))

# r.json().set("thread-4", "$", messages)

print(r.exists("thread-5"))
if (r.exists("thread-6")):
    result = r.json().arrappend("thread-6", "$",
                                MessageSchema.model_validate(message).model_dump(mode='json'))
    print(f"result of appending message to redis: {result}")


print(f"messages from redis thread 6: {r.json().get("thread-6", "$")}")
print("------------------- end of test-------------------")

thread_id = "8c6149d2-eed5-4f58-9258-262ca0f53313"
messages = []
messages.append(Message(id=1, thread_id=UUID(thread_id), role="user",
                content="hello world", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=2, thread_id=UUID(thread_id), role="assistant",
                content="hi there!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))

messages_json = [MessageSchema.model_validate(
    m).model_dump(mode='json') for m in messages]
# print(f"1 - messages json: {messages_json}")

if r.exists(thread_id):
    print(f"messages exist in redis for thread_id {thread_id}")
    messages = r.json().get(thread_id, "$")
    print(
        f"messages retrieved from redis for thread_id {thread_id}: {messages}")
else:
    print(
        f"no messages found in redis for thread_id {thread_id}. setting messages in redis...")
    result = r.json().set(thread_id, "$", messages_json)
    print(f"result of setting messages in redis: {result}")


messages = r.json().get(thread_id, "$")
# print(f"1 - messages retrieved from redis for thread_id {thread_id}: {messages}")

messages = []
messages_json = []
messages.append(Message(id=3, thread_id=UUID(thread_id), role="user",
                content="hello world2", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages.append(Message(id=4, thread_id=UUID(thread_id), role="assistant",
                content="hi there2!", summary="greeting", tool_calls=None, tool_call_id=None, created_at=datetime.now()))
messages_json = [MessageSchema.model_validate(
    m).model_dump(mode='json') for m in messages]

# print(f"2 - messages json: {messages_json}")

if r.exists(thread_id):
    print(
        f"messages exist in redis for thread_id {thread_id}.. appending messages to redis...")
    result = r.json().arrappend(
        thread_id, "$", *messages_json)
    print(f"result of appending messages to redis: {result}")
    messages = r.json().get(thread_id, "$")
    # print(f"all messages: {messages}")


messages = r.json().get(thread_id, "$")
# print(f"2 - messages retrieved from redis for thread_id {thread_id}: {messages}")
