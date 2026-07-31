import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.cloud import pubsub_v1
from exceptions import InvalidCredentials
import logging
import base64
from models import MailMessage
import html2text

# from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://mail.google.com/"]
TOKEN_FILE = "token.json"
PROJECT_ID = "trocks-ai-gmail"
TOPIC_ID = "trocks-ai-gmail-topic"
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/{TOPIC_ID}"

h2Text = html2text.HTML2Text()
h2Text.ignore_links = False
h2Text.ignore_images = True
h2Text.body_width = 0

# def _clean_html_to_text(html_content):
#   # Parse the HTML
#   soup = BeautifulSoup(html_content, "html.parser")

#   # Remove unwanted elements like scripts and styles
#   for script_or_style in soup(["script", "style"]):
#     script_or_style.decompose()

#   # Get text and handle whitespace
#   text = soup.get_text(separator="\n")

#   # Clean up excessive blank lines
#   lines = [line.strip() for line in text.splitlines()]
#   clean_text = "\n".join(line for line in lines if line)

#   return clean_text


def get_credentials():
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds:
            raise InvalidCredentials("Invalid credentials")
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
    else:
        raise InvalidCredentials("credentials not found")


def _complete_oauth_workflow():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())


def _get_user_profile():
    service = build("gmail", "v1", credentials=get_credentials())

    # API Call: Get User Profile - Verify the token
    profile = service.users().getProfile(userId="me").execute()
    print(f"Email address: {profile['emailAddress']}")
    print(f"Messages total: {profile['messagesTotal']}")


def _watch():

    # assume valide token exist
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Initialize the Gmail API service
    service = build("gmail", "v1", credentials=creds)

    print(dir(service))

    print(dir(service.users()))
    print(dir(service.users().messages()))
    print(dir(service.users().history().list))

    # Define the watch request payload
    # Must format your topic as: projects/{project_id}/topics/{topic_name}
    body = {"topicName": TOPIC_NAME, "labelIds": ["INBOX"]}

    try:
        response = service.users().watch(userId="me", body=body).execute()
        print("Watch response received successfully: {response}")
        print(f"History ID: {response.get('historyId')}")
        print(f"Expiration (timestamp): {response.get('expiration')}")
    except Exception as e:
        print(f"exception occurred. unable to watch {e}")


def _create_pubsub_topic():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    global topic

    try:
        topic = publisher.get_topic(topic=TOPIC_NAME)
        print(f"Topic already existed: {topic.name}")
    except Exception as e:
        print(f"topic {TOPIC_NAME} does not exist.. create one")
        topic = publisher.create_topic(request={"name": topic_path})


def _get_body(parts):
    for part in parts:
        # get text/html content if exists first
        if part["mimeType"] == "text/html":
            base64_content = part["body"]["data"]
            body_content = base64.urlsafe_b64decode(base64_content).decode(
                "utf-8", errors="ignore"
            )
            # plain_text = _clean_html_to_text(body_content)
            markdown_text = h2Text.handle(body_content)
            # logger.info("HTML Body: {%s}", plain_text)
            # logger.info("HTML Body: {%s}", markdown_text)
            # return markdown_text
            logger.info("HTML Body: {%s}", body_content)
            return markdown_text

    # otherwise look for text/plain
    for part in parts:
        if part["mimeType"] == "text/plain":
            base64_content = part["body"]["data"]
            body_content = base64.urlsafe_b64decode(base64_content).decode(
                "utf-8", errors="ignore"
            )
            logger.info("Plain Body: {%s}", body_content)
            return body_content
    return None


def _fetch_mail(message_id, service):
    logger.info("Fetching message ID: %s", message_id)
    try:
        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        logger.info("Message ID: %s", message["id"])
        # logger.info("Paylod: %s", message["payload"])
        headers = message["payload"]["headers"]
        mime_type = message["payload"]["mimeType"]
        # logger.info("Headers: %s", headers)
        logger.info("MIME Type: %s", mime_type)

        for header in headers:
            # logger.info(f"{header['name']}: {header['value']}")
            if header["name"] == "Subject":
                subject = header["value"]
            elif header["name"] == "From":
                email_from = header["value"]
            elif header["name"] == "Date":
                received_on = header["value"]
        logger.info("From: %s", email_from)
        logger.info("Subject: %s", subject)
        logger.info("Received on: %s", received_on)

        ## body.data will be empty for multipart/* type of emails
        if "multipart" in mime_type:
            # read body from parts
            logger.info("multipart email. need to parse parts")
            body_content = _get_body(message["payload"]["parts"])
        else:
            # logger.info("Body: %s", message["payload"]["body"])
            base64_content = message["payload"]["body"]["data"]
            body_content = base64.urlsafe_b64decode(base64_content).decode(
                "utf-8", errors="ignore"
            )
            # logger.info("Body: {%s}", body_content)

        mail_message = MailMessage(
            message_id=message["id"],
            subject=subject,
            sender=email_from,
            body=body_content,
            received_on=received_on,
        )
        return mail_message
    except Exception as e:
        logger.exception("Error fetching message: %s", e)
        return None


def fetch_mails(start_history_id):
    # build the gmail service
    service = build("gmail", "v1", credentials=get_credentials())
    logger.info("Fetching mails from history ID: %s", start_history_id)
    # https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list
    response = (
        service.users()
        .history()
        .list(
            userId="me", startHistoryId=start_history_id, historyTypes=["messageAdded"]
        )
        .execute()
    )
    histories = response.get("history", [])
    logger.info("histories list %s", histories)
    messages = []
    for history in histories:
        # process only messageAdded messages
        if "messagesAdded" in history:
            messages_added = history["messagesAdded"]
            for message_added in messages_added:
                # labels = message_added["message"]["labelIds"]
                message = message_added["message"]
                labels = message.get("labelIds", [])
                logger.info(
                    "---------------------------------------------------------------"
                )
                # https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get
                mail_message = (
                    _fetch_mail(message_added["message"]["id"], service)
                    if "INBOX" in labels
                    else None
                )
                if mail_message:
                    messages.append(mail_message)
                logger.info(
                    "---------------------------------------------------------------"
                )
    return messages


if __name__ == "__main__":
    # _create_pubsub_topic()
    # _complete_oauth_workflow()
    # _get_user_profile()
    _watch()
    fetch_mails(14817201)
