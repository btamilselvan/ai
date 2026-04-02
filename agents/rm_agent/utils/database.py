import os
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, Integer, String, TEXT, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
import uuid
import json
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
import redis

class Base(AsyncAttrs, DeclarativeBase):
    pass


metadata = Base.metadata


class Messages(Base):
    __tablename__ = "rm_agent_messages"

    id = mapped_column(Integer, primary_key=True,
                       nullable=False, autoincrement="auto")
    thread_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    # role can be user, assistant or system
    role: Mapped[str] = mapped_column(
        String(6), nullable=False, name="user_role")
    # can be declared without mapped_column if the type can be inferred,
    # but adding mapped_column allows us to add additional constraints like nullable, default value etc
    message: Mapped[Optional[str]] = mapped_column(TEXT)
    summary: Mapped[Optional[str]] = mapped_column(TEXT)
    tool: Mapped[Optional[str]] = mapped_column(String(50), name="tool_name")
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(50))
    created_at = mapped_column(TIMESTAMP,
                               default=func.current_timestamp())


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


def _convert_to_messages(thread_id, messages: list[dict]) -> list[Messages]:
    """ convert list of dict messages to list of Messages objects """

    list_of_messages = []
    for message in messages:
        m = Messages()
        m.thread_id = thread_id
        m.role = message["role"]
        m.message = message.get("content")
        m.summary = message.get("summary", None)

        if message["role"] == "tool":
            m.tool = message["name"]
            m.tool_call_id = message["tool_call_id"]

        tool_calls = []
        if message.get("tool_calls", None):
            for tool_call in message.get("tool_calls", []):
                tool_calls.append({
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                    "id": tool_call.id
                })

            print(
                f"tool calls detected, adding to message content...{tool_calls}")
            m.message = message["content"] + \
                "\n Tool Calls: \n" + json.dumps(tool_calls)

        list_of_messages.append(m)

    return list_of_messages


async def save_messages(async_sessionmaker: async_sessionmaker[AsyncSession], r: redis.Redis, thread_id: str, messages: list):
    """ save messages to database """

    async with async_sessionmaker() as session:
        async with session.begin():
            session.add_all(_convert_to_messages(thread_id, messages))
        await session.commit()
    
    # _save_messages_to_redis(r, thread_id, messages)
    return messages

def _save_messages_to_redis(r, thread_id: str, messages: list):
    """ save messages to redis """
    # convert list of Messages objects to list of dict messages
    print(f"converting messages to json for redis storage: {messages}")
    json_messages = convert_messages_to_json(_convert_to_messages(thread_id, messages))
    
    result = None
    if (r.exists(thread_id)):
        # if the thread already exists, we want to append the message to the existing list of messages for that thread
        result = r.json().arrappend(
            thread_id, "$", json_messages)
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
        result = await session.execute(select(Messages).where(Messages.thread_id == thread_id))
        messages = result.scalars().all()
        return messages


def convert_messages_to_dict(messages: list[Messages]) -> list[dict]:
    """ convert list of Messages objects to list of dict messages """

    list_of_dict_messages = []
    for message in messages:
        m = {
            "id": message.id,
            "thread_id": str(message.thread_id),
            "role": message.role,
            "content": message.message,
            "summary": message.summary,
            "tool": message.tool,
            "tool_call_id": message.tool_call_id,
            "created_at": message.created_at.isoformat()
        }
        list_of_dict_messages.append(m)

    return list_of_dict_messages


def convert_messages_to_json(messages: list[Messages]) -> list[dict]:
    """ convert list of Messages objects to json string """
    return [MessageSchema.model_validate(
        m).model_dump(mode='json') for m in messages]
