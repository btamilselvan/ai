# Cricket Agent - Async Implementation

An AI agent built with LangGraph that answers cricket-related questions using MCP (Model Context Protocol) tools from RapidAPI.

## Architecture

### Workflow
1. User query → `llm_node` → `tools_condition` (conditional edge)
2. If tool calls needed → `tools` node → back to `llm_node`
3. If no tool calls → END

### Key Components

**Nodes:**
- `llm_node` - Processes queries with LLM and system prompt
- `tools` - Executes MCP tools via remote connection

**State:**
- `messages` - Conversation history (appended)
- `preferred_team` - User's favorite team (optional)
- `llm_calls` - Counter for LLM invocations
- `tool_calls` - Counter for tool executions

**Features:**
- Async execution with `asyncio`
- PostgreSQL checkpointing for conversation persistence
- MCP remote tools via `mcp-remote` bridge
- Human-in-the-loop with `interrupt()` for preferred team input
- Retry policy for tool failures (3 attempts)

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database
- RapidAPI key for Cricbuzz API
- Node.js (for `mcp-remote`)

### Environment Variables
```bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
RAPIDAPI_API_KEY=your_api_key_here
DEEPSEEK_API_KEY=your_deepseek_key  # or use Ollama
```

### Installation with uv
```bash
# Install uv if not already installed
brew install uv

# Initialize project (if starting fresh)
uv init

# Add dependencies
uv add langchain-core langgraph langchain-mcp-adapters mcp python-dotenv psycopg psycopg-pool

# Or sync from existing pyproject.toml
uv sync
```

## Running the Agent

### Using uv
```bash
# Run directly with uv
uv run cricket_agent_async.py

# Or activate virtual environment first
source .venv/bin/activate
python cricket_agent_async.py
```

### Execution Flow
1. Agent initializes MCP connection to RapidAPI
2. Loads cricket tools (matches, rankings, stats)
3. Sets up PostgreSQL checkpointer
4. Starts conversation with greeting
5. Prompts for preferred team (interrupt)
6. Continues with 2 user queries
7. Displays statistics (messages, LLM calls, tool calls)

## MCP Integration

### Transport: Stdio with mcp-remote Bridge
```python
server_params = StdioServerParameters(
    command="npx",
    args=[
        "mcp-remote",
        "https://mcp.rapidapi.com",
        "--header", "x-api-host: cricbuzz-cricket.p.rapidapi.com",
        "--header", f"x-api-key: {RAPIDAPI_API_KEY}",
    ]
)
```

**Connection Chain:**
Agent → Local `mcp-remote` (stdio) → RapidAPI MCP Server (HTTPS)

### Tool Loading
```python
async with ClientSession(read, write) as session:
    await session.initialize()
    mcp_tools = await load_mcp_tools(session)
    model_with_tools = model.bind_tools(mcp_tools)
```

## Configuration

### LLM Model
```python
# DeepSeek (default)
model = init_chat_model("deepseek-chat", temperature=0, max_tokens=2048)

# Or Ollama (local)
# model = init_chat_model("ollama:llama3.2", temperature=0, max_tokens=2048)
```

### Session Management
```python
session_id = f"session-{random.randint(1000, 9999)}"
config = {"configurable": {"thread_id": session_id}}
```

### Checkpointer
```python
async with AsyncConnectionPool(conninfo=DATABASE_URL, max_size=10, 
                               kwargs={"autocommit": True, "prepare_threshold": 0}) as pool:
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
```

## Human-in-the-Loop

The agent uses `interrupt()` to request user's preferred team:

```python
if not state.get("preferred_team"):
    preferred_team = interrupt({
        "message": "Enter your preferred team:",
        "prompt": "Please enter your preferred team: "
    })
```

Resume execution:
```python
chat_state = await agent.ainvoke(Command(resume=resume_map), config=config)
```

## Graph Visualization

```
    +-----------+
    |   START   |
    +-----------+
          *
          *
          *
    +-----------+
    |    llm    |
    +-----------+
       *      *
      *        *
     *          *
+-----------+   *
|   tools   |   *
+-----------+   *
       *        *
        *      *
         *    *
    +-----------+
    |    END    |
    +-----------+
```

## Troubleshooting

### MCP Connection Issues
- Ensure Node.js and `npx` are installed
- Verify RapidAPI key is valid
- Check network connectivity to `mcp.rapidapi.com`

### Database Issues
- Confirm PostgreSQL is running
- Verify `DATABASE_URL` format
- Ensure database exists and user has permissions

### Tool Execution Failures
- Check retry policy logs (3 attempts with exponential backoff)
- Verify tool arguments match expected schema
- Review MCP server response format

## Notes

- Session ID is randomly generated per run
- Conversation history persists in PostgreSQL
- Tool node wrapper intercepts and logs tool calls
- `tools_condition` replaces manual `planner_node` logic
- Async operations use `asyncio.to_thread()` for blocking I/O
