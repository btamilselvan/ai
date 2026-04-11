from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy import select, Integer, String, TEXT, TIMESTAMP, func, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import redis
import logging

logger = logging.getLogger(__name__)


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
        # logger.debug("converting message to Message object: %s", message)
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


async def save_messages_to_pg(async_sessionmaker: async_sessionmaker[AsyncSession], thread_id: str, messages: list):
    """ save messages to database """

    messages_to_save = _convert_to_messages(thread_id, messages)
    async with async_sessionmaker() as session:
        async with session.begin():
            session.add_all(messages_to_save)
        await session.commit()
    logger.debug("messages saved to database for thread_id: %s", thread_id)

    return messages_to_save


def get_messages_to_summarize(r: redis.Redis, thread_id: str, summary_threshold: int, num_messages_summarize: int):
    """ summarize messages for a given thread id and save the summary to the database and redis.
    summarize when the total number of messages in the conversation thread exceeds a certain threshold (e.g. 10 messages), 
    and include the most recent assistant message in the messages to be summarized, as that would likely contain the most relevant information for summarization.
    """
    # get messages for the thread id from redis
    messages = get_messages_by_thread_id_from_redis(r, thread_id)
    if not messages:
        logger.info(
            "no messages found in redis for thread_id %s, skipping summarization", thread_id)
        return
    messages_to_summarize = []
    # fetch first 5 message for summarization
    # make sure include the most recent assistant message in the messages to be summarized, as that would likely contain the most relevant information for summarization
    if len(messages) >= summary_threshold:
        index = 0
        while index < len(messages):

            messages_to_summarize.append(messages[index])

            index += 1
            if len(messages_to_summarize) >= num_messages_summarize and messages_to_summarize[-1]["role"] == "user":
                messages_to_summarize.remove(messages_to_summarize[-1])
                return messages_to_summarize
    else:
        logger.debug(
            "not enough messages to summarize for thread_id %s, skipping summarization", thread_id)
    return messages_to_summarize


def save_messages_to_redis(r, thread_id: str, messages: list, overwrite: bool = False, convert_to_json: bool = True):
    """ save messages to redis """
    # convert list of Messages objects to list of dict messages
    # logger.debug("converting messages to json for redis storage: %s", messages)
    # json_messages = convert_messages_to_json(_convert_to_messages(thread_id, messages))
    json_messages = messages

    if convert_to_json:
        json_messages = convert_messages_to_json(messages)

    # logger.debug(f"json messages to be stored in redis: {json_messages}")

    result = None
    if not overwrite and r.exists(thread_id):
        # if the thread already exists, we want to append the message to the existing list of messages for that thread.
        # unpack the list of json messages so that each message is appended as a separate element in the redis list
        result = r.json().arrappend(
            thread_id, "$", *json_messages)
    else:
        # if the thread does not exist, we want to create a new list of messages for that thread and add the message to that list
        result = r.json().set(thread_id, "$", json_messages)

    logger.debug("result of storing message in redis: %s", result)
    return result


def add_summary_to_redis(r, thread_id: str, summary: Message, num_messages_to_replace):
    logger.debug("add summary to redis [%s]", summary)
    available_messages = get_messages_by_thread_id_from_redis(r, thread_id)
    updated_messages = available_messages[num_messages_to_replace:]
    updated_messages.insert(0, __convert_message_to_json(summary))
    save_messages_to_redis(r, thread_id, updated_messages,
                           overwrite=True, convert_to_json=False)


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


def __convert_message_to_json(message: Message) -> dict:
    """ convert list of Message objects to json string """
    return MessageSchema.model_validate(message).model_dump(mode='json')


def get_messages_by_thread_id_from_redis(r: redis.Redis, thread_id: str):
    """ get messages by thread id from redis """
    if r.exists(thread_id):
        messages = r.json().get(thread_id, "$")
        logger.debug(
            "messages retrieved from redis for thread_id %s: %s", thread_id, messages)
        return messages[0] if messages else []
    else:
        logger.debug("no messages found in redis for thread_id %s", thread_id)
        return None
