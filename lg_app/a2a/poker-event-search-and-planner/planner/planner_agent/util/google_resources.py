from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import os
from langchain_google_community import CalendarToolkit
import logging
from langchain_google_community.calendar.get_calendars_info import GetCalendarsInfo
from langchain_google_community.calendar.search_events import CalendarSearchEvents
from langchain_google_community.calendar.current_datetime import GetCurrentDatetime
import json
from redis import Redis
from planner_agent.util.resource_registry import ResourceRegistry
from fastapi import Request

load_dotenv()

logger = logging.getLogger(__name__)

logger.info("Setting up Google Calendar API client...")


def save_token(email, token: dict, r: Redis):
    # save token to redis
    logger.info("saving token %s for user: %s", token, email)
    result = r.json().set(f"user:{email}:token", "$", json.dumps(token))
    logger.info("saved token for user: %s result %s", email, result)


def __build_credentials(email, r: Redis):
    # get token from redis and build credentials
    data = r.json().get(f"user:{email}:token", "$")
    if data:
        cred = json.loads(data[0])
        logger.info("token %s", cred)
        creds = Credentials(
            token=cred.get("access_token"),
        )
        return creds
    return None


def get_current_datetime(user_id, r: Redis):
    logger.info("get current datetime for user %s", user_id)
    creds = __build_credentials(user_id, r)
    if creds:
        api_resource = build("calendar", "v3", credentials=creds)
        data = GetCurrentDatetime.from_api_resource(api_resource=api_resource).invoke(
            {}
        )
        return data


def get_calendar_info(email, r: Redis):
    creds = __build_credentials(email, r)
    logger.info("credentials %s", creds)
    # get_current_datetime(user_id, r)
    if creds:
        api_resource = build("calendar", "v3", credentials=creds)
        info = GetCalendarsInfo(api_resource=api_resource)
        logger.info("calendar info %s", info)
        data = info.invoke({})
        logger.info("calendar_info {%s}", data)


def get_refresh_token(email, r: Redis):
    """get google refresh token from redis for the given email"""
    data = r.json().get(f"user:{email}:token", "$")
    if data:
        cred = json.loads(data[0])
        return cred.get("refresh_token")
    return None
