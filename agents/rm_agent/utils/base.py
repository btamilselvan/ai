import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class BaseAgent:
    def __init__(self, client: OpenAI, model, temperature=1.6, tools: list = None, max_tokens=4096):
        logger.info("RM agent initialized...")
        self.client = client
        self.model = model
        self.temperature = temperature
        self.tools = tools
        self.max_tokens = max_tokens

    def call_llm(self, context: str, messages: list):
        # logger.debug(f"messages: {messages}")

        prompt = self.SYSTEM_PROMPT.format(context=context)

        # add system prompt at index 0
        messages = [
            {"role": "system", "content": prompt}
        ] + messages
        
        logger.debug("calling LLM with messages: %s", messages)

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

