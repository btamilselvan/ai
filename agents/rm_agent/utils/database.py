import os
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, Integer, String, TEXT, TIMESTAMP, func, JSON
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
import uuid
import json
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import redis


class Base(AsyncAttrs, DeclarativeBase):
    pass


metadata = Base.metadata


class Message(Base):
    __tablename__ = "rm_agent_messages"

    id = mapped_column(Integer, primary_key=True,
                       nullable=False, autoincrement="auto")
    thread_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    # role can be user, assistant or system
    role: Mapped[str] = mapped_column(
        String(6), nullable=False, name="user_role")
    # can be declared without mapped_column if the type can be inferred,
    # but adding mapped_column allows us to add additional constraints like nullable, default value etc
    content: Mapped[Optional[str]] = mapped_column(TEXT, name="message")
    summary: Mapped[Optional[str]] = mapped_column(TEXT)
    tool_calls: Mapped[Optional[JSON]] = mapped_column(JSON, name="tool_calls")
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(50))
    created_at = mapped_column(TIMESTAMP,
                               default=func.current_timestamp())


class MessageSchema(BaseModel):
    # This allows Pydantic to read data directly from the SQLAlchemy object
    # and not just from a dictionary.  This is important because it means we don't have to write a separate schema for the database models.
    # It allows Pydantic to "scrape" the data out of the database model so it can then be turned into the clean JSON that Redis requires.
    model_config = ConfigDict(from_attributes=True, title="MessageSchema")

    id: int = Field(exclude=True)
    thread_id: UUID = Field(exclude=True)
    role: str
    content: Optional[str] = None
    summary: Optional[str] = Field(exclude=True)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    created_at: datetime


def _convert_to_messages(thread_id, messages: list[dict]) -> list[Message]:
    """ convert list of dict messages to list of Message objects compatible with the database schema """

    list_of_messages = []
    for message in messages:
        # print(f"converting message to Message object: {message}")
        m = Message()
        m.thread_id = thread_id
        m.role = message["role"]
        m.content = message.get("content", None)
        m.summary = message.get("summary", None)
        m.tool_call_id = message.get("tool_call_id", None)

        tool_calls = []
        if message.get("tool_calls", None):
            for tool_call in message.get("tool_calls", []):
                # print(type(tool_call))
                # print(f"tool call: {tool_call}")
                tool_calls.append({
                    "type": tool_call.type,
                    "id": tool_call.id,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

            # print(
            #     f"tool calls detected, adding to message content...{tool_calls}")
            # store tool_calls in the format expected by OpenAI chat completions API, which is a list of dicts with keys type, id and function (which is another dict with name and arguments)
            m.tool_calls = tool_calls

        list_of_messages.append(m)

    return list_of_messages


async def save_messages(async_sessionmaker: async_sessionmaker[AsyncSession], r: redis.Redis, thread_id: str, messages: list):
    """ save messages to database """

    messages_to_save = _convert_to_messages(thread_id, messages)
    async with async_sessionmaker() as session:
        async with session.begin():
            session.add_all(messages_to_save)
        await session.commit()
    print(f"messages saved to database for thread_id: {thread_id}")
    _save_messages_to_redis(r, thread_id, messages_to_save)
    return messages


def _save_messages_to_redis(r, thread_id: str, messages: list):
    """ save messages to redis """
    # convert list of Messages objects to list of dict messages
    # print(f"converting messages to json for redis storage: {messages}")
    # json_messages = convert_messages_to_json(_convert_to_messages(thread_id, messages))
    json_messages = convert_messages_to_json(messages)

    # print(f"json messages to be stored in redis: {json_messages}")

    result = None
    if (r.exists(thread_id)):
        # if the thread already exists, we want to append the message to the existing list of messages for that thread.
        # unpack the list of json messages so that each message is appended as a separate element in the redis list
        result = r.json().arrappend(
            thread_id, "$", *json_messages)
    else:
        # if the thread does not exist, we want to create a new list of messages for that thread and add the message to that list
        result = r.json().set(thread_id, "$", json_messages)

    print(f"result of storing message in redis: {result}")
    return result


# async def save_message(async_sessionmaker, thread_id: str, role: str,
#                        content: Optional[str] = None, summary: Optional[str] = None,
#                        tool: Optional[str] = None, tool_call_id: Optional[str] = None):
#     """ save message to database """
#     print(
#         f"saving message to database with thread_id: {thread_id}, role: {role}, message: {content}, summary: {summary}, tool: {tool}, tool_call_id: {tool_call_id}")
#     async with async_sessionmaker() as session:
#         async with session.begin():
#             session.add(Messages(thread_id=thread_id, role=role, message=content, summary=summary,
#                         tool=tool, tool_call_id=tool_call_id))
#         await session.commit()


async def get_messages_by_thread_id(async_sessionmaker, thread_id: str):
    """ get messages by thread id """
    async with async_sessionmaker() as session:
        result = await session.execute(select(Message).where(Message.thread_id == thread_id))
        messages = result.scalars().all()
        return messages


def convert_messages_to_dict(messages: list[Message]) -> list[dict]:
    """ convert list of Messages objects to list of dict messages """

    list_of_dict_messages = []
    for message in messages:
        m = {
            "id": message.id,
            "thread_id": str(message.thread_id),
            "role": message.role,
            "content": message.content,
            "summary": message.summary,
            "tool_calls": message.tool_calls,
            "tool_call_id": message.tool_call_id,
            "created_at": message.created_at.isoformat()
        }
        list_of_dict_messages.append(m)

    return list_of_dict_messages


def convert_messages_to_json(messages: list[Message]) -> list[dict]:
    """ convert list of Message objects to json string """
    return [MessageSchema.model_validate(
        m).model_dump(mode='json') for m in messages]


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
