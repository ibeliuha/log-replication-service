import os
from pydantic import Field
from utils.other import create_signature, RetryMechanism
import enum
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    MASTER_HOST: str = Field(alias='MASTER_HOST')
    MASTER_PORT: int = Field(default=None, alias='MASTER_PORT')
    SECONDARY_PORT: int = Field(default=None, alias='SECONDARY_PORT')

    HEALTHCHECK_DELAY: int = Field(alias='HEALTHCHECK_DELAY', ge=60, le=120)
    SECONDARY_REMOVAL_DELAY: int = Field(os.getenv('SECONDARY_REMOVAL_DELAY'), ge=60)

    MAX_CONNECTION_TO_MASTER_DELAY: int = Field(alias='MAX_CONNECTION_TO_MASTER_DELAY', ge=1)
    CONNECTION_TO_MASTER_RETRY_INTERVAL: int = Field(alias='CONNECTION_TO_MASTER_RETRY_INTERVAL', ge=1)
    CONNECTION_TO_MASTER_RETRY_MECHANISM: RetryMechanism = Field(alias='CONNECTION_TO_MASTER_RETRY_MECHANISM',
                                                                 default='uniform')
    MAX_MESSAGE_POST_RETRY_DELAY: int = Field(alias='MAX_MESSAGE_POST_RETRY_DELAY', ge=1)
    MESSAGE_POST_RETRY_INTERVAL: int = Field(alias='MESSAGE_POST_RETRY_INTERVAL', ge=1)
    MESSAGE_POST_RETRIES_MECHANISM: RetryMechanism = Field(alias='MESSAGE_POST_RETRIES_MECHANISM',
                                                           default='exponential')
    CLIENT_TOKEN: str = Field(alias='API_TOKEN')
    SERVICE_TOKEN: str = create_signature(os.getenv('API_TOKEN'))



