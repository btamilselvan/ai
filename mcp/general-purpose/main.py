from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import httpx
import resource_registry

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(server: FastMCP):
    try:
        logger.info("Starting MCP server...")
        resource_registry.http_client = httpx.AsyncClient()
        yield
        logger.info("Shutting down MCP server...")
    finally:
        logger.info("Finalizing MCP server...")
        if resource_registry.http_client:
            await resource_registry.http_client.aclose()


mcp = FastMCP("general-purpose", lifespan=lifespan)

# Register tools and resources from the "mcp" directory. any tool or resource defined in that directory
# will be automatically registered to the MCP server with the namespace "general-purpose" (e.g. general-purpose.get_current_gc_perm_estimate)
mcp.add_provider(
    FileSystemProvider(Path(__file__).parent / "mcp"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.http_app(transport="sse"), host="0.0.0.0", port=8003)