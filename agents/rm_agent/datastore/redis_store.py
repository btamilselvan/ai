import redis
from datastore.database import Message, MessageSchema, convert_messages_to_json


def store_message_in_redis(r: redis.Redis, thread_id: str, message: Message):
    """ store message in redis """
    result = None
    if (r.exists(thread_id)):
        # if the thread already exists, we want to append the message to the existing list of messages for that thread
        result = r.json().arrappend(
            thread_id, "$", MessageSchema.model_validate(message).model_dump(mode='json'))
    else:
        # if the thread does not exist, we want to create a new list of messages for that thread and add the message to that list
        result = r.json().set(thread_id, "$", [
            MessageSchema.model_validate(message).model_dump(mode='json')])

    print(f"result of storing message in redis: {result}")
    return result


def store_messages_in_redis(r: redis.Redis, thread_id: str, messages: list[Message]):
    """ store message in redis """

    print(f"storing messages in redis for thread_id: {thread_id} with messages: {messages}")

    json_messages = convert_messages_to_json(messages)
    
    result = None
    if (r.exists(thread_id)):
        # if the thread already exists, we want to append the message to the existing list of messages for that thread
        result = r.json().arrappend(
            thread_id, "$", json_messages)
    else:
        # if the thread does not exist, we want to create a new list of messages for that thread and add the message to that list
        result = r.json().set(thread_id, "$", json_messages)

    print(f"result of storing message in redis: {result}")
    return result
