# shared/tools/token/exceptions.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Token Exceptions
# ---------------- Exception 정의 ----------------
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
    InvalidAccessTokenError: ("TOKEN_INVALID_ACCESS", 401),
    InvalidRefreshTokenError: ("TOKEN_INVALID_REFRESH", 401),
    ExpiredRefreshTokenError: ("TOKEN_EXPIRED_REFRESH", 401),
    RefreshSessionMismatchError: ("TOKEN_REFRESH_SESSION_MISMATCH", 401),
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

# Token Rotation Exceptions
# ---------------- 예외 정의 ----------------
class RefreshTokenReusedError(Exception):
    """이미 사용된 Refresh Token 재사용 시도 (Replay 공격)"""
    pass

class RefreshSessionMismatchError(Exception):
    """클라이언트 session_id와 Redis session_id 불일치 (탈취 의심)"""
    pass

class RefreshTokenRevokedError(Exception):
    """강제로 폐기된 Refresh Token 사용"""
    pass

class ExpiredRefreshTokenError(Exception):
    """Refresh Token 만료 (Rotation 불가)"""
    pass

class InvalidRefreshTokenError(Exception):
    """Refresh Token 변조/서명 오류/포맷 오류"""
    pass

class RefreshTokenNotFoundError(Exception):
    """DB에 Refresh Token 기록 없음 (발급된 적 없음)"""
    pass

# ---------------- exception_map ----------------
rotation_exception_map = {
    RefreshTokenReusedError: ("TOKEN_REFRESH_REUSED", 401),
    RefreshSessionMismatchError: ("TOKEN_REFRESH_SESSION_MISMATCH", 401),
    RefreshTokenRevokedError: ("TOKEN_REFRESH_REVOKED", 401),
    ExpiredRefreshTokenError: ("TOKEN_EXPIRED_REFRESH", 401),
    InvalidRefreshTokenError: ("TOKEN_INVALID_REFRESH", 401),
    RefreshTokenNotFoundError: ("TOKEN_REFRESH_NOT_FOUND", 404),
}

# ---------------- register 함수 ----------------
def register_rotation_exception_handlers(app: FastAPI):
    """
    FastAPI 앱에 Refresh Token 관련 예외 핸들러 등록
    """
    for exc_class, (code, status) in rotation_exception_map.items():
        @app.exception_handler(exc_class)
        async def handler(request, exc, code=code, status=status):
            return JSONResponse(
                status_code=status,
                content={"detail": code}
            )