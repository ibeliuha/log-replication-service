import functools
import logging
from typing import Optional
import time
import asyncio
import enum
from utils.other import next_retry_in

LOGGER = logging.getLogger("default")


def async_handler(func, retries=1):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if 'api_key' in kwargs:
            _ = kwargs.pop('api_key')
        message_dict = {
            'function': func.__name__,
            'status': 'called'
        }
        exception: Optional[Exception] = None
        for retry_number in range(1, kwargs.get('retries', retries)+1):
            try:
                message_dict.update(kwargs)
                message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
                LOGGER.info(message)
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                exception = e
                await asyncio.sleep(next_retry_in(retry_number, ))
                continue
        message_dict.update({
            'status': 'failed',
            'error': exception
        })
        message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
        LOGGER.error(message)

    return wrapper


def sync_handler(func, retries=1):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'api_key' in kwargs:
            _ = kwargs.pop('api_key')
        message_dict = {
            'function': func.__name__,
            'status': 'called'
        }
        exception: Optional[Exception] = None
        for x in range(kwargs.get('retries', retries)):

            try:
                message_dict.update(kwargs)
                message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
                LOGGER.info(message)
                res = func(*args, **kwargs)
                return res
            except Exception as e:
                exception = e
                time.sleep(10)
                continue
        message_dict.update({
            'status': 'failed',
            'error': exception
        })
        message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
        LOGGER.error(message)

    return wrapper
