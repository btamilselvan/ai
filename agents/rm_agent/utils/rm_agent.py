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


class RecipeManagerAgent():

    SEARCH_THRESHOLD = 0.9

    NAME = "main_agent"
    MAX_TOOL_CALLS_ALLOWED_PER_CONVERSATION = 5

    # System prompt
    SYSTEM_PROMPT = """
    # ROLE
    You are the Professional Recipe Manager Assistant. Your goal is to help users discover, create, and audit recipes with high precision and safety.

    # OPERATIONAL PROTOCOL (MCP)
    1. **Discovery (Search)**: Use the `recipe_search` tool for any query involving recipe titles or ingredients. It returns the top 5 matches.
    2. **Deep Dive (Resources)**: Once you have a recipe ID from a search, ALWAYS fetch the full content using the resource URI `recipe://details/{{id}}` before providing instructions.
    3. **Safety First**: Before suggesting any cooking steps, reference kitchen safetey guidelines to ensure the instructions follow professional kitchen standards.
    4. **Unit Consistency**: For all measurement conversions or scaling, reference the ground truth in measurement guide.

    Use the provided context when answering questions about food safety, cooking techniques, or measurements.

    # Context
    {context}
    """

    def __init__(self, client: OpenAI, model, temperature=1.6, tools: list = None, max_tokens=4096):
        print("RM agent initialized...")
        self.client = client
        self.model = model
        self.temperature = temperature
        self.tools = tools
        self.max_tokens = max_tokens
        self.__init_chroma_collection()

    def __init_chroma_collection(self):
        print("initializing chroma collection...")

        settings = EnvSettings()

        print(f"tenant id {settings.hf_token}")
        chroma_client = chromadb.CloudClient(tenant=settings.chroma_tenant, database=settings.chroma_database,
                                             api_key=settings.chroma_cloud_api_key)
        # embedding_functions.HuggingFaceEmbeddingFunction(api_key=settings.hf_token, model_name="")

        self.__collection = chroma_client.get_collection(
            "rm_knowledge_collection_1")
        print(
            f"chroma collection initialized...{self.__collection.configuration_json}")

    def __call_llm(self, context: str, messages: list):
        # print(f"messages: {messages}")

        prompt = self.SYSTEM_PROMPT.format(context=context)

        # add system prompt at index 0
        messages = [
            {"role": "system", "content": prompt}
        ] + messages

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=messages,
                # stream=True,
                tools=self.tools,
            )
            # for chunk in response:
            #     yield chunk
            return response
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    async def orchestrate(self, chat_request: ChatRequest, history: list, toolname_servername_map: dict, mcp_session_map: dict):

        try:
            # step 1 - Retrieve data from Chroma DB (vector store) - provide context
            # print("executing step 1...")
            context = self.__get_context_from_database(
                chat_request.message) or ""

            length_of_history = len(history)

            print(f"length of history: {length_of_history}")

            # print(f"history {history}")
            # combine history and new messages for processing in the orchestration loop
            messages = history + \
                [{"role": "user", "content": chat_request.message}]

            loop_count = 0

            while loop_count < self.MAX_TOOL_CALLS_ALLOWED_PER_CONVERSATION:

                loop_count += 1

                # step 2 - call LLM
                # pass the context and the user query to the LLM and get a response
                llm_response = self.__call_llm(context, messages)
                print(f"llm response: {llm_response}")

                # step 3 - check if tool calls are present in response
                tool_calls = self.__get_tool_calls(llm_response)

                if (len(tool_calls) > 0):
                    # step 4 - execute tool calls and send back to LLM (repeat for all tool calls)
                    messages.append(
                        {"role": "assistant", "content": llm_response.choices[0].message.content, "tool_calls": tool_calls})

                    for tool in tool_calls:
                        # print(f"executing tool call: {tool}")
                        server_name = toolname_servername_map.get(
                            tool.function.name)
                        mcp_session: ClientSession = mcp_session_map.get(
                            server_name)

                        tool_response = await mcp_session.call_tool(tool.function.name, json.loads(tool.function.arguments))

                        # print(f"tool response: {tool_response}")

                        tool_response_content_text = tool_response.content[
                            0].text if tool_response.content else ""

                        # add tool response to the messages to be sent back to the LLM for the next iteration of the loop
                        messages.append(
                            {"role": "tool", "content": tool_response_content_text, "tool_calls": [tool], "tool_call_id": tool.id})
                else:
                    print("no tool calls detected, returning response...")
                    # print(f"final messages: {new_messages}")
                    messages.append(
                        {"role": "assistant", "content": llm_response.choices[0].message.content, "tool_calls": tool_calls})
                    # return the new messages excluding the history messages
                    return messages[length_of_history:]
            # max tool calls reached, returning response with a warning about max tool calls reached
            messages.append(
                {"role": "assistant", "content": "Max tool calls reached. Returning response without executing further tool calls.", "tool_calls": []})
            return messages[length_of_history:]
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            return None

    def __get_context_from_database(self, message):
        try:
            print(f"querying chroma db with: {message}")

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
