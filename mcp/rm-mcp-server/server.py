from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
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


mcp = FastMCP(name="RM MCP Server", lifespan=app_lifespan)

mcp.add_middleware(LoggingMiddleware())
mcp.add_middleware(AuthMiddleware())
