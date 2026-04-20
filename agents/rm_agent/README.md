
# RM Agent

An AI-powered Recipe Manager Agent that demonstrates OpenAI-compatible LLM orchestration with MCP (Model Context Protocol) tool calling, RAG (Retrieval-Augmented Generation), and multi-layer memory management.

## What This Project Does

The agent acts as a **Professional Recipe Manager Assistant**. Users chat with it via a REST API and the agent answers culinary questions, searches for recipes, and retrieves recipe details — all backed by live tool calls to an MCP server.

### Key Capabilities Demonstrated

- **Custom LLM orchestration loop** — The agent iterates between LLM calls and tool execution without relying on a framework like LangChain or LangGraph. The loop is capped at a configurable number of rounds to prevent runaway execution.
- **MCP tool calling over SSE transport** — Tool calls are dispatched to an MCP server via Server-Sent Events (SSE) using the `fastmcp` client. Multiple tool calls in a single LLM response are executed concurrently with `asyncio.gather`.
- **RAG with ChromaDB** — Before each LLM call, relevant context (kitchen safety guidelines, measurement guides) is retrieved from a ChromaDB Cloud vector store and injected into the system prompt.
- **Thread-scoped conversation memory** — Each conversation thread is identified by a `thread_id`. Session state is stored in Redis (short-term) and persisted to PostgreSQL (long-term).
- **Background summarization** — When a thread's message count exceeds a threshold, a dedicated `SummarizationAgent` compresses older messages into a summary, keeping the context window manageable.
- **API-key-authenticated MCP connection** — The `fastmcp` SSE transport sends an `x-api-key` header for server authentication.
- **Concurrent request protection** — A Redis-based distributed lock on each `thread_id` prevents overlapping requests from corrupting conversation state.

## Architecture

```
Client
  └── POST /chat/{thread_id}  (FastAPI)
        ├── Load session state from Redis
        ├── SupervisorAgent.orchestrate()
        │     ├── ChromaDB → inject RAG context into system prompt
        │     └── Loop (max MAX_ORCHESTRATION_ROUNDS):
        │           ├── OpenAI-compatible LLM call (DeepSeek)
        │           └── if tool_calls → fastmcp Client → MCP Server (SSE)
        └── Background tasks:
              ├── Persist new messages → PostgreSQL
              ├── Save updated state → Redis
              └── SummarizationAgent → compress old messages
```

### Component Overview

| Component | File | Responsibility |
|---|---|---|
| FastAPI server | `main.py` | HTTP entrypoint, lifespan, request routing |
| ResourceRegistry | `utils/resource_registry.py` | Singleton manager for MCP clients, AI clients, DB, Redis |
| SupervisorAgent | `agents/supervisor.py` | RAG + orchestration loop |
| BaseAgent | `agents/base.py` | LLM invocation + concurrent tool execution |
| SummarizationAgent | `agents/summarization_agent.py` | Compresses conversation history |
| Background tasks | `utils/background_task.py` | Persistence + summarization after each turn |
| Database | `datastore/database.py` | SQLAlchemy models + async PG operations |
| Models | `utils/models.py` | Pydantic schemas for AppState, ConversationModel, ToolCall |
| Settings | `utils/env_settings.py` | Pydantic-settings for environment config |

## Tech Stack

- **LLM**: DeepSeek (via OpenAI-compatible API)
- **MCP**: `fastmcp` >= 3.2.4, `mcp` >= 1.26.0 — SSE transport
- **Vector store**: ChromaDB Cloud
- **API framework**: FastAPI + Uvicorn/Gunicorn
- **Short-term memory**: Redis (JSON store)
- **Long-term memory**: PostgreSQL (via SQLAlchemy async)
- **Python**: >= 3.12

## Setup

### Environment Variables

Create a `.env` file:

```env
DEEPSEEK_API_KEY=...
MCP_SERVER_API_KEY=...
MCP_SERVERS={"rm_mcp_server": "http://localhost:8000/sse"}
AGENTS={"supervisor_agent": "deepseek-chat", "summarization_agent": "deepseek-chat"}
CHROMA_CLOUD_API_KEY=...
CHROMA_TENANT=...
CHROMA_DATABASE=...
HF_TOKEN=...
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Run

```bash
# Development
uv run uvicorn main:app --reload --host 0.0.0.0 --port 9000

# Production
uv run gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:9000

# Direct
uv run main.py
```

## API

### Health check
```
GET /health
```

### Chat
```
POST /chat/{thread_id}
Content-Type: application/json

{"message": "Are there any avocado toast recipes?"}
```

The `thread_id` scopes the conversation. Use the same ID across turns to maintain history.

**Responses:**
- `200` — `{"message": "<assistant reply>"}`
- `429` — Another request is already processing for this thread
- `500` — Internal error

## References

- https://api-docs.deepseek.com
- https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- https://gofastmcp.com
- https://docs.trychroma.com
