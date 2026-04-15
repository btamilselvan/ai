# used for local testing of redis commands and data structure for storing conversation messages in redis. not used in production code.
# # install
# docker run -d --name redis -p 6379:6379 -p 8001:8001 redis:latest

# connect
# docker exec -it redis redis-cli

# uv run python -m datastore.redis_test

# pip install redis redis-om
import os
import redis
from dotenv import load_dotenv
from redis_om import JsonModel, Field, Migrator
import json
from redis.commands.json.path import Path
from datastore.database import Message, convert_messages_to_dict, convert_messages_to_json, Conversation
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, TEXT, TIMESTAMP, func
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy import select, Integer, String, TEXT, TIMESTAMP, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from utils.models import AppState, ConversationModel, ToolCall, ToolFunctionInfo

print(f"version {sqlalchemy.__version__}")

load_dotenv()

DB_URL = os.getenv("DATABASE_URL_SYNC")
# Lazy initialization
# engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
engine = create_engine(DB_URL, echo=True)

print("connection created...")


pool = redis.ConnectionPool(
    host='localhost', port=6379, db=0, max_connections=10)
r = redis.Redis(connection_pool=pool)

ret_val = r.set('foo1', 'bar1', nx=True)
# print(f"set command return value: {ret_val}")
# print(r.get('foo1'))

ret_val = r.set('foo2', 'bar2', nx=True)
# print(f"set command return value: {ret_val}")

r.hset("thread-2", items=["role", "user", "message", "hello world"])

messages = []

thread_id = "8c6149d2-eed5-4f58-9258-262ca0f53314"

user_message = "hello world"


c1 = ConversationModel(thread_id=UUID(thread_id), role="user",
                       content="hello world", summary=None,
                       tool_calls=[ToolCall(id="call_1", type="function", function=ToolFunctionInfo(name="search", arguments=""))], tool_call_id=None, created_at=datetime.now())

# c1 = ConversationModel(thread_id=UUID(thread_id), role="user",
#                 content="hello world", summary=None,
#                 tool_calls=[], tool_call_id=None, created_at=datetime.now())

messages.append(c1)
messages.append(ConversationModel(thread_id=UUID(thread_id), role="assistant",
                content="hi there!", summary=None, tool_calls=None, tool_call_id=None, created_at=datetime.now()))

app_state = AppState(thread_id=thread_id, messages=messages,
                     history=messages, user_message=user_message, current_agent_name="test")

# print(f"appstate: {app_state.model_dump()}")

status = r.json().set(thread_id, "$", app_state.model_dump(mode="json"))
print(f"redis set status {status}")

# convert pydantic model to json to entity
# json_results = [ConversationModel(**r).model_dump(mode='json') for r in messages]
entities = [Conversation(**c1.model_dump(exclude_none=True))]

print(f"entities: {entities}")

saved_state = r.json().get(thread_id, "$")
print(f"saved_state {saved_state[0]}")
st = type(saved_state[0])
print(st)
# data_dict = json.loads(saved_state[0])
saved_state_obj = AppState.model_validate(saved_state[0])
print(f"saved_state {saved_state_obj}")

conversations = []
# conversations.append(ConversationModel(thread_id=UUID(thread_id), role="user",
#                 content="hello world", summary=None, tool_calls=None, tool_call_id=None, created_at=datetime.now()))

with Session(engine) as session:
    result = session.add_all(entities)
    session.commit()

result = []
stmt = select(Conversation).where(Conversation.thread_id ==
                                  UUID("8c6149d2-eed5-4f58-9258-262ca0f53313"))
with Session(engine) as session:
    # result = session.execute(stmt).first()
    result = session.execute(stmt).all()
    # print(f"first result {result[0]}")

# print(f"result: {result} ")
for row in result:
    print(f"row : {row}")
    print(f"row: {row[0]}")
    print(f"thread id: {row[0].id}")
    print(f"tool calls: {row[0].tool_calls}")
    tt = type(row[0].tool_calls)
    print(f"type of tool calls: {tt}")
    rr = ConversationModel.model_validate(row[0]).model_dump(mode='json')
    print(f"row converted to json: {rr}")
    # pass

# convert entity to pydantic model
# results = [ConversationModel.model_validate(r[0]).model_dump(mode='json') for r in result ]
# print(f"results: {results} ")

# convert pydantic model to json to entity
# json_results = [ConversationModel(**r).model_dump(mode='json') for r in results]

# print(f"results: {json_results} ")
