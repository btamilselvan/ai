--
Two ways to enable MCP capabilites to an existing Fast API Project:
1) Generate an MCP server FROM your FastAPI app - Convert existing API endpoints into MCP tools
2) Mount an MCP server INTO your FastAPI app - Add MCP functionality to your web application (have both API and MCP)

A common pattern is to generate an MCP server from your FastAPI app and serve both interfaces from the same application. This provides an LLM-optimized interface alongside your regular API.