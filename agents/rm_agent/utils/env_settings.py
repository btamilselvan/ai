from pydantic_settings import BaseSettings
from typing import Dict


class EnvSettings(BaseSettings):

    mcp_servers: Dict[str, str]
    agents: Dict[str, str]
    chroma_cloud_api_key: str
    chroma_tenant: str
    chroma_database: str
    hf_token: str
