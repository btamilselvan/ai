# LangGraph Apps (lg_app)

A collection of LangGraph applications demonstrating agent building, MCP integration, RAG, tool calling, and LangSmith deployment.

## Apps

| App | Description |
|-----|-------------|
| `cricket-agent-app` | Cricket agent with MCP (Stdio/mcp-remote) tool integration, deployed to LangSmith cloud |
| `rm_agent_app` | Recipe Manager agent with RAG (ChromaDB), MCP (SSE/Stdio), tool calling, and Docker deployment |

## Capabilities Demonstrated

| Capability | App |
|------------|-----|
| ReAct agent (LLM + Tools loop) | Both |
| MCP via Stdio (mcp-remote bridge) | cricket-agent-app |
| MCP via SSE (remote HTTP server) | rm_agent_app |
| RAG with ChromaDB vector store | rm_agent_app |
| Tool calling with `bind_tools` | Both |
| LangSmith cloud deployment | cricket-agent-app |
| Docker Compose deployment | rm_agent_app |
| Interrupt & resume | cricket-agent-app |
| Short-term memory (checkpointing) | Both |

## Project Structure

```
lg_app/
├── cricket-agent-app/        # Cricket agent — MCP + LangSmith cloud
│   ├── cricket_agent/
│   │   ├── utils/            # state, nodes, tools, mcp_tools
│   │   ├── agent_with_mcp.py # Main graph (exported)
│   │   └── agent.py          # Alternative (no MCP)
│   ├── langgraph.json
│   └── pyproject.toml
├── rm_agent_app/             # Recipe Manager agent — RAG + MCP + Docker
│   ├── rm_agent/
│   │   ├── utils/            # state, nodes, tools
│   │   ├── rm_agent_with_mcp.py  # Main graph (exported)
│   │   └── rm_agent.py       # Simplified (mock tools)
│   ├── docker-compose.yaml
│   ├── langgraph.json
│   └── pyproject.toml
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.12
- `uv` (`brew install uv`)
- Node.js (for `npx mcp-remote` in cricket-agent-app)
- Docker (for rm_agent_app Docker deployment)

### Run locally

```bash
# Cricket agent
cd cricket-agent-app
uv sync
uv run langgraph dev

# Recipe Manager agent
cd rm_agent_app
uv sync
uv run langgraph dev
```

Local API: `http://localhost:2024` | Docs: `http://localhost:2024/docs`

## App Details

### cricket-agent-app

- Connects to Cricbuzz API via RapidAPI MCP gateway using `mcp-remote` (Stdio bridge → SSE remote)
- Supports interrupt/resume for user preference collection
- Deployable to LangSmith cloud via GitHub

**Graph:** `START → llm → tools_condition → [tools → llm] → END`

### rm_agent_app

- RAG node retrieves context from ChromaDB cloud before each LLM call
- Connects to a FastMCP recipe server via SSE (`http://<host>:8000/sse`)
- Full Docker Compose stack: agent + PostgreSQL + Redis + MCP server

**Graph:** `START → rag → llm → tools_condition → [tools → llm] → END`

## Deployment

| Method | App | Command |
|--------|-----|---------|
| LangSmith cloud (GitHub) | cricket-agent-app | Push to GitHub → LangSmith UI |
| Docker Compose | rm_agent_app | `docker-compose up` |
| LangGraph standalone | Both | `langgraph up` |

## References

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangSmith Deployment](https://docs.langchain.com/langsmith/deployment)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [MCP Remote](https://github.com/modelcontextprotocol/mcp-remote)
