# RM MCP Server

A Recipe Manager MCP server that demonstrates key [Model Context Protocol](https://modelcontextprotocol.io) capabilities using [FastMCP](https://gofastmcp.com).

## What This Project Demonstrates

### Multi-Server Architecture
The main server mounts two sub-servers under separate namespaces. Tools and resources from each sub-server are automatically prefixed (e.g. `recipes_search`, `collections_search`), keeping domains isolated.

```
RM MCP Server (main)
├── Recipe MCP Server       → namespace: "recipes"
└── Collections MCP Server  → namespace: "collections"
```

### Tools
- **`recipes_search`** — search mock recipes by title or ingredients (async)
- **`recipes_recipes`** — fetch full recipe details by ID
- **`collections_search`** — stub for future collection search

Tools use the standalone `@tool()` decorator from `fastmcp.tools` (not `@mcp.tool`) to avoid circular imports when discovered via `FileSystemProvider`.

### Resources
Static, read-only content exposed via URI schemes:
- `recipe://docs/safety` — kitchen safety guidelines
- `recipe://docs/measurements` — cooking measurement conversions

### Middleware (Hooks)
Registered on the main server and applied to all mounted sub-servers:

| Middleware | Hook | Purpose |
|---|---|---|
| `LoggingMiddleware` | `on_message` | Logs every message with request/session IDs |
| `AuthMiddleware` | `on_initialize` | Logs connecting client info |
| `AuthMiddleware` | `on_request` | Validates `x-api-key` header against `MCP_SERVER_API_KEY` |

### Context & State
The `recipes_search` tool demonstrates:
- `context.report_progress()` — progress updates during tool execution
- `context.info()` — informational log messages to the client
- `context.get_state()` / `context.set_state()` — session-scoped state (tracks last search query)

### Dependency Injection
Tools can inject the raw Starlette `Request` object via `CurrentRequest()` to access HTTP headers directly, independent of middleware.

### Auto-Discovery
`FileSystemProvider` scans the `mcp/recipe` and `mcp/collection` directories and automatically registers any `@tool`, `@resource`, or `@prompt` decorated functions found there.

---

## Project Structure

```
rm-mcp-server/
├── main.py                        # Entry point — server setup and run
├── hooks.py                       # Middleware: logging and auth
├── mcp/
│   ├── recipe/
│   │   ├── tools/recipe_tool.py   # Recipe search and detail tools
│   │   └── resources/rm_resources.py  # Safety and measurement resources
│   └── collection/
│       └── tools/collection_tool.py   # Collection search (stub)
├── fastmcp.json                   # FastMCP project config (see below)
├── mcp-config.json                # MCP client config (see below)
├── Dockerfile                     # Container deployment
└── .env                           # API keys (not committed)
```

---

## Generating Config Files

Use the FastMCP CLI to auto-generate both config files.

### Generate `fastmcp.json`
```bash
uv run fastmcp install mcp-json main.py >> fastmcp.json
```

With additional options:
```bash
uv run fastmcp install mcp-json main.py \
  --name "RM MCP Server" \
  --env MCP_SERVER_API_KEY=your-key >> fastmcp.json
```

### Generate `mcp-config.json`
```bash
uv run fastmcp install mcp-json main.py \
  --name "RM MCP Server" \
  --env-file .env \
  --python 3.12 > mcp-config.json
```

---

## Configuration Files

### `fastmcp.json`
FastMCP's project-level config file. When present, `uv run fastmcp run` reads this file instead of requiring all flags on the command line. It specifies:
- **source** — which file and object (`main.py` → `mcp`) to run
- **deployment** — transport (`sse`), host, and port
- **environment** — package manager (`uv`)

With this file in place, starting the server is just:
```bash
uv run fastmcp run
```

### `mcp-config.json`
A client-side MCP connection config snippet. MCP clients (Claude Desktop, etc.) use this format to know how to launch and connect to an MCP server. It specifies the command, arguments, and environment variables the client should use. Generate or update it with:
```bash
uv run fastmcp install mcp-config.json main.py --env-file .env --python 3.12 --name "RM MCP Server"
```

---

## Running the Server

**Using `fastmcp.json` (recommended):**
```bash
uv run fastmcp run
```

**Explicit flags:**
```bash
uv run fastmcp run main.py --transport sse --port 8002
```

**Direct Python (runs uvicorn):**
```bash
LOCAL_API_KEY="your-key" uv run python main.py
```

**Docker:**
```bash
docker build -t rm-mcp-server .
docker run -e MCP_SERVER_API_KEY=your-key -p 8002:8002 rm-mcp-server
```

---

## Useful FastMCP CLI Commands

| Command | Purpose |
|---|---|
| `uv run fastmcp run` | Start the server using `fastmcp.json` config |
| `uv run fastmcp run main.py --transport sse --port 8002` | Start with explicit flags |
| `uv run fastmcp dev apps main.py:mcp --mcp-port 8002 --dev-port 9090` | Start with live-reload dev mode |
| `uv run fastmcp inspect main.py --format fastmcp` | Inspect server — lists all tools, resources, and prompts |
| `uv run fastmcp list http://localhost:8002/mcp` | List tools/resources from a running server |
| `uv run fastmcp install mcp-config.json main.py --env-file .env` | Generate MCP client config |
| `npx @modelcontextprotocol/inspector python3 main.py` | Open MCP Inspector UI in browser |

> Most commands that connect to the server require the API key:
> ```bash
> LOCAL_API_KEY="your-key" uv run fastmcp inspect main.py --format fastmcp
> ```

---

## References
- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP Middleware](https://gofastmcp.com/servers/middleware)
- [MCP Specification](https://modelcontextprotocol.io)
