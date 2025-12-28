# service/auth/app/exceptions.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Token Exceptions
# ---------------- Exception 정의 ----------------
class UserNotFoundError(Exception):
    """사용자 없음 예외"""
    pass

class InvalidAccessTokenError(Exception):
    """액세스 토큰이 변조되었거나 유효하지 않음"""
    pass

class InvalidRefreshTokenError(Exception):
    """리프레시 토큰 변조 또는 형식 오류"""
    pass

class ExpiredRefreshTokenError(Exception):
    """리프레시 토큰 만료 (완전 재로그인 필요)"""
    pass

class RefreshSessionMismatchError(Exception):
    """session_id가 Redis와 불일치 (탈취/재사용 의심)"""
    pass

class RefreshSessionNotFoundError(Exception):
    """session_id가 쿠키에 없거나 Redis에 없음"""
    pass

class RefreshTokenNotFoundError(Exception):
    """DB/Redis에서 토큰 기록 없음 (존재하지 않는 토큰)"""
    pass

class RefreshTokenReusedError(Exception):
    """이미 사용된 리프레시 토큰 재사용 시도"""
    pass

class RefreshTokenRevokedError(Exception):
    """폐기(로그아웃 등)된 리프레시 토큰 사용"""
    pass

class RefreshTokenRequiredError(Exception):
    """갱신 요청인데 Refresh Token 없음"""
    pass

# ---------------- Exception Handler 등록 ----------------
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


# Email Verification Exceptions
# ---------------- Exception 정의 ----------------
class EmailVerificationTokenExpiredError(Exception):
    """이메일 인증 토큰이 만료됨"""
    pass

class EmailVerificationInvalidTokenError(Exception):
    """이메일 인증 토큰이 유효하지 않음"""
    pass

class EmailVerificationCodeMismatchError(Exception):
    """이메일 인증 코드 불일치"""
    pass

class EmailVerificationNotFoundError(Exception):
    """이메일 인증 기록이 없음"""
    pass

class EmailAlreadyVerifiedError(Exception):
    """이미 인증된 이메일 주소"""
    pass

# ---------------- Exception Handler 등록 ----------------
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
        
# OAuth Exceptions
# ---------------- Exception 정의 ----------------
class InvalidGoogleTokenException(Exception):
    """구글 인증 토큰이 유효하지 않음"""
    pass
class ProviderAccountAlreadyLinkedException(Exception):
    """OAuth 제공자 계정이 이미 연결되어 있음"""
    pass
# ---------------- Exception Handler 등록 ----------------
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