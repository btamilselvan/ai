import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from fastmcp.server.providers import FileSystemProvider

from hooks import LoggingMiddleware, AuthMiddleware

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@lifespan
async def app_lifespan(app):
    try:
        logger.debug("server is starting up..")
        yield
        logger.debug("server is shutdown initiated..")
    except Exception as e:
        logger.error(f"error in lifespan : {e}")
        raise
    finally:
        logger.debug("resource cleanup is done...")


# main MCP server
mcp = FastMCP(name="RM MCP Server", lifespan=app_lifespan,
              website_url="tamils.rocks")
mcp.add_middleware(LoggingMiddleware())
mcp.add_middleware(AuthMiddleware())

# sub-servers for logical domain separation
recipe_mcp_server = FastMCP(name="Recipe MCP Server")
collections_mcp_server = FastMCP(name="RM Collections MCP Server", on_duplicate="warn")

recipe_mcp_server.add_provider(
    FileSystemProvider(Path(__file__).parent / "mcp/recipe"))
collections_mcp_server.add_provider(
    FileSystemProvider(Path(__file__).parent / "mcp/collection"))

# namespace prefix is applied to all tools/resources (e.g. recipes_search, collections_search)
mcp.mount(recipe_mcp_server, namespace="recipes")
mcp.mount(collections_mcp_server, namespace="collections")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(mcp.http_app(transport="sse"), host="0.0.0.0", port=8002)
