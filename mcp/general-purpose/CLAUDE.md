# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A FastMCP server exposing general-purpose tools via the Model Context Protocol (MCP) over SSE transport on port 8003.

## Commands

```bash
# Install dependencies
uv sync

# Run locally (fastmcp CLI — picks up fastmcp.json automatically)
uv run fastmcp run main.py:mcp --transport sse --port 8003

# Run locally (uvicorn directly)
uv run uvicorn asgi:app --host 0.0.0.0 --port 8003

# Build Docker image
docker build -t general-purpose-mcp .

# Run Docker container
docker run -p 8003:8003 -e PERM_TRACKER_API_URL=<url> general-purpose-mcp
```

Requires a `.env` file (local) or `-e PERM_TRACKER_API_URL=<url>` (Docker) with `PERM_TRACKER_API_URL` set.

## Architecture

**Entry point**: `main.py` — creates the `FastMCP` instance named `"general-purpose"`, registers a `FileSystemProvider` pointing at the `mcp/` directory, and manages an `httpx.AsyncClient` lifecycle via the `lifespan` context manager.

**Tool auto-discovery**: Any `@tool`-decorated function inside the `mcp/` directory is automatically registered under the namespace `general-purpose.*` (e.g., `general-purpose.get_current_gc_perm_estimate`).

**Shared HTTP client**: `resource_registry.py` holds a module-level `http_client` variable. The lifespan in `main.py` initializes it on startup and closes it on shutdown. Tools import `resource_registry` directly to access the shared client — do not create per-request clients.

**Adding a new tool**: Create a new `.py` file in `mcp/`, define an `async def` function decorated with `@tool(name=..., description=...)`, and use `Annotated[type, Field(description=...)]` for typed parameters. The tool is picked up automatically.
