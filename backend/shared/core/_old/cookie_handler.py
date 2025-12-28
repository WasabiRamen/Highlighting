from fastapi import Response
from enum import Enum

class AuthCookieHandler:
    class TokenType(Enum):
        ACCESS = "access_token"
        REFRESH = "refresh_token"
        SESSION = "session_id"

    def __init__(self, secure: bool, path: str, samesite: str):
        self.secure = secure
        self.path = path
        self.samesite = samesite

    def set_token_cookies(
        self,
        response: Response,
        access_token,
        refresh_token,
        ) -> Response:
        
        response.set_cookie(
            key=self.TokenType.ACCESS.value,
            value=access_token.token,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=access_token.expires_at - access_token.created_at,
            path=self.path
        )

        response.set_cookie(
            key=self.TokenType.REFRESH.value,
            value=refresh_token.token,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=refresh_token.expires_in,
            path=self.path
        )

        response.set_cookie(
            key=self.TokenType.SESSION.value,
            value=refresh_token.session_id,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=refresh_token.expires_in,
            path=self.path
        )
        return response
    
    def get_token_cookies(self, request) -> tuple[str | None, str | None]:
        access_token = request.cookies.get(self.TokenType.ACCESS.value)
        refresh_token = request.cookies.get(self.TokenType.REFRESH.value)
        session_id = request.cookies.get(self.TokenType.SESSION.value)
        return access_token, refresh_token, session_id

    def delete_token_cookies(self, response: Response) -> Response:
        """토큰 쿠키 삭제"""
        response.delete_cookie(self.TokenType.ACCESS.value, path=self.path)
        response.delete_cookie(self.TokenType.REFRESH.value, path=self.path)
        response.delete_cookie(self.TokenType.SESSION.value, path=self.path)
        return response
    
    
class EmailVerifyCookieHandler:
    __email_verify_cookie_key = "evt"

    def __init__(self, secure: bool, path: str, samesite: str):
        self.secure = secure
        self.path = path
        self.samesite = samesite

    def set_email_verify_cookie(
        self,
        response: Response,
        verify_token,
        expires_in: int,
        ) -> Response:
        
        response.set_cookie(
            key=self.__email_verify_cookie_key,
            value=verify_token,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=expires_in,
            path=self.path
        )
        return response
    
    def get_email_verify_cookie(self, request) -> str | None:
        verify_token = request.cookies.get(self.__email_verify_cookie_key)
        return verify_token

    def delete_email_verify_cookie(self, response: Response) -> Response:
        response.delete_cookie(self.__email_verify_cookie_key, path=self.path)
        return response