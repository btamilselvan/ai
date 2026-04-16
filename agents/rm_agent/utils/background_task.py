from datastore.database import save_messages_to_pg, save_messages_to_pg, save_appstate_to_redis
from agents.summarization_agent import SummarizationAgent
from utils.resource_registry import ResourceRegistry
from utils.models import AppState, ConversationModel
import logging
import traceback

logger = logging.getLogger(__name__)

SUMMARY_THRESHOLD = 10
NUMBER_OF_MESSAGES_SUMMARIZE = 5
AGENT_NAME = "summarization_agent"


async def run_background_tasks(resource_registry: ResourceRegistry, appstate: AppState):
    """ function to run background tasks for summarizing messages and saving messages to database and redis. this function is called in the chat endpoint after getting response from the agent and before returning the response to the user. """

    thread_id = appstate.thread_id
    # persist only the new messages. trim the history from the messages list
    messages = appstate.messages[appstate.messages_count:]
    # save messages in PG for long term memory and in Redis for short term memory
    await save_messages_to_pg(resource_registry.async_session, thread_id, messages)

    save_appstate_to_redis(
        resource_registry.redis_client, thread_id, appstate)

    lock_key = f"summary_lock:{thread_id}"
    try:
        # lock the thread
        if resource_registry.redis_client.set(lock_key, "processing", nx=True, ex=60):
            logger.info("summarize messages...")
            await __summarize_messages(resource_registry, appstate)
        else:
            logger.warning("summarization is in progress already.. ")
    except Exception as e:
        logger.error("unable to summarize messages %s", e)
        traceback.print_exc()
    finally:
        resource_registry.redis_client.delete(lock_key)

def __get_messages_to_summarize(appstate: AppState):
    """ summarize messages for a given thread id and save the summary to the database and redis.
    summarize when the total number of messages in the conversation thread exceeds a certain threshold (e.g. 10 messages), 
    and include the most recent assistant message in the messages to be summarized, as that would likely contain the most relevant information for summarization.
    """
    # get messages for the thread id from redis
    thread_id: str = appstate.thread_id
    messages: list[ConversationModel] = appstate.messages
    if not messages:
        logger.info(
            "no messages found in redis for thread_id %s, skipping summarization", thread_id)
        return
    messages_to_summarize: list[ConversationModel] = []
    # fetch first 5 message for summarization
    # make sure include the most recent assistant message in the messages to be summarized, as that would likely contain the most relevant information for summarization
    if len(messages) >= SUMMARY_THRESHOLD:
        index = 0
        while index < len(messages):

            messages_to_summarize.append(messages[index])

            index += 1
            if len(messages_to_summarize) >= NUMBER_OF_MESSAGES_SUMMARIZE and messages_to_summarize[-1].role == "user":
                messages_to_summarize.remove(messages_to_summarize[-1])
                return messages_to_summarize
    else:
        logger.debug(
            "not enough messages to summarize for thread_id %s, skipping summarization", thread_id)
    return messages_to_summarize


async def __summarize_messages(resource_registry: ResourceRegistry, appstate: AppState):
    # summarize messages if the number of messages in the conversation thread exceeds a certain threshold (e.g. 10 messages)
    
    thread_id: str = appstate.thread_id
    messages_to_summarize: list = __get_messages_to_summarize(appstate)

    logger.debug("message to summarize %s", messages_to_summarize)

    if messages_to_summarize:

        logger.debug("messages to summarize %s", messages_to_summarize)

        agent: SummarizationAgent = resource_registry.ai_clients[AGENT_NAME]

        # call LLM to summarize messages
        updated_appstate = agent.invoke_llm(context="", appstate=AppState(thread_id=appstate.thread_id,
                                                                              messages=messages_to_summarize, current_agent_name=AGENT_NAME))
        llm_summary = updated_appstate.messages[-1]

        logger.debug("summary %s", llm_summary.content)

        summary_count = len(messages_to_summarize)

        summary = ConversationModel(thread_id=appstate.thread_id,
                                    role="system", content=llm_summary.content, summary=llm_summary.content)
        # save summary to pg
        await save_messages_to_pg(resource_registry.async_session,
                                      thread_id, [summary])

        # add summary to redis and trim old messages
        available_messages = appstate.messages
        updated_messages = available_messages[summary_count:]

        updated_messages.insert(0, summary)
        appstate.messages = updated_messages
        appstate.messages_count = len(updated_messages)
        save_appstate_to_redis(
            resource_registry.redis_client, thread_id, appstate)
