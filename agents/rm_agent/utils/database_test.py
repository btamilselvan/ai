import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, TEXT, TIMESTAMP, func
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import insert, select

print(f"version {sqlalchemy.__version__}")

# Lazy initialization
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

print("connection created...")

# commit as go
with engine.connect() as conn:
    result = conn.execute(sqlalchemy.text("select 'hello world'"))
    print(result.all())

# auto-committing
with engine.begin() as conn:
    conn.execute(sqlalchemy.text(
        "create table if not exists test (x int, y int)"))
    result = conn.execute(sqlalchemy.text("insert into test (x,y) values (:x, :y)"), [
        {"x": 1, "y": 1}, {"x": 2, "y": 2}])
    print(f"insert result {result}")
    result = conn.execute(sqlalchemy.text("select * from test"))
    print("data inserted...")
    for row in result:
        print(f"row {row.x}, {row.y}")

    result = conn.execute(sqlalchemy.text(
        "select x, y from test where x = :x"), {"x": 1})
    for row in result:
        print(f"row {row.x}, {row.y}")

# commit as go
# The Session doesn’t actually hold onto the Connection object after it ends the transaction.
# It gets a new Connection from the Engine the next time it needs to execute SQL against the database.
with Session(engine) as session:
    result = session.execute(sqlalchemy.text("select * from test"))
    for row in result:
        print(f"row {row.x}, {row.y}")

##### ORM way of doing things - using DeclarativeBase and mapped_column #####
# A collection of Table objects and their associated schema constructs. (something like a database schema, persistent unit)
metadata = MetaData()
messages = Table("messages", metadata,
                 Column("id", Integer, primary_key=True, autoincrement="auto"),
                 Column("thread_id", String(36), nullable=False),
                 Column("user_role", String(6), nullable=False),
                 Column("message", TEXT),
                 Column("summary", TEXT),
                 Column("tool_name", String(50)),
                 Column("tool_call_id", String(50)),
                 Column("created_at", TIMESTAMP, default=func.current_timestamp()))

metadata.create_all(engine)

with Session(engine) as session:
    result = session.execute(sqlalchemy.text(
        "select thread_id, user_role from messages"))
    for row in result:
        print(f"row {row.thread_id}, {row.user_role}")


# declarative base class - acts as Metadata (ORM way of creating MetaData())
class Base(DeclarativeBase):
    pass


print(f"base metadata {Base.metadata}")
print(f"base registry {Base.registry}")

# Declarative mapping - creates a new table in the database for each class that inherits from Base


class Messages(Base):
    __tablename__ = "messages"

    id = mapped_column(Integer, primary_key=True,
                       nullable=False, autoincrement="auto")
    thread_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str] = mapped_column(String(6), nullable=False, name="user_role")  # role can be user, assistant or system
    # can be declared without mapped_column if the type can be inferred,
    # but adding mapped_column allows us to add additional constraints like nullable, default value etc
    message = Mapped[str],
    summary: Mapped[str] = mapped_column(TEXT)
    tool: Mapped[str] = mapped_column(String(50), name="tool_name")
    tool_call_id: Mapped[str] = mapped_column(String(50))
    created_at = mapped_column(TIMESTAMP,
                               default=func.current_timestamp())

    def __repr__(self) -> str:
        return f"Messages(id={self.id!r}, thread_id={self.thread_id!r}, role={self.role!r})"


# Imperative way of creating tables vs Declarative way (ORM)
# class MessagesImperative(Base):
#     __table__ = messages

# create tables in the database
Base.metadata.create_all(engine)

# auto load existing tables into ORM (either this MetaData way or DeclarativeBase way)
# metadata_another = MetaData()


class BaseAnother(DeclarativeBase):
    pass


messages_orm = Table("messages", BaseAnother.metadata, autoload_with=engine)
print(f"messages_orm {messages_orm.columns.keys()}")


# insert - imperative way
stmt = insert(messages).values(thread_id="1234",
                               user_role="user", message="hello world")
print(f"insert statement {stmt}")
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(f"insert result {result.inserted_primary_key}")
    conn.commit()

with engine.connect() as conn:
    result = conn.execute(insert(messages), [
        {"thread_id": "1234", "user_role": "user", "message": "hello world"},
        {"thread_id": "1234", "user_role": "assistant", "message": "hi there"}
    ])
    print(f"insert result {result.inserted_primary_key_rows}")
    conn.commit()

with engine.connect() as conn:
    result = conn.execute(sqlalchemy.text(
        "select id, thread_id, user_role from messages"))
    for row in result:
        print(f"row {row.id}, {row.thread_id}, {row.user_role}")

stmt = select(messages).where(messages.c.thread_id == "1234")
print(f"select statement: {stmt}")

with engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(f"row {row.id}, {row.thread_id}, {row.user_role}")
        
## ORM way
stmt = select(Messages).where(Messages.thread_id == "1234")
with Session(engine) as session:
    result = session.execute(stmt).first()
    print(f"first result {result[0]}")
    # for row in result:
    #     print(f"(ORM) row {row.Messages.id}, {row.Messages.thread_id}, {row.Messages.role}")
    
# stmt = insert(Messages).
with Session(engine) as session:
    result = session.execute(insert(Messages).returning(Messages), [
        {"thread_id": "5678", "role": "user", "message": "hello again"}
    ])
    print(f"inserted primary key (ORM) {result.all()}")
    session.commit()