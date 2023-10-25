import os
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
import enum
import hashlib
from typing import Optional


class RetryMechanism(enum.Enum):
    UNIFORM = 'uniform'
    EXPONENTIAL = 'exponential'


class Config(BaseSettings):
    HOSTNAME: str = Field(alias='HOSTNAME')
    MASTER_HOST: str = Field(alias='MASTER_HOST')
    MASTER_PORT: int = Field(default=None, alias='MASTER_PORT')
    SECONDARY_PORT: int = Field(default=None, alias='SECONDARY_PORT')

    HEALTHCHECK_DELAY: int = Field(alias='HEALTHCHECK_DELAY', ge=1)
    SECONDARY_REMOVAL_DELAY: int = Field(os.getenv('SECONDARY_REMOVAL_DELAY'), ge=1)

    MAX_CONNECTION_TO_MASTER_DELAY: int = Field(alias='MAX_CONNECTION_TO_MASTER_DELAY', ge=1)
    CONNECTION_TO_MASTER_RETRY_INTERVAL: int = Field(alias='CONNECTION_TO_MASTER_RETRY_INTERVAL', ge=1)
    CONNECTION_TO_MASTER_RETRY_MECHANISM: RetryMechanism = Field(alias='CONNECTION_TO_MASTER_RETRY_MECHANISM',
                                                                 default='uniform')
    MAX_MESSAGE_POST_RETRY_DELAY: int = Field(alias='MAX_MESSAGE_POST_RETRY_DELAY', ge=1)
    MESSAGE_POST_RETRY_INTERVAL: int = Field(alias='MESSAGE_POST_RETRY_INTERVAL', ge=1)
    MESSAGE_POST_RETRIES_MECHANISM: RetryMechanism = Field(alias='MESSAGE_POST_RETRIES_MECHANISM',
                                                           default='exponential')
    CLIENT_TOKEN: str = Field(alias='API_TOKEN')
    SERVICE_TOKEN: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_signature()

    @model_validator(mode="after")
    def config_validator(self) -> 'Config':
        if self.SECONDARY_REMOVAL_DELAY < self.HEALTHCHECK_DELAY:
            raise ValueError('HEALTHCHECK_DELAY must be less or equal to SECONDARY_REMOVAL_DELAY')
        if self.CONNECTION_TO_MASTER_RETRY_INTERVAL > self.MAX_CONNECTION_TO_MASTER_DELAY:
            raise ValueError('CONNECTION_TO_MASTER_RETRY_INTERVAL must be less or equal to '
                             'MAX_CONNECTION_TO_MASTER_DELAY')
        if self.MAX_MESSAGE_POST_RETRY_DELAY > self.SECONDARY_REMOVAL_DELAY:
            raise ValueError('MAX_MESSAGE_POST_RETRY_DELAY must be less or equal to SECONDARY_REMOVAL_DELAY')
        if self.MESSAGE_POST_RETRY_INTERVAL > self.MAX_MESSAGE_POST_RETRY_DELAY:
            raise ValueError('MESSAGE_POST_RETRY_INTERVAL must be less or equal to MAX_MESSAGE_POST_RETRY_DELAY')

        return self

    def create_signature(self,
                         salt: str = '028ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ61702'):
        """
        create server-to-server api key
        """
        full_string = f'{self.CLIENT_TOKEN}&{salt}'

        self.SERVICE_TOKEN = hashlib.sha256(full_string.encode('utf-8')).hexdigest()
