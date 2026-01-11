# coding: utf-8
# crypto_toolkit/key_management/asymmetric.py

# Standard Library
from datetime import datetime, timedelta, timezone

# Third Party
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Utility
from ...tools.kid import generate_kid


def generate_key(key_size: int) -> dict:
    """
    비대칭 키 쌍 생성 (RSA)
    """
    # RSA 키 쌍 생성
    private_key_obj = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    public_key_obj = private_key_obj.public_key()

    # PEM 형식으로 직렬화
    private_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key_obj.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    now = datetime.now(timezone.utc)
    kid = generate_kid(now)

    return {
        "kid": kid,
        "private_key": private_pem,
        "public_key": public_pem,
        "key_size": key_size,
        "created_at": now,
    }

