from pathlib import Path
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from fastmcp.server.providers import FileSystemProvider
from hooks import LoggingMiddleware, AuthMiddleware
import logging

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

# create the main mcp server instance
mcp = FastMCP(name="RM MCP Server", lifespan=app_lifespan,
              website_url="tamils.rocks")
mcp.add_middleware(LoggingMiddleware())
mcp.add_middleware(AuthMiddleware())

# create additional mcp server instances - logical separation - this provides recipe related tools
recipe_mcp_server = FastMCP(name="Recipe MCP Server")

# this provides collections related tools
collections_mcp_server = FastMCP(
    name="RM Collections MCP Server", on_duplicate="warn")

# register tools/resources/prompts/etc using FileSystemProvider
recipe_mcp_server.add_provider(
    FileSystemProvider(Path(__file__).parent / "mcp/recipe"))

collections_mcp_server.add_provider(
    FileSystemProvider(Path(__file__).parent / "mcp/collection"))

# the namespace (e.g. recipes, collections) will be prefixed to the tool/resource/prompt name
# the tool, @tool(name="search"), will be available as recipes_search when client receives the tool details
mcp.mount(recipe_mcp_server, namespace="recipes")
mcp.mount(collections_mcp_server, namespace="collections")
