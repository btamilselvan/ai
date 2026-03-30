import os
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, Integer, String, TEXT, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
import asyncio

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)


class Base(DeclarativeBase):
    pass


metadata = Base.metadata


class Messages(Base):
    __tablename__ = "messages"

    id = mapped_column(Integer, primary_key=True,
                       nullable=False, autoincrement="auto")
    thread_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # role can be user, assistant or system
    role: Mapped[str] = mapped_column(
        String(6), nullable=False, name="user_role")
    # can be declared without mapped_column if the type can be inferred,
    # but adding mapped_column allows us to add additional constraints like nullable, default value etc
    message = Mapped[Optional[str]],
    summary: Mapped[Optional[str]] = mapped_column(TEXT)
    tool: Mapped[Optional[str]] = mapped_column(String(50), name="tool_name")
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(50))
    created_at = mapped_column(TIMESTAMP,
                               default=func.current_timestamp())

# metadata.create_all(engine)

# async test


async def async_main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    print(f"database connection successful {engine}...")

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            session.add(Messages(thread_id="1234",
                        role="user", message="hello world"))
            print("df")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(async_main())
