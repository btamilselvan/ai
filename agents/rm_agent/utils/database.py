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

            print(f"tool calls detected, adding to message content...{tool_calls}")
            m.message = message["content"] + \
                "\n Tool Calls: \n" + json.dumps(tool_calls)

        list_of_messages.append(m)

    return list_of_messages


async def save_messages(async_sessionmaker: async_sessionmaker[AsyncSession], thread_id: str, messages: list):
    """ save messages to database """

    async with async_sessionmaker() as session:
        async with session.begin():
            session.add_all(_convert_to_messages(thread_id, messages))
        await session.commit()


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
