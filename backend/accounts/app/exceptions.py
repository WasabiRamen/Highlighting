from fastapi import FastAPI
from fastapi.responses import JSONResponse


# ---------------- Exception 정의 ----------------
class EmailTokenNotValidException(Exception):
    """이메일 인증 토큰이 유효하지 않음"""
    pass

class UserAlreadyExistsException(Exception):
    """이미 존재하는 사용자"""
    pass

class AccountNotFoundException(Exception):
    """계정이 존재하지 않음"""
    pass

class IncorrectPasswordException(Exception):
    """잘못된 비밀번호"""
    pass

class InvalidGoogleTokenException(Exception):
    """구글 인증 토큰이 유효하지 않음"""
    pass


# ---------------- Exception Handler 등록 ----------------
accounts_exception_map = {
    EmailTokenNotValidException: ("EMAIL_TOKEN_NOT_VALID", 400),
    UserAlreadyExistsException: ("USER_ALREADY_EXISTS", 400),
    AccountNotFoundException: ("ACCOUNT_NOT_FOUND", 404),
    IncorrectPasswordException: ("INCORRECT_PASSWORD", 400),
    InvalidGoogleTokenException: ("GOOGLE_CODE_NOT_VALID", 400),
}

def register_accounts_exception_handlers(app: FastAPI):
    """
    FastAPI 앱에 accounts 관련 예외 핸들러 등록
    """
    for exc_class, (code, status) in accounts_exception_map.items():
        @app.exception_handler(exc_class)
        async def handler(request, exc, code=code, status=status):
            return JSONResponse(
                status_code=status,
                content={"detail": code}
            )