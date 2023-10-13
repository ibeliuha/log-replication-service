import functools
import hashlib
import random
import string


def encrypt(msg: str) -> str:
    pass


def decrypt(msg: str) -> str:
    pass


def log_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(F"{func.__name__}")
        return func(*args, **kwargs)

    return wrapper


def create_signature(key: str, salt: str = '028ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ61702'):
    # salt = ''.join([str(random.choice(string.ascii_uppercase.split()+list(range(10)))) for _ in range(10)])
    full_string = f'{key}&{salt}'

    return hashlib.sha256(full_string.encode('utf-8')).hexdigest()
