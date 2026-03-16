# Recipe Manager Agent (rm_agent_app)

A LangGraph-based AI agent that demonstrates MCP integration (SSE and Stdio transports), RAG-based context injection, and tool calling — built as a LangSmith deployable application.

## Architecture

```
User Message
    ↓
RAG Node  ──── ChromaDB (Cloud) ──── injects context into system prompt
    ↓
LLM Node  ──── DeepSeek Chat ──── binds MCP tools
    ↓
Tools Node ──── MCP Server (SSE/Stdio) ──── recipe_search, get_recipe_details
    ↓
LLM Node  (loop until no tool calls)
    ↓
Response
```

### Key Components

| Component | Description |
|-----------|-------------|
| `rm_agent_with_mcp.py` | Main agent graph — connects to MCP server via SSE, runs RAG + LLM + Tools nodes |
| `rm_agent.py` | Simplified agent using mock local tools (no MCP) |
| `utils/nodes.py` | Node implementations: `rag_node`, `llm_node`, `tool_node_wrapper`, `resource_node` |
| `utils/state.py` | `RecipeAppState` — shared graph state (messages, context, call counters) |
| `langgraph.json` | LangGraph app config — registers `rm_agent` graph entry point |

### MCP Server (`ai/mcp/rm-mcp-server`)

A FastMCP server exposing:
- **Tools**: `recipe_search(query)`, `get_recipe_details(recipe_id)`
- **Resources**: `recipe://docs/safety`, `recipe://docs/measurements`

The server binds to `0.0.0.0:8000` to accept connections from outside containers.

### Transport Modes

| Mode | Config | Use Case |
|------|--------|----------|
| SSE | `MCP_SERVER_URL=http://<host>:8000/sse` | Default — used in Docker and local dev |
| Stdio | `command: python`, `args: [path/to/main.py]` | Local process, no network required |

The active transport is configured in `rm_agent_with_mcp.py` via `MultiServerMCPClient`.

### RAG Node

Retrieves relevant context from a ChromaDB cloud vector store (`rm_knowledge_collection`) using `BAAI/bge-large-en-v1.5` embeddings. The retrieved context is injected into the system prompt `{context}` placeholder before the LLM call.

## Local Development

### Prerequisites
- Python 3.12
- `uv` installed (`brew install uv`)

### Setup

```bash
cd ai/lg_app/rm_agent_app
uv sync
```

Configure `.env`:
```
DEEPSEEK_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=trocks-ai
HF_TOKEN=...
CHROMA_CLOUD_API_KEY=...
CHROMA_TENANT=...
MCP_SERVER_URL=http://localhost:8000/sse   # point to local MCP server
```

### Start the MCP Server

```bash
cd ai/mcp/rm-mcp-server
uv run python main.py
# Server starts at http://0.0.0.0:8000
# Verify the Server using http://0.0.0.0:8000/sse
```

### Run the Agent (LangGraph Dev Mode)

```bash
cd ai/lg_app/rm_agent_app
uv run langgraph dev
# LangGraph Studio available at https://smith.langchain.com/studio
# API available at http://localhost:2024
```

## Docker Deployment

### Build Images

```bash
# Build MCP server image
cd ai/mcp/rm-mcp-server
docker build -t rm-mcp:latest .

# Build LangGraph agent image
cd ai/lg_app/rm_agent_app
langgraph build -t rm_agent
```

### Run with Docker Compose

```bash
cd ai/lg_app/rm_agent_app
docker-compose up
```

This starts:
- `langgraph-postgres` — stores threads, runs, thread state, and long-term memory (port `5432`)
- `langgraph-redis` — handles streaming real-time output for background runs
- `rm-mcp` — MCP server (port `8000`)
- `langgraph-api` — Agent server (port `8123`)

The compose file injects the following into the agent container:
```
REDIS_URI=redis://langgraph-redis:6379
DATABASE_URI=postgres://postgres:...@langgraph-postgres:5432/postgres?sslmode=disable
MCP_SERVER_URL=http://rm-mcp:8000/sse
```

### Standalone Container

When running the agent container standalone (outside compose), provide these env variables:

```bash
docker run -p 8123:8000 \
  --env-file .env \
  -e REDIS_URI=redis://<host>:6379 \
  -e DATABASE_URI=postgres://<user>:<pass>@<host>:5432/postgres \
  -e MCP_SERVER_URL=http://<mcp-host>:8000/sse \
  rm_agent
```

- `REDIS_URI` — required for streaming real-time output in background runs
- `DATABASE_URI` — required for persisting threads, runs, thread state, and long-term memory

## LangGraph Commands

| Command | Description |
|---------|-------------|
| `uv run langgraph dev` | Start local dev server with hot reload |
| `langgraph build -t <image>` | Build production Docker image |
| `langgraph up` | Start full stack (agent + postgres + redis) via Docker |
| `uv run python main.py` | Run agent directly without LangGraph server |

## API

Once running, the agent is accessible at:
- Local dev: `http://localhost:2024`
- Docker: `http://localhost:8123`
- API docs: `http://localhost:2024/docs`

Graph name: `rm_agent`
