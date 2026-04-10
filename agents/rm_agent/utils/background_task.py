from utils.database import save_messages_to_pg, get_messages_to_summarize, save_messages_to_redis, add_summary_to_redis
from utils.agents import SummarizationAgent
from utils.resource_registry import ResourceRegistry
import logging

logger = logging.getLogger(__name__)

SUMMARY_THRESHOLD = 10
NUMBER_OF_MESSAGES_SUMMARIZE = 5
AGENT_NAME = "summarization_agent"


async def run_background_tasks(resource_registry: ResourceRegistry, thread_id: str, messages: list):
    """ function to run background tasks for summarizing messages and saving messages to database and redis. this function is called in the chat endpoint after getting response from the agent and before returning the response to the user. """
    # save messages in PG for long term memory and in Redis for short term memory
    saved_messages = await save_messages_to_pg(resource_registry.async_session, thread_id, messages)
    save_messages_to_redis(resource_registry.redis_client, thread_id, saved_messages)
    
    lock_key = f"summary_lock:{thread_id}"
    try:
        # lock the thread
        if resource_registry.redis_client.set(lock_key, "processing", nx=True, ex=60):
            logger.info("summarize messages...")
            await __summarize_messages(resource_registry, thread_id, messages)
        else:
            logger.warning("summarization is in progress already.. ")
    except Exception as e:
        logger.error("unable to summarize messages %s", e)
    finally:
        resource_registry.redis_client.delete(lock_key)
    
        

async def __summarize_messages(resource_registry: ResourceRegistry, thread_id: str, messages: list):
    # summarize messages if the number of messages in the conversation thread exceeds a certain threshold (e.g. 10 messages)
    messages_to_summarize: list = get_messages_to_summarize(
        resource_registry.redis_client, thread_id, SUMMARY_THRESHOLD, NUMBER_OF_MESSAGES_SUMMARIZE)

    logger.debug("message to summarize %s", messages_to_summarize)

    if messages_to_summarize:
        
        print(f"Messages to summarize: {messages_to_summarize}")

        agent: SummarizationAgent = resource_registry.ai_clients[AGENT_NAME]

        # call LLM to summarize messages
        llm_response = agent.call_llm("", messages_to_summarize)
        logger.info("summary %s", llm_response.choices[0].message.content)
        summary_count = len(messages_to_summarize)
        summary = {"role": "system",
                   "content": llm_response.choices[0].message.content, "tool_calls": [], "summary": llm_response.choices[0].message.content}
        # save summary to pg
        saved_messages = await save_messages_to_pg(resource_registry.async_session,
                            thread_id, [summary])

        # add summary to redis and trim old messages
        add_summary_to_redis(resource_registry.redis_client,
                             thread_id, saved_messages[0], summary_count)
