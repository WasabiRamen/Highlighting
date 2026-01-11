# service/auth/app/exceptions.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .exceptions import (
    UserNotFoundError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
    ExpiredRefreshTokenError,
    RefreshSessionMismatchError,
    RefreshSessionNotFoundError,
    RefreshTokenNotFoundError,
    RefreshTokenReusedError,
    RefreshTokenRevokedError,
    RefreshTokenRequiredError,
    EmailVerificationTokenExpiredError,
    EmailVerificationInvalidTokenError,
    EmailVerificationCodeMismatchError,
    EmailVerificationNotFoundError,
    EmailAlreadyVerifiedError,
    InvalidGoogleTokenException,
    ProviderAccountAlreadyLinkedException,
)


# Token Exceptions Handlers


token_exception_map = {
    UserNotFoundError: ("USER_NOT_FOUND", 404),
    InvalidAccessTokenError: ("TOKEN_INVALID_ACCESS", 401),
    InvalidRefreshTokenError: ("TOKEN_INVALID_REFRESH", 401),
    ExpiredRefreshTokenError: ("TOKEN_EXPIRED_REFRESH", 401),
    RefreshSessionMismatchError: ("TOKEN_REFRESH_SESSION_MISMATCH", 401),
    RefreshSessionNotFoundError: ("TOKEN_REFRESH_SESSION_NOT_FOUND", 401),
    RefreshTokenNotFoundError: ("TOKEN_REFRESH_NOT_FOUND", 404),
    RefreshTokenReusedError: ("TOKEN_REFRESH_REUSED", 401),
    RefreshTokenRevokedError: ("TOKEN_REFRESH_REVOKED", 401),
    RefreshTokenRequiredError: ("TOKEN_REFRESH_REQUIRED", 400),
}

def register_token_exception_handlers(app: FastAPI):
    """
    FastAPI 앱에 토큰 관련 예외 핸들러 등록
    """
    for exc_class, (code, status) in token_exception_map.items():
        @app.exception_handler(exc_class)
        async def handler(request, exc, code=code, status=status):
            return JSONResponse(
                status_code=status,
                content={"detail": code}
            )


# Email Verification Exceptions Handlers


email_verification_exception_map = {
    EmailVerificationTokenExpiredError: ("EMAIL_VERIFICATION_TOKEN_EXPIRED", 401),
    EmailVerificationInvalidTokenError: ("EMAIL_VERIFICATION_TOKEN_INVALID", 400),
    EmailVerificationCodeMismatchError: ("EMAIL_VERIFICATION_CODE_MISMATCH", 400),
    EmailVerificationNotFoundError: ("EMAIL_VERIFICATION_NOT_FOUND", 404),
    EmailAlreadyVerifiedError: ("EMAIL_ALREADY_VERIFIED", 400),
}

def register_email_verification_exception_handlers(app: FastAPI):
    """
    FastAPI 앱에 토큰 관련 예외 핸들러 등록
    """
    for exc_class, (code, status) in email_verification_exception_map.items():
        @app.exception_handler(exc_class)
        async def handler(request, exc, code=code, status=status):
            return JSONResponse(
                status_code=status,
                content={"detail": code}
            )


# OAuth Exceptions Handlers


oauth_exception_map = {
    InvalidGoogleTokenException: ("OAUTH_INVALID_GOOGLE_TOKEN", 400),
    ProviderAccountAlreadyLinkedException: ("OAUTH_PROVIDER_ACCOUNT_ALREADY_LINKED", 400),
} 
def register_oauth_exception_handlers(app: FastAPI):
    """
    FastAPI 앱에 OAuth 관련 예외 핸들러 등록
    """
    for exc_class, (code, status) in oauth_exception_map.items():
        @app.exception_handler(exc_class)
        async def handler(request, exc, code=code, status=status):
            return JSONResponse(
                status_code=status,
                content={"detail": code}
            )