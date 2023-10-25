import hashlib
import logging
# import global_entities as ge
from config import CONFIG
from config.config import RetryMechanism
import enum
import asyncio
import random
import os


def get_retry_properties(func: str) -> dict:
    kwargs = {
        "default": {
            "max_delay": 300,
            "interval": 10,
            "mechanism": RetryMechanism.UNIFORM
        },
        "_publish_to_secondary": {
            "max_delay": CONFIG.MAX_MESSAGE_POST_RETRY_DELAY,
            "interval": CONFIG.MESSAGE_POST_RETRY_INTERVAL,
            "mechanism": CONFIG.MESSAGE_POST_RETRIES_MECHANISM
        },
        "_register_to_master": {
            "max_delay": CONFIG.MAX_CONNECTION_TO_MASTER_DELAY,
            "interval": CONFIG.CONNECTION_TO_MASTER_RETRY_INTERVAL,
            "mechanism": CONFIG.CONNECTION_TO_MASTER_RETRY_MECHANISM
        }
    }
    return kwargs.get(func, kwargs["default"])


def next_retry_in(mechanism: RetryMechanism, **kwargs):
    def _exponential_retry(max_delay: float, interval: int):
        current_delay = 0
        total_delay = 0
        while total_delay < max_delay:
            current_delay = int(min(max(current_delay, interval) ** (5 / 4), (max_delay - total_delay) + 1))
            total_delay += current_delay
            yield current_delay

    def _uniform_retry(max_delay: float, interval: int):
        total_delay = 0
        while total_delay < max_delay:
            total_delay += interval
            yield interval

    return {
        RetryMechanism.UNIFORM: _uniform_retry,
        RetryMechanism.EXPONENTIAL: _exponential_retry
    }[mechanism](**kwargs)


async def delay(a, b):
    sleep_time = random.randint(a, b)
    logging.getLogger('default').info(f'Sleep for {sleep_time}')
    await asyncio.sleep(sleep_time)
