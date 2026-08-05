import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import pubsub_v1
from exceptions import InvalidCredentials
import logging
import base64
import redis
from models import MailMessage
import html2text

import config

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

# Gmail's history.list only returns records *after* startHistoryId -- the
# historyId carried by a push notification is the mailbox's current state
# (i.e. the very change that triggered the notification), so using it
# directly as startHistoryId always comes back empty. We must instead track
# our own "last processed" checkpoint and advance it after each successful
# fetch; see fetch_mails() below.
LAST_HISTORY_ID_KEY = "gmail:last_history_id"

_redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,
)


def _get_last_history_id() -> str | None:
    return _redis_client.get(LAST_HISTORY_ID_KEY)


def _set_last_history_id(history_id) -> None:
    _redis_client.set(LAST_HISTORY_ID_KEY, str(history_id))

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
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("No valid credentials found. Opening browser for login.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())


def _get_user_profile():
    service = build("gmail", "v1", credentials=get_credentials())

    # API Call: Get User Profile - Verify the token
    profile = service.users().getProfile(userId="me").execute()
    logger.info(f"Email address: {profile['emailAddress']}")
    logger.info(f"Messages total: {profile['messagesTotal']}")


def renew_watch():
    # Gmail watch subscriptions expire after ~7 days and must be re-registered
    # before then to keep push notifications flowing.

    # Initialize the Gmail API service
    service = build("gmail", "v1", credentials=get_credentials())

    logger.info("Service initialized")
    logger.info("Available methods: %s", dir(service))

    logger.info("Available methods for users(): %s", dir(service.users()))
    logger.info("Available methods for users().messages(): %s", dir(service.users().messages()))
    logger.info("Available methods for users().history().list: %s", dir(service.users().history().list))

    # Define the watch request payload
    # Must format your topic as: projects/{project_id}/topics/{topic_name}
    body = {"topicName": TOPIC_NAME, "labelIds": ["INBOX"]}

    try:
        response = service.users().watch(userId="me", body=body).execute()
        logger.info("Watch response received successfully: {response}")
        logger.info(f"History ID: {response.get('historyId')}")
        logger.info(f"Expiration (timestamp): {response.get('expiration')}")
        # Seed the fetch_mails() checkpoint only if one doesn't exist yet, so
        # a fresh install has a valid starting point but a routine weekly
        # renewal never clobbers (and silently skips a backlog behind) the
        # real last-processed checkpoint.
        if response.get("historyId") and not _get_last_history_id():
            _set_last_history_id(response["historyId"])
            logger.info("Seeded initial history checkpoint: %s", response["historyId"])
        return response
    except Exception as e:
        logger.exception(f"exception occurred. unable to watch {e}")
        return None


def _create_pubsub_topic():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    global topic

    try:
        topic = publisher.get_topic(topic=TOPIC_NAME)
        logger.info(f"Topic already existed: {topic.name}")
    except Exception as e:
        logger.info(f"topic {TOPIC_NAME} does not exist.. create one")
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
            # logger.info("HTML Body: {%s}", body_content)
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


def trash_message(message_id, service=None):
    if service is None:
        service = build("gmail", "v1", credentials=get_credentials())
    service.users().messages().trash(userId="me", id=message_id).execute()
    logger.info("Trashed message ID: %s", message_id)


def fetch_mails(notification_history_id):
    # build the gmail service
    service = build("gmail", "v1", credentials=get_credentials())

    # The push notification's historyId is the mailbox's *current* state, not
    # a safe startHistoryId -- history.list only returns records strictly
    # after startHistoryId, so passing the notification's own id always comes
    # back empty. Use our persisted "last processed" checkpoint instead, and
    # only fall back to the notification's id if we have no checkpoint yet
    # (e.g. before the first watch() has ever run).
    start_history_id = _get_last_history_id() or notification_history_id
    logger.info(
        "Fetching mails from history ID: %s (notification historyId was %s)",
        start_history_id,
        notification_history_id,
    )
    # https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list
    # TODO: this doesn't page through nextPageToken -- a notification batch
    # with enough history entries to span multiple pages will silently lose
    # the entries on later pages.
    # Scope to INBOX (matches the watch() registration) and to "messageAdded"
    # events server-side. This is authoritative, unlike labelIds on the
    # minimal message object embedded in messagesAdded entries below, which
    # Gmail leaves unpopulated (labelIds always came back empty there, so an
    # "INBOX" in labels client-side check always failed and skipped every
    # new message, not just deletions).
    try:
        response = (
            service.users()
            .history()
            .list(
                userId="me",
                startHistoryId=start_history_id,
                labelId="INBOX",
                historyTypes=["messageAdded"],
            )
            .execute()
        )
    except HttpError as e:
        if e.resp.status == 404:
            # startHistoryId too old / outside Gmail's retention window.
            # Fast-forward to the notification's id instead of retrying the
            # same stale checkpoint forever; any mail strictly between the
            # stale checkpoint and this notification is unrecoverably missed.
            logger.warning(
                "startHistoryId %s is invalid/expired (404); fast-forwarding "
                "checkpoint to notification historyId %s",
                start_history_id,
                notification_history_id,
            )
            _set_last_history_id(notification_history_id)
            return []
        raise

    histories = response.get("history", [])
    logger.info("histories list %s", histories)
    messages = []
    for history in histories:
        for message_added in history.get("messagesAdded") or []:
            message_id = message_added["message"]["id"]
            logger.info(
                "---------------------------------------------------------------"
            )
            # https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get
            mail_message = _fetch_mail(message_id, service)
            if mail_message:
                messages.append(mail_message)
            logger.info(
                "---------------------------------------------------------------"
            )

    # Advance the checkpoint to the mailbox's historyId as of this call
    # (authoritative per Gmail), falling back to the notification's id.
    _set_last_history_id(response.get("historyId") or notification_history_id)
    return messages


if __name__ == "__main__":
    # _create_pubsub_topic()
    _complete_oauth_workflow()
    # _get_user_profile()
    renew_watch()
    fetch_mails(14817201)
