from utils.base import BaseAgent
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class SummarizationAgent(BaseAgent):
    SYSTEM_PROMPT = """ You are a helpful assistant that summarizes conversation threads. 
    You will be provided with the conversation history in the form of messages, and your task is to generate a concise summary of the conversation that captures the main points and important information. 
    The summary should be informative and provide a clear overview of the conversation thread, while omitting any irrelevant details. """

    def __init__(self, client: OpenAI, model, temperature=1.6, max_tokens=4096):
        super().__init__(client, model, temperature, max_tokens=max_tokens)
        logger.info("Summarization agent initialized...")
