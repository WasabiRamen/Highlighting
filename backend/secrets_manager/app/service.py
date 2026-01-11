# Usage: gRPC / FastAPI

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from . import crud
from .tools.kid import generate_kid
from .tools.dt import get_current_utc_datetime
from .core.crypto.asymmetric import generate_key as generate_asymmetric_key_pair
from .core.crypto.symmetric import generate_key as generate_symmetric_key, aes_encrypt_data, aes_decrypt_data

# Exceptions
class SecretNotFoundError(Exception):
    """시크릿 조회 결과 없음"""
    pass

class DecryptionError(Exception):
    """키 복호화 실패 - 보통 잘못된 마스터 키"""
    pass

# utils
def orm_to_dict(obj):
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


# Secret CRUD Operations
async def create_secrets_key(
    db: AsyncSession,
    key_name: str,
    value: str,
    mk: bytes,
    mk_version: int = 1,
    key_type: str = None,
) -> dict:
    """
        새로운 Secret 항목을 DB에 생성
        기존 Secret 항목이 존재할 경우, 비활성화 처리 (업데이트)

        gRPC에서 요구하는 Args
            - key_name
            - value
            - key_type (optional)
    """

    created_at = get_current_utc_datetime()
    new_kid = generate_kid(created_at=created_at)
    encrypted_value = aes_encrypt_data(key=mk, plaintext=value)

    result = await crud.create_secret(
        db=db,
        kid=new_kid,
        key_name=key_name,
        key_type=key_type,
        value=encrypted_value,
        created_at=created_at,
        mk_version=mk_version
        )

    logger.info(f"Created new secret with key_name: {key_name}, kid: {new_kid}")
    
    return orm_to_dict(result)


async def get_secret_by_name(
        db: AsyncSession, 
        key_name: str, 
        mk: bytes
        ) -> dict:
    """
       DB내에 Secret을 조회 후, 활성화 되어있는 항목 반환
    """
    secret = await crud.get_secret_by_key_name(db, key_name)

    if not secret:
        raise SecretNotFoundError(f"Secret with key_name '{key_name}' not found.")

    result = orm_to_dict(secret)

    try:
        result['value'] = aes_decrypt_data(key=mk, ciphertext=secret.value)
    except Exception as e:
        raise DecryptionError("Invalid master key") from e

    return result

# Asymmetric Key Pair CRUD Operations
async def create_asymmetric_key_pair(
    db: AsyncSession,
    key_size: int,
    key_name: str,
    mk: bytes,
    mk_version: int = 1,
    key_type: str = None
) -> dict:
    """
    Create a new asymmetric key pair entry in the database.

        gRPC에서 요구하는 Args
        - key_name
        - key_size
        - key_type (optional)
    """
    new_key_pair = generate_asymmetric_key_pair(key_size)
    encrypted_private_key = aes_encrypt_data(key=mk, plaintext=new_key_pair['private_key'])
    encrypted_public_key = aes_encrypt_data(key=mk, plaintext=new_key_pair['public_key'])
    new_kid = new_key_pair['kid']
    created_at = new_key_pair['created_at']

    result = await crud.create_asymmetric_key_pair(
        db=db,
        kid=new_kid,
        key_name=key_name,
        private_key=encrypted_private_key,
        public_key=encrypted_public_key,
        key_size=key_size,
        created_at=created_at,
        mk_version=mk_version,
        key_type=key_type
    )

    logger.info(f"Created new asymmetric key pair with kid: {new_kid}")
    return orm_to_dict(result)


async def get_asymmetric_key_pair_by_key_name(
        db: AsyncSession, 
        key_name: str, 
        mk: bytes,
        return_key_type: str = 'public'
        ) -> dict:
    """
       DB내에 Asymmetric Key 조회 후, 활성화 되어있는 항목 반환

       key_type: 'pair' | 'public'
    """
    asymmetric_key_pair = await crud.get_asymmetric_key_pair_by_key_name(db, key_name, return_key_type)

    if not asymmetric_key_pair:
        raise SecretNotFoundError(f"Asymmetric Key Pair with key_name '{key_name}' not found.")

    result = orm_to_dict(asymmetric_key_pair)

    try:
        result['public_key'] = aes_decrypt_data(key=mk, ciphertext=asymmetric_key_pair.public_key)
    except Exception as e:
        raise DecryptionError("Invalid master key") from e

    if return_key_type == 'pair':
        try:
            result['private_key'] = aes_decrypt_data(key=mk, ciphertext=asymmetric_key_pair.private_key)
        except Exception as e:
            raise DecryptionError("Invalid master key") from e

    return result


# Symmetric Key CRUD Operations

async def create_symmetric_key(
    db: AsyncSession,
    key_size: int,
    key_name: str,
    mk: bytes,
    mk_version: int = 1,
    key_type: str = None
) -> dict:
    """
    Create a new symmetric key entry in the database.
        gRPC에서 요구하는 Args
        - key_name
        - key_size
        - key_type (optional)
    """
    new_symmetric_key = generate_symmetric_key(key_size)
    encrypted_key = aes_encrypt_data(key=mk, plaintext=new_symmetric_key['key'])
    new_kid = new_symmetric_key['kid']
    created_at = new_symmetric_key['created_at']

    result = await crud.create_symmetric_key(
        db=db,
        kid=new_kid,
        key_name=key_name,
        key_type=key_type,
        key_value=encrypted_key,
        created_at=created_at,
        mk_version=mk_version,
        key_size=key_size,
    )

    logger.info(f"Created new symmetric key with kid: {new_kid}")
    return orm_to_dict(result)


async def get_symmetric_key_by_key_name(
        db: AsyncSession, 
        key_name: str, 
        mk: bytes) -> dict:
    """
       DB내에 Symmetric Key 조회 후, 활성화 되어있는 항목 반환
    """
    symmetric_key = await crud.get_symmetric_key_by_key_name(db, key_name)

    if not symmetric_key:
        raise SecretNotFoundError(f"Symmetric Key with key_name '{key_name}' not found.")
    
    result = orm_to_dict(symmetric_key)

    try:
        result['key_value'] = aes_decrypt_data(key=mk, ciphertext=symmetric_key.key_value)
    except Exception as e:
        raise DecryptionError("Invalid master key") from e

    return result