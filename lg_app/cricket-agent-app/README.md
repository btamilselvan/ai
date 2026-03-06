# Cricket Agent App - LangSmith Cloud Deployment

LangGraph application for deploying the cricket agent to LangSmith cloud with MCP integration.

## Project Structure

```
cricket-agent-app/
├── cricket_agent/
│   ├── utils/
│   │   ├── state.py          # MyAppState definition
│   │   ├── nodes.py          # llm_node, tool_node_wrapper
│   │   ├── tools.py          # Local tools (if any)
│   │   └── mcp_tools.py      # MCP tool utilities
│   ├── agent_with_mcp.py     # Main agent graph (exported)
│   └── agent.py              # Alternative agent implementation
├── langgraph.json            # LangGraph deployment config
├── pyproject.toml            # Dependencies
├── .env                      # Environment variables
└── main.py                   # Entry point (optional)
```

## Configuration

### langgraph.json
```json
{
    "dependencies": ["./"],
    "env": "./.env",
    "python_version": "3.12",
    "graphs": {
        "cricket_agent": "./cricket_agent/agent_with_mcp.py:agent"
    }
}
```

**Key fields:**
- `graphs` - Maps graph name to module path and exported variable
- `python_version` - Python runtime version (3.12)
- `env` - Environment variables file
- `dependencies` - Local dependencies to include

### Environment Variables
```bash
# .env
RAPIDAPI_API_KEY=your_rapidapi_key
DEEPSEEK_API_KEY=your_deepseek_key
LANGSMITH_API_KEY=your_langsmith_key  # For cloud deployment
```

## Dependencies

```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "langchain>=1.2.10",
    "langchain-deepseek>=1.0.1",
    "langchain-mcp-adapters>=0.2.1",
    "langgraph>=1.0.10",
    "langgraph-checkpoint-postgres>=3.0.4",
    "psycopg[binary,pool]>=3.3.3",
    "python-dotenv>=1.2.2",
]
```

## Local Development

### Setup with uv
```bash
# Initialize
uv init

# Install dependencies
uv sync

# Install langgraph-cli for local development
uv pip install langgraph-cli "langgraph-cli[inmem]"

# Run local dev server
uv run langgraph dev
```

### Access Local API
- API Docs: http://127.0.0.1:2024/docs
- Studio UI: http://127.0.0.1:2024/studio

### Test Locally
```bash
# Invoke agent
curl -X POST http://127.0.0.1:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "cricket_agent",
    "input": {"messages": [{"role": "user", "content": "What are upcoming matches?"}]},
    "config": {"configurable": {"thread_id": "test-123"}}
  }'
```

## Cloud Deployment

### Prerequisites
- LangSmith account
- GitHub repository (for cloud deployment)
- LANGSMITH_API_KEY configured

### Deploy from GitHub
1. Push code to GitHub repository
2. Go to LangSmith UI → Deployments
3. Create new deployment:
   - Select repository
   - Choose branch (e.g., `main`)
   - Specify `langgraph.json` path
4. Configure environment variables in UI
5. Deploy

### Deploy with CLI (Hybrid/Self-hosted)
```bash
# Build Docker image
langgraph build -t cricket-agent:latest

# Push to registry
docker tag cricket-agent:latest your-registry/cricket-agent:latest
docker push your-registry/cricket-agent:latest

# Deploy via LangSmith UI or API
```

### Standalone Server
```bash
# Run production server
langgraph up

# Containers started:
# - PostgreSQL (checkpointing)
# - Redis (caching)
# - API server
```

## Agent Architecture

### Graph Structure
```
START → llm → tools_condition → [tools → llm] → END
```

### MCP Client Setup
```python
mcp_client = MultiServerMCPClient({
    "rapidapi_cricbuzz": {
        "command": "npx",
        "transport": "stdio",
        "args": [
            "mcp-remote",
            "https://mcp.rapidapi.com",
            "--header", "x-api-host: cricbuzz-cricket.p.rapidapi.com",
            "--header", f"x-api-key: {RAPIDAPI_API_KEY}"
        ]
    }
})
```

### Graph Creation
```python
async def create_graph():
    tools = await mcp_client.get_tools()
    model_with_tools = model.bind_tools(tools)
    
    graph = StateGraph(MyAppState)
    graph.add_node("llm", partial(llm_node, model_with_tools, SYSTEM_PROMPT))
    graph.add_node("tools", partial(tool_node_wrapper, mcp_tool_node))
    
    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", tools_condition)
    graph.add_edge("tools", "llm")
    
    return graph.compile()

agent = asyncio.run(create_graph())
```

## API Usage

### Invoke Agent
```python
# Python SDK
from langgraph_sdk import get_client

client = get_client(url="https://your-deployment.langsmith.com")
thread = await client.threads.create()

response = await client.runs.create(
    thread["thread_id"],
    "cricket_agent",
    input={"messages": [{"role": "user", "content": "Show me India's ranking"}]},
)
```

### Stream Responses
```python
async for chunk in client.runs.stream(
    thread["thread_id"],
    "cricket_agent",
    input={"messages": [{"role": "user", "content": "Upcoming matches?"}]},
    stream_mode="values"
):
    print(chunk)
```

### Handle Interrupts
```python
# First call - hits interrupt for preferred_team
response = await client.runs.create(thread_id, "cricket_agent", input=initial_input)

# Resume with user input
await client.runs.create(
    thread_id,
    "cricket_agent",
    command={"resume": {"interrupt_id": "India"}},
)
```

## State Management

### MyAppState
```python
class MyAppState(TypedDict):
    preferred_team: Optional[str]
    messages: Annotated[List[AnyMessage], operator.add]
    llm_calls: int
    tool_calls: int
```

### Checkpointing
- Local dev: InMemorySaver (`.langgraph_api/`)
- Production: PostgreSQL (configured in deployment)

## Monitoring

### LangSmith Tracing
All runs automatically traced in LangSmith:
- View conversation history
- Inspect tool calls
- Debug errors
- Monitor latency

### Access Traces
1. Go to LangSmith UI
2. Navigate to Projects
3. Select your deployment
4. View runs and traces

## Troubleshooting

### MCP Connection Fails
- Ensure Node.js installed in deployment environment
- Verify `npx` available in PATH
- Check RAPIDAPI_API_KEY is set

### Graph Not Found
- Verify `langgraph.json` graph path matches file structure
- Ensure `agent` variable is exported at module level
- Check Python version compatibility (3.12)

### Deployment Errors
- Review build logs in LangSmith UI
- Validate all environment variables set
- Check dependencies in `pyproject.toml`

## Development Workflow

1. **Local Development**
   ```bash
   uv run langgraph dev
   # Test at http://127.0.0.1:2024
   ```

2. **Test Changes**
   ```bash
   # Use Studio UI or curl
   curl -X POST http://127.0.0.1:2024/runs/stream ...
   ```

3. **Commit & Push**
   ```bash
   git add .
   git commit -m "Update agent"
   git push origin main
   ```

4. **Deploy**
   - LangSmith auto-deploys from GitHub
   - Or manually trigger deployment in UI

## References

- [LangGraph Cloud Docs](https://docs.langchain.com/langsmith/deployment)
- [langgraph.json Schema](https://docs.langchain.com/langsmith/deployment/config)
- [LangGraph SDK](https://docs.langchain.com/langsmith/sdk)
- [MCP Integration](https://docs.langchain.com/langsmith/mcp)
