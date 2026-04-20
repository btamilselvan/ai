- use mcp inspector to access mcp server console.
- npx @modelcontextprotocol/inspector python3 main.py
- uv run fastmcp run main.py --transport sse --port 8002
- uv run fastmcp install mcp-json main.py --env-file .env --python 3.12 --name "RM MCP Server" >> mcp-config.json
- with fastmcp.json -> uv run fastmcp run
- CMD ["fastmcp", "run", "main.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8002"]
- LOCAL_API_KEY="lcjC52l26HAqQl87oN" uv run fastmcp inspect main.py --format fastmcp
- LOCAL_API_KEY="lcjC52l26HAqQl87oN" uv run fastmcp dev apps main.py:mcp --mcp-port 8002 --dev-port 9090
- LOCAL_API_KEY="lcjC52l26HAqQl87oN" uv run fastmcp list http://localhost:8002/mcp

#### References
- https://gofastmcp.com/servers/middleware