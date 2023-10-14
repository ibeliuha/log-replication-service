import functools
import logging
from typing import Optional
import time
import asyncio
from utils.other import next_retry_in, get_retry_properties

LOGGER = logging.getLogger("default")


def async_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if 'api_key' in kwargs:
            _ = kwargs.pop('api_key')
        message_dict = {
            'function': func.__name__,
            'status': 'called'
        }
        exception: Optional[Exception] = None
        for interval in next_retry_in(**get_retry_properties(func.__name__)):
            try:
                message_dict.update(kwargs)
                LOGGER.info(';'.join([f"{key}={value}" for key, value in message_dict.items()]))
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                exception = e
                message_dict.update({'status': 'failed', 'next_retry_in(sec)': f'{interval}', 'error': exception})
                LOGGER.info(';'.join([f"{key}={value}" for key, value in message_dict.items()]))
                await asyncio.sleep(interval)
                continue
        message_dict.update({
            'status': 'error',
            'error': exception
        })
        message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
        LOGGER.error(message)

    return wrapper


def sync_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'api_key' in kwargs:
            _ = kwargs.pop('api_key')
        message_dict = {
            'function': func.__name__,
            'status': 'called'
        }
        exception: Optional[Exception] = None
        for interval in next_retry_in(**get_retry_properties(func.__name__)):
            try:
                message_dict.update(kwargs)
                message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
                LOGGER.info(message)
                res = func(*args, **kwargs)
                return res
            except Exception as e:
                exception = e
                message_dict.update({'status': 'failed', 'next_retry_in(sec)': f'{interval}', 'error': exception})
                LOGGER.info(';'.join([f"{key}={value}" for key, value in message_dict.items()]))
                time.sleep(interval)
                continue
        message_dict.update({
            'status': 'failed',
            'error': exception
        })
        message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
        LOGGER.error(message)

    return wrapper
