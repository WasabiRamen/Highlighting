# core/security/refresh_token.py
import secrets
import hashlib
from datetime import datetime, timezone
from pydantic import BaseModel, Field

def create_session_id() -> str:
    """세션 토큰 생성 (CSPRNG 기반 16바이트 랜덤 문자열)"""
    return secrets.token_urlsafe(16)

class RefreshTokenService:
    """
    리프래시 토큰 관리 유틸리티

    토큰 형식 -> CSPRNG 기반 32바이트 랜덤 문자열

    사용법:
        refresh_token_service = RefreshTokenService(byte_length=32, store_hashed=True, expire_days=30)
    기본값:
        byte_length: 리프래시 토큰 바이트 길이 (기본값: 32)
        store_hashed: 토큰 저장 시 해싱 여부 (기본값: True)
        expire_days: 토큰 만료 기간 (기본값: 30일)
    """
    def __init__(self, byte_length: int = 32, store_hashed: bool = True, expire_days: int = 30):
        self.__REFRESH_TOKEN_BYTE_LENGTH = byte_length
        self.__REFRESH_TOKEN_STORE_HASHED = store_hashed
        self.__REFRESH_TOKEN_EXPIRE_DAYS = expire_days
    
    class TokenResponse(BaseModel):
        token: str = Field(..., description="리프래시 토큰")
        created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
        expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")
        expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
        user_uuid: str = Field(..., description="토큰 소유자 UUID (DB 저장용)")
        session_id: str = Field(default_factory=create_session_id, description="세션 식별자")

    def get_expiration_datetime(self) -> tuple[int, int, int]:
        create_at = round(datetime.now(timezone.utc).timestamp())
        expires_in = self.__REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        expires_at = create_at + expires_in
        return create_at, expires_at, expires_in

    def create_token(self, user_uuid: str) -> TokenResponse:
        """CSPRNG 기반 리프래시 토큰 생성"""
        create_at, expires_at, expires_in = self.get_expiration_datetime()
        token = secrets.token_urlsafe(self.__REFRESH_TOKEN_BYTE_LENGTH)
        if self.__REFRESH_TOKEN_STORE_HASHED:
            token = hashlib.sha256(token.encode('utf-8')).hexdigest()
        return RefreshTokenService.TokenResponse(
            token=token,
            created_at=create_at,
            expires_in=expires_in,
            expires_at=expires_at,
            user_uuid=user_uuid,
            session_id=create_session_id()
        )

    def verify_token(self, token: str, stored_token: str) -> bool:
        """리프래시 토큰 검증"""
        if self.__REFRESH_TOKEN_STORE_HASHED:
            hash_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
            return hash_token == stored_token
        return token == stored_token
