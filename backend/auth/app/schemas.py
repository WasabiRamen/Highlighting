from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class ResponseCode(Enum):
    AUTH_TOKEN_ISSUED = "AUTH_TOKEN_ISSUED"
    AUTH_TOKEN_REVOKED = "AUTH_TOKEN_REVOKED"
    EMAIL_TOKEN_ISSUED = "EMAIL_TOKEN_ISSUED"
    EMAIL_VERIFIED = "EMAIL_VERIFIED"


class SendEmailRequest(BaseModel):
    """이메일 인증 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")

class VerifyEmailRequest(BaseModel):
    """이메일 인증 코드 검증 요청 스키마"""
    code: str = Field(..., description="이메일 인증 코드")


class GoogleLoginRequest(BaseModel):
    """구글 로그인 요청 스키마"""
    code: str = Field(..., description="구글 OAuth2 인증 코드")


# ----------------------------------------------------------------

# 내부 로직에서 사용하는 응답 스키마 정의
class AccessTokenResponse(BaseModel):
    token : str = Field(..., description="JWT 액세스 토큰")
    expires_in : int = Field(..., description="토큰 만료까지 남은 시간(초)")
    expires_at : int = Field(..., description="토큰 만료 시간(Unix timestamp)")


class RefreshTokenResponse(BaseModel):
    token: str = Field(..., description="리프래시 토큰")
    created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
    expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")
    expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
    user_uuid: str = Field(..., description="토큰 소유자 UUID (DB 저장용)")


class EmailVerifyResponse(BaseModel):
    email: EmailStr = Field(..., description="이메일 주소")
    token: str = Field(..., description="이메일 인증 토큰")
    code: str = Field(..., description="이메일 인증 코드")
    expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
    created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
    expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")


# -------------------------------- Json Token Response --------------------------------

class AuthTokenIssueResponse(BaseModel):
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = "bearer"
    detail: str = "토큰이 발급되었습니다."
    code: str = ResponseCode.AUTH_TOKEN_ISSUED.value


class AuthTokenRevokeResponse(BaseModel):
    detail: str = "토큰이 무효화되었습니다."
    code: str = ResponseCode.AUTH_TOKEN_REVOKED.value



# -------------------------------- Email Verify Login Response --------------------------------

class EmailTokenIssueResponse(BaseModel):
    email: EmailStr = Field(..., description="이메일 주소")
    detail: str = "이메일이 발송되었습니다."
    code: str = ResponseCode.EMAIL_TOKEN_ISSUED.value


class EmailVerifySuccessResponse(BaseModel):
    email: EmailStr = Field(..., description="이메일 주소")
    detail: str = "이메일 인증이 완료되었습니다."
    code: str = ResponseCode.EMAIL_VERIFIED.value