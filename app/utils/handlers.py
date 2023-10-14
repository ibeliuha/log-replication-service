import functools
import global_entities
from models.models import ServiceType
import logging


async def async_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        _ = kwargs.pop('api_key')
        message_dict = {
            'function': func.__name__,
            'status': 'called'
        }
        try:
            message_dict.update(kwargs)
            message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
            logging.info(message)
            res = await func(*args, **kwargs)
            return res
        except Exception as e:
            message_dict.update({
                'status': 'failed',
                'error': e
            })
            message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
            logging.error(message)

    return wrapper


def sync_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        _ = kwargs.pop('api_key')
        message_dict = {
            'function': func.__name__,
            'status': 'called'
        }
        try:
            message_dict.update(kwargs)
            message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
            logging.info(message)
            res = func(*args, **kwargs)
            return res
        except Exception as e:
            message_dict.update({
                'status': 'failed',
                'error': e
            })
            message = ';'.join([f"{key}={value}" for key, value in message_dict.items()])
            logging.error(message)

    return wrapper