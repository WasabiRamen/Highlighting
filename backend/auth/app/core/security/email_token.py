# core/security/email_token.py
import secrets
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class EmailTokenManager:
    """
    이메일 인증 토큰 관리 유틸리티

    토큰 형식 -> CSPRNG 기반 16바이트 랜덤 문자열
    """
    def __init__(self, token_byte_length: int = 16, expire_minutes: int = 10):
        self.__EMAIL_TOKEN_BYTE_LENGTH = token_byte_length
        self.__EMAIL_TOKEN_EXPIRE_MINUTES = expire_minutes


    class EmailVerifyResponse(BaseModel):
        email: str = Field(..., description="이메일 주소")
        token: str = Field(..., description="이메일 인증 토큰")
        code: str = Field(..., description="이메일 인증 코드")
        expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
        created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
        expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")


    def get_expiration_datetime(self) -> tuple[int, int, int]:
        create_at = round(datetime.now(timezone.utc).timestamp())
        expires_in = self.__EMAIL_TOKEN_EXPIRE_MINUTES * 60
        expires_at = create_at + expires_in
        return create_at, expires_at, expires_in

    def create_token(self, email: str) -> EmailVerifyResponse:
        """CSPRNG 기반 이메일 인증 토큰 생성"""
        create_at, expires_at, expires_in = self.get_expiration_datetime()
        token = secrets.token_urlsafe(self.__EMAIL_TOKEN_BYTE_LENGTH)
        code = f"{secrets.randbelow(1000000):06d}"
        return EmailTokenManager.EmailVerifyResponse(
            email=email,
            token=token,
            code=code,
            expires_at=expires_at,
            created_at=create_at,
            expires_in=expires_in
        )