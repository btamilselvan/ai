from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy import Integer, String, TEXT, TIMESTAMP,  JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
from uuid import UUID
import redis
import logging
from utils.models import ConversationModel, AppState


logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    pass


metadata = Base.metadata


# create a table to store conversation messages
class Conversation(Base):
    __tablename__ = "rm_conversation"

    id = mapped_column(Integer, primary_key=True,
                       nullable=False, autoincrement="auto")
    thread_id: Mapped[UUID] = mapped_column(nullable=False)
    # role can be user, assistant or system
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, name="user_role")
    # can be declared without mapped_column if the type can be inferred,
    # but adding mapped_column allows us to add additional constraints like nullable, default value etc
    content: Mapped[Optional[str]] = mapped_column(TEXT, name="message")
    summary: Mapped[Optional[str]] = mapped_column(TEXT)
    tool_calls: Mapped[Optional[JSON]] = mapped_column(JSON, name="tool_calls")
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(50))
    # created_at = mapped_column(TIMESTAMP,
    #                            default=func.current_timestamp())
    created_at = mapped_column(TIMESTAMP(timezone=True),
                               server_default=func.now())


async def save_messages_to_pg(async_sessionmaker: async_sessionmaker[AsyncSession], thread_id: str, messages: list[ConversationModel]):
    """ save messages to database """

    entities = [Conversation(**message.model_dump(exclude_none=True))
                for message in messages]
    logger.debug("saving messages to database: %s", entities)

    async with async_sessionmaker() as session:
        async with session.begin():
            session.add_all(entities)
        await session.commit()
    logger.debug("messages saved to database for thread_id: %s", thread_id)


def save_appstate_to_redis(r, thread_id: str, appstate: AppState):
    """ save messages to redis """
    result = r.json().set(thread_id, "$", appstate.model_dump(mode="json"))
    logger.debug("result of storing message in redis: %s", result)
    return result


def load_appstate_from_redis(r: redis.Redis, thread_id) -> AppState:
    """ load app state by thread_id """
    saved_state = r.json().get(thread_id, "$")
    logger.debug("saved_state %s", saved_state)
    if not saved_state:
        return AppState(thread_id=thread_id)
    return AppState.model_validate(saved_state[0])
