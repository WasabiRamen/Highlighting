# coding: utf-8
# crypto_toolkit/key_management/symmetric.py

# Standard Library
import os
from datetime import datetime, timedelta, timezone

# Third Party
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Utility
from ...tools.kid import generate_kid


def generate_key(key_size: int) -> dict:
    """
    대칭 키 생성
    """
    key = os.urandom(key_size)
    now = datetime.now(timezone.utc)
    kid = generate_kid(now)

    return {
        "kid": kid,
        "key": key,
        "created_at": now,
    }


def aes_encrypt_data(key: bytes, plaintext: bytes) -> bytes:
    """
    AES 대칭 키로 데이터 암호화
    """

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = iv + encryptor.update(plaintext) + encryptor.finalize()
    return ciphertext


def aes_decrypt_data(key: bytes, ciphertext: bytes) -> bytes:
    """
    AES 대칭 키로 데이터 복호화
    """

    iv = ciphertext[:16]
    actual_ciphertext = ciphertext[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
    return plaintext