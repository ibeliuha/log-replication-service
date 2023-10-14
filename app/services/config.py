import os
from pydantic import BaseModel, Field
from utils.other import create_signature
import enum


class RetryMechanism(enum.Enum):
    UNIFORM = 'uniform'
    EXPONENTIAL = 'exponential'


class Config(BaseModel):
    MASTER_HOST: str = os.getenv('API_TOKEN')
    MASTER_PORT: int = os.getenv('MASTER_PORT')
    SECONDARY_PORT: int = os.getenv('SECONDARY_PORT')

    HEALTHCHECK_DELAY: int = Field(os.getenv('SECONDARY_PORT'), ge=60, le=120)
    SECONDARY_REMOVAL_DELAY: int = Field(os.getenv('SECONDARY_PORT'), ge=60)

    MAX_CONNECTION_TO_MASTER_DELAY: int = Field(os.getenv('MAX_CONNECTION_TO_MASTER_DELAY'), ge=1)
    CONNECTION_TO_MASTER_RETRY_INTERVAL: int = Field(os.getenv('CONNECTION_TO_MASTER_RETRY_INTERVAL'), ge=1)
    CONNECTION_TO_MASTER_RETRY_MECHANISM: RetryMechanism = Field(
        os.getenv('CONNECTION_TO_MASTER_RETRY_MECHANISM', 'uniform'))

    MAX_MESSAGE_POST_RETRY_DELAY = Field(os.getenv('MAX_MESSAGE_POST_RETRY_DELAY'), ge=1)
    MESSAGE_POST_RETRY_INTERVAL: int = Field(os.getenv('MESSAGE_POST_RETRY_INTERVAL'), ge=1)
    MESSAGE_POST_RETRIES_MECHANISM: RetryMechanism = Field(
        os.getenv('MESSAGE_POST_RETRIES_MECHANISM', 'uniform'))

    CLIENT_TOKEN: str = os.getenv('API_TOKEN')
    SERVICE_TOKEN: str = create_signature(os.getenv('API_TOKEN'))



