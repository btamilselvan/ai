import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import logging
from langchain_google_community.calendar.get_calendars_info import GetCalendarsInfo
from langchain_google_community.calendar.search_events import CalendarSearchEvents
from langchain_google_community.calendar.current_datetime import GetCurrentDatetime
import json
from redis import Redis

load_dotenv()

logger = logging.getLogger(__name__)

logger.info("Setting up Google Calendar API client...")


def save_token(email, token: dict, r: Redis):
    # save token to redis
    logger.info("saving token %s for user: %s", token, email)
    result = r.json().set(f"user:{email}:token", "$", json.dumps(token))
    logger.info("saved token for user: %s result %s", email, result)



def get_refresh_token(email, r: Redis):
    """get google refresh token from redis for the given email"""
    data = r.json().get(f"user:{email}:token", "$")
    if data:
        cred = json.loads(data[0])
        return cred.get("refresh_token")
    return None


def update_access_token(email, access_token, r):
    data = r.json().get(f"user:{email}:token", "$")
    if data:
        cred = json.loads(data[0])
        cred["access_token"] = access_token
        result = r.json().set(f"user:{email}:token", "$", json.dumps(cred))
        logger.info("updated access token for user: %s result %s", email, result)
    else:
        logger.warning("data not found for the user %s", email)


def __build_credentials(email, r: Redis):
    # get token from redis and build credentials
    data = r.json().get(f"user:{email}:token", "$")
    if data:
        cred = json.loads(data[0])
        logger.info("token %s", cred)
        # Note: accesss token will be refreshed automatically using refresh token
        creds = Credentials(
            token=cred.get("access_token"),
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            refresh_token=cred.get("refresh_token"),
            token_uri=os.getenv("GOOGLE_TOKEN_URI"),
        )
        return creds
    return None


def get_current_datetime(email, r: Redis):
    """get current datetime for the user from google calendar"""
    logger.info("get current datetime for user %s", email)
    creds = __build_credentials(email, r)
    if creds:
        api_resource = build("calendar", "v3", credentials=creds)
        data = GetCurrentDatetime(api_resource=api_resource).invoke({})
        logger.info("current datetime %s", data)
        return data
    return None


def get_calendar_info(email, r: Redis):
    """get calendar info for the user from google calendar"""
    creds = __build_credentials(email, r)
    # logger.info("credentials %s", creds)
    # get_current_datetime(user_id, r)
    if creds:
        api_resource = build("calendar", "v3", credentials=creds)
        info = GetCalendarsInfo(api_resource=api_resource)
        logger.info("calendar info %s", info)
        data = info.invoke({})
        logger.info("calendar_info {%s}", data)
        return data
    return None


def search_events(email, r: Redis, min_datetime, max_datetime, single_events, query):
    creds = __build_credentials(email, r)
    if creds:
        api_resource = build("calendar", "v3", credentials=creds)
        calendar_info = get_calendar_info(email, r)
        logger.info(
            "searching events for user %s from %s to %s using calendar info %s",
            email,
            min_datetime,
            max_datetime,
            calendar_info,
        )
        search = CalendarSearchEvents(api_resource=api_resource)
        data = search.invoke(
            {
                "min_datetime": min_datetime,
                "max_datetime": max_datetime,
                "single_events": single_events,
                "query": query,
                "calendars_info": calendar_info,
            }
        )
        return data
