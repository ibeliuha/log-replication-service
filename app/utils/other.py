import functools
import hashlib
import random
import string
from services.config import RetryMechanism


def create_signature(key: str, salt: str = '028ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ61702'):
    # salt = ''.join([str(random.choice(string.ascii_uppercase.split()+list(range(10)))) for _ in range(10)])
    full_string = f'{key}&{salt}'

    return hashlib.sha256(full_string.encode('utf-8')).hexdigest()


def next_retry_in(
        max_delay: int,
        previous_delay: float,
        step: int,
        mechanism: RetryMechanism) -> int:
    if mechanism == RetryMechanism.UNIFORM:
        return int(previous_delay/step)
    if mechanism == RetryMechanism.EXPONENTIAL:
        return int(max(previous_delay**(5/4), max_delay-previous_delay))