import hashlib
import logging

import global_entities as ge
import enum


def create_signature(key: str, salt: str = '028ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ61702'):
    # salt = ''.join([str(random.choice(string.ascii_uppercase.split()+list(range(10)))) for _ in range(10)])
    full_string = f'{key}&{salt}'

    return hashlib.sha256(full_string.encode('utf-8')).hexdigest()


class RetryMechanism(enum.Enum):
    UNIFORM = 'uniform'
    EXPONENTIAL = 'exponential'


def get_retry_properties(func: str) -> dict:
    kwargs = {
        "default": {
            "max_delay": 300,
            "interval": 10,
            "mechanism": RetryMechanism.UNIFORM
        },
        "_publish_to_secondary": {
            "max_delay": ge.CONFIG.MAX_MESSAGE_POST_RETRY_DELAY,
            "interval": ge.CONFIG.MESSAGE_POST_RETRY_INTERVAL,
            "mechanism": ge.CONFIG.MESSAGE_POST_RETRIES_MECHANISM
        },
        "_register_to_master": {
            "max_delay": ge.CONFIG.MAX_CONNECTION_TO_MASTER_DELAY,
            "interval": ge.CONFIG.CONNECTION_TO_MASTER_RETRY_INTERVAL,
            "mechanism": ge.CONFIG.CONNECTION_TO_MASTER_RETRY_MECHANISM
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