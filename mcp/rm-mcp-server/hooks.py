from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from mcp.types import InitializeRequestParams, ErrorData
from mcp.shared.exceptions import McpError
import logging
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_API_KEY = os.getenv("MCP_SERVER_API_KEY")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY")

logger = logging.getLogger(__name__)


class LoggingMiddleware(Middleware):

    async def on_message(self, context: MiddlewareContext, call_next):
        """ use this hook to intercept everything """
        logger.debug(f"Processing message: {context.method}")

        ctx = context.fastmcp_context

        if ctx.request_context:
            # session available
            request_id = ctx.request_id
            session_id = ctx.session_id
            logger.debug("Request ID: %s, Session ID: %s",
                         request_id, session_id)

        result = await call_next(context)
        logger.debug(f"Finished processing message: {context.method}")
        return result

    # async def on_request(self, context: MiddlewareContext, call_next):
    #     """ use this hook to intercept requests and authorize them """

    #     logger.debug(f"Processing request: {context.method}")
    #     result = await call_next(context)
    #     logger.debug(f"Finished processing request: {context.method}")
    #     return result


class AuthMiddleware(Middleware):

    def __authenticate_client(self, headers):
        """ authenticate the client using the x-api-key header """
        api_key = headers.get("x-api-key") or LOCAL_API_KEY
        logger.debug("API Key: %s, %s", api_key, SERVER_API_KEY)
        if not api_key or api_key != SERVER_API_KEY:
            logger.error("Invalid or missing API key")
            raise McpError(error=ErrorData(
                code=401, message="Invalid API Key"))
        logger.debug("Client authenticated successfully")

    async def on_initialize(self, context: MiddlewareContext, call_next):
        """ use this hook to intercept initialize request, allow/reject connections by client name, etc """

        logger.debug("Client initializing connection...")
        # client_info = context.message.params.get("clientInfo", {})
        # client_name = client_info.get("name", "unknown")

        init_params: InitializeRequestParams = context.message.params
        logger.debug("init param %s", init_params)
        client_name = init_params.clientInfo.name

        logger.debug("client name %s", client_name)

        # self.__authenticate_client(get_http_headers())

        result = await call_next(context)
        logger.debug("Client initialized successfully!")
        return result

    async def on_request(self, context, call_next):
        """ use this hook to intercept requests and authorize them """
        self.__authenticate_client(get_http_headers())
        logger.debug("Authorized request: %s", context.message)
        return await super().on_request(context, call_next)
