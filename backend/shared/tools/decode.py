# Third Party
import jwt
from pydantic import BaseModel, Field
from fastapi.requests import Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# Cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# gRPC Auth Service Client
from .grpc_auth_client import get_grpc_auth_client

from .exceptions import (
    InvalidAccessTokenError
)


# Payload 모델 정의
class AccessTokenPayload(BaseModel):
    sub: str = Field(..., description="사용자 UUID")
    iat: int = Field(..., description="발급 시간 (timestamp)")
    exp: int = Field(..., description="만료 시간 (timestamp)")


# -------- JWT 헤더 디코딩 --------

def decode_header(token: str) -> dict:
        """JWT 헤더 디코딩"""
        try:
            header = jwt.get_unverified_header(token)
            return header
        except Exception as e:
            raise InvalidAccessTokenError("토큰 헤더 디코딩에 실패하였습니다.") from e


def get_jwt_header_kid(token: str) -> str:
    """
    JWT 토큰 헤더에서 키 ID (kid) 추출
    """
    try:
        headers = decode_header(token)
        kid = headers.get("kid")
        if not kid:
            raise ValueError("키 ID(kid)가 토큰 헤더에 없습니다.")
        return kid
    except Exception as e:
        logger.error(f"Failed to decode JWT headers: {e}")
        raise

# -------- RSA Key Handling --------

def load_public_key_from_string(key_str: str) -> rsa.RSAPublicKey:
    """
    문자열에서 RSA 공개키 불러오기
    """
    key_bytes = key_str.encode("utf-8")
    public_key = serialization.load_pem_public_key(key_bytes)
    return public_key


# Secret Key 조회 함수
async def get_rsa_public_key(request: Request, db: AsyncSession, kid: str) -> rsa.RSAPublicKey:
    """
    RSA 공개키 조회 (gRPC 사용)
    """
    public_keys: dict = request.app.state.public_keys
    if kid not in public_keys.keys():
        grpc_client = get_grpc_auth_client()
        public_key = await grpc_client.get_public_key(kid)
        if not public_key:
            raise ValueError(f"키 ID '{kid}'에 해당하는 공개 키를 찾을 수 없습니다.")
        request.app.state.public_keys[kid] = load_public_key_from_string(public_key)
    return request.app.state.public_keys[kid]


# Decode 함수
async def decode_token(request: Request, db: AsyncSession, token: str, options: dict = None) -> dict:
    """
    JWT 디코딩. options에 verify_signature=False 가 명시되면 secret_key는 필수가 아님.
    """
    opts = options or {}
    verify_signature = opts.get("verify_signature", True)
    kid = get_jwt_header_kid(token)
    secret_key = await get_rsa_public_key(request, db, kid)

    if verify_signature and not secret_key:
        raise ValueError("비밀 키가 제공되지 않았습니다.")

    try:
        payload = jwt.decode(
            token,
            key=(secret_key if verify_signature else None),
            algorithms=["RS256"],
            options=opts
        )
        return payload

    except Exception as e:
        # PyJWT의 ExpiredSignatureError가 있으면 별도 처리
        ExpiredErr = getattr(jwt, "ExpiredSignatureError", None)
        if ExpiredErr and isinstance(e, ExpiredErr):
            raise ValueError("토큰이 만료되었습니다.") from e

        # 그 외 예외는 검증 실패로 래핑
        raise ValueError("토큰 검증에 실패하였습니다.") from e

async def decode_token_without_expiration(request: Request, db: AsyncSession, token: str) -> dict:
    """만료 검증 없이 JWT 토큰 디코딩 및 payload 반환"""
    option = {
        "verify_exp": False
    }
    return await decode_token(request, db, token, option)
    
async def decode_token_without_validation(request: Request, db: AsyncSession, token: str) -> dict:
    """검증 없이 JWT 토큰 디코딩 및 payload 반환"""
    options = {
        "verify_signature": False,
        "verify_exp": False
        }
    return await decode_token(request, db, token, options)