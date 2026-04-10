from openai import OpenAI
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from utils.env_settings import EnvSettings
from utils.models import ChatRequest
import traceback
from chromadb import Search, K, Knn
from mcp import ClientSession
import json
import logging
from utils.agents import BaseAgent

logger = logging.getLogger(__name__)


class RecipeManagerAgent(BaseAgent):

    SEARCH_THRESHOLD = 0.9

    NAME = "main_agent"
    MAX_TOOL_CALLS_ALLOWED_PER_CONVERSATION = 5

    # System prompt
    SYSTEM_PROMPT_OLD = """
    # ROLE
    You are the Professional Recipe Manager Assistant. Your goal is to help users discover, create, and audit recipes with high precision and safety.
    
    # OPERATIONAL PROTOCOL (MCP)
    1. **Discovery (Search)**: You have access to a recipe search tool. Use it only if you lack the specific information requested or if the user asks for a full, detailed recipe. 
    If the user asks a general comparison or a 'which is better' question that you can answer using your internal knowledge, answer directly without calling the tool.
    2. **Deep Dive (Resources)**: You can fetch the full content of a recipe using the receipe ID returned by recipe_search. Fetch the full content only when the user asks full details about that recipe.
    3. **Safety First**: Before suggesting any cooking steps, reference kitchen safetey guidelines to ensure the instructions follow professional kitchen standards.
    4. **Unit Consistency**: For all measurement conversions or scaling, reference the ground truth in measurement guide.
    5. Do not attempt to make more than 3 tool calls.

    Use the provided context when answering questions about food safety, cooking techniques, or measurements.

    # Context
    {context}
    """

    SYSTEM_PROMPT = """
    
    # IDENTITY
        You are the Professional Recipe Manager Assistant. You provide expert culinary advice, recipe discovery, and safety audits with precision and professional kitchen standards.

        # OPERATIONAL PROTOCOL (MCP)
        1. **Internal Knowledge vs. Discovery**: 
        - ALWAYS prioritize your internal knowledge for general culinary questions (e.g., "which nut is better," "what can I substitute for eggs," "flavor profiles"). 
        - DO NOT use the `recipe_search` tool for comparisons, general nutritional advice, or ingredient science.
        - ONLY trigger `recipe_search` when the user explicitly requests a specific, external recipe or when you cannot satisfy the query with your training data.

        2. **Efficient Searching**:
        - If a search is required, perform ONE comprehensive search query. 
        - DO NOT perform multiple parallel searches for individual ingredients unless the user's request is multi-faceted and unrelated.

        3. **Deep Dive (Resources)**: 
        - Use `get_recipe_details` (or your specific ID tool) ONLY after a user identifies a specific recipe from the search results they wish to explore.

        4. **Safety & Standards**:
        - Every instruction must adhere to professional kitchen safety guidelines (cross-contamination, internal temperatures, knife safety).

        5. **Unit Integrity**:
        - Use the `measurement_guide` tool for all conversions. Do not guess math for scaling recipes.

        # CONSTRAINTS
        - **Tool Quota**: You are strictly limited to a maximum of 3 tool calls per turn. Use them sparingly.
        - **Directness**: If you can answer without a tool, do so immediately.
        
        Use the provided context when answering questions about food safety, cooking techniques, or measurements.

        # Context
        {context}
    
    """

    def __init__(self, client: OpenAI, model, temperature=1.6, tools: list = None, max_tokens=4096):
        super().__init__(client, model, temperature, tools, max_tokens)
        self.__init_chroma_collection()
        logger.info("RM agent initialized...")

    def __init_chroma_collection(self):
        logger.info("initializing chroma collection...")

        settings = EnvSettings()

        logger.debug("tenant id %s", settings.hf_token)
        chroma_client = chromadb.CloudClient(tenant=settings.chroma_tenant, database=settings.chroma_database,
                                             api_key=settings.chroma_cloud_api_key)
        # embedding_functions.HuggingFaceEmbeddingFunction(api_key=settings.hf_token, model_name="")

        self.__collection = chroma_client.get_collection(
            "rm_knowledge_collection_1")
        logger.info(
            "chroma collection initialized...%s", self.__collection.configuration_json)

    async def orchestrate(self, chat_request: ChatRequest, history: list, toolname_servername_map: dict, mcp_session_map: dict):

        try:
            # step 1 - Retrieve data from Chroma DB (vector store) - provide context
            # print("executing step 1...")
            context = self.__get_context_from_database(
                chat_request.message) or ""

            length_of_history = len(history)

            logger.debug("length of history: %s", length_of_history)

            # logger.debug(f"history {history}")
            # combine history and new messages for processing in the orchestration loop
            messages = history + \
                [{"role": "user", "content": chat_request.message}]

            loop_count = 0

            while loop_count < self.MAX_TOOL_CALLS_ALLOWED_PER_CONVERSATION:

                loop_count += 1

                # step 2 - call LLM
                # pass the context and the user query to the LLM and get a response
                llm_response = self.call_llm(context, messages)
                logger.debug("llm response: %s", llm_response)

                # step 3 - check if tool calls are present in response
                tool_calls = self.__get_tool_calls(llm_response)

                if (len(tool_calls) > 0):
                    # step 4 - execute tool calls and send back to LLM (repeat for all tool calls)
                    messages.append(
                        {"role": "assistant", "content": llm_response.choices[0].message.content, "tool_calls": tool_calls})

                    for tool in tool_calls:
                        logger.debug("executing tool call: %s", tool)
                        server_name = toolname_servername_map.get(
                            tool.function.name)
                        mcp_session: ClientSession = mcp_session_map.get(
                            server_name)

                        tool_response = await mcp_session.call_tool(tool.function.name, json.loads(tool.function.arguments))

                        logger.debug("tool response: %s", tool_response)

                        tool_response_content_text = tool_response.content[
                            0].text if tool_response.content else ""

                        # add tool response to the messages to be sent back to the LLM for the next iteration of the loop
                        messages.append(
                            {"role": "tool", "content": tool_response_content_text, "tool_calls": [tool], "tool_call_id": tool.id})
                else:
                    logger.debug(
                        "no tool calls detected, returning response...")
                    # logger.debug(f"final messages: {new_messages}")
                    messages.append(
                        {"role": "assistant", "content": llm_response.choices[0].message.content, "tool_calls": tool_calls})
                    # return the new messages excluding the history messages
                    return messages[length_of_history:]
            # max tool calls reached, returning response with a warning about max tool calls reached
            messages.append(
                {"role": "assistant", "content": "Max tool calls reached. Returning response without executing further tool calls.", "tool_calls": []})
            return messages[length_of_history:]
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            traceback.print_exc()
            return None

    def __get_context_from_database(self, message):
        try:
            logger.debug("querying chroma db with: %s", message)

            search = Search().rank(Knn(query=message)).limit(
                limit=5).select(K.ID, K.DOCUMENT, K.SCORE)

            results = self.__collection.search(search)

            payloads = zip(
                results["ids"], results["documents"], results["scores"])

            context = []

            for payload in payloads:
                ids, documents, scores = payload
                # print(f"payload {payload}")

                for id, doc, score in zip(ids, documents, scores):
                    if score is not None and score <= self.SEARCH_THRESHOLD:
                        # print(f"id: {id}, document: {doc}, score: {score}")
                        context.append(doc)

            return "\n".join(context)

        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            return None

    def __get_tool_calls(self, response):
        if response.choices and response.choices[0].message.tool_calls:
            return response.choices[0].message.tool_calls
        return []
