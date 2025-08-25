import hashlib

from cryptography.fernet import Fernet

from src.core.config import AppConfig
from src.core.utils import mjson

config = AppConfig.get()
_cipher_suite = Fernet(config.crypt_key.get_secret_value().encode())


def encrypt(data: str) -> str:
    return _cipher_suite.encrypt(data.encode()).decode()


def decrypt(data: str) -> str:
    return _cipher_suite.decrypt(data.encode()).decode()


def get_webhook_hash(webhook_data: dict) -> str:
    return hashlib.sha256(mjson.bytes_encode(webhook_data)).hexdigest()
