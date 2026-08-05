from google.cloud import pubsub_v1
# from google.pubsub import g
from googleapiclient.discovery import build

project_id = "trocks-ai-gmail"
topic_id = "trocks-ai-gmail-topic"
topic_name = f"projects/{project_id}/topics/{topic_id}"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)
global topic
# topic = publisher.create_topic(request={"name": topic_path})
try:
    topic = publisher.get_topic(topic=topic_name)
    print(f"Topic already existed: {topic.name}")
except Exception as e:
    print(f"topic {topic_name} does not exist.. create one")
    topic = publisher.create_topic(request={"name": topic_path})


gmail = build('gmail', 'v1')

request = {
  'labelIds': ['INBOX'],
  'topicName': topic_name
}
response = gmail.users().watch(userId='me', body=request).execute()

print(f"Watch established! Current History ID: {response['historyId']}")
print(f"Expiration Timestamp: {response['expiration']}")


