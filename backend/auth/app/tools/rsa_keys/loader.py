from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import aiofiles

async def load_private_key(file_path: str) -> rsa.RSAPrivateKey:
    """
    PEM 파일에서 RSA 개인키 불러오기 (비동기)
    """
    async with aiofiles.open(file_path, "rb") as f:
        key_bytes = await f.read()

    private_key = serialization.load_pem_private_key(
        key_bytes,
        password=None,
    )
    return private_key


async def load_public_key(file_path: str) -> str:
    """
    PEM 파일에서 RSA 공개키 불러오기 (비동기)
    """
    async with aiofiles.open(file_path, "rb") as f:
        key_bytes = await f.read()

    return key_bytes.decode('utf-8')