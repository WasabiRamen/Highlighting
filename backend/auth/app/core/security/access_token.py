# core/security/access_token.py
from datetime import datetime, timezone
import jwt
from pydantic import BaseModel, Field

from cryptography.hazmat.primitives.asymmetric import rsa

class AccessTokenService:
    """JWT 생성 및 검증 유틸리티

    - HS256 알고리즘 사용
    - 토큰 만료 시간 설정 가능

    @TODO: 알고리즘 선택 기능 구현

    사용 예시:
    jwt_manager = JWTManager(algorithm=algorithm, access_token_expire_minutes=expire_minutes)
    기본값:
        algorithm = "RS256"
        access_token_expire_minutes = 15

    알고리즘은, 초기 셋팅 때만 건들 수 있게 설계 필요.
    """
    def __init__(self, algorithm: str = "RS256", access_token_expire_minutes: int = 15):
        allow_algorithms = ["RS256"]
        if algorithm not in allow_algorithms:
            raise AccessTokenService.NotSupportedAlgorithmError(f"지원하지 않는 알고리즘입니다. 지원 알고리즘: {allow_algorithms}")

        self.__ALGORITHM: str = algorithm
        self.__ACCESS_TOKEN_EXPIRE_MINUTES: int = access_token_expire_minutes

    # 예외 정의
    class ExpiredTokenError(Exception):
        """토큰 만료 예외"""
        pass

    class InvalidTokenError(Exception):
        """토큰 검증 예외"""
        pass

    class NotSupportedAlgorithmError(Exception):
        """지원하지 않는 알고리즘 예외"""
        pass

    class SecretKeyNotFoundError(Exception):
        """비밀 키 미설정 예외"""
        pass

    # 내부 응답 스키마 정의
    class TokenResponse(BaseModel):
        token: str = Field(..., description="JWT 토큰")
        created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
        expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")

    # 내부 함수 정의
    @staticmethod
    def now() -> int:
        return round(datetime.now(timezone.utc).timestamp())

    # JWT 토큰 생성
    def issue_token(self, user_uuid: str, secret_key: rsa.RSAPrivateKey, kid: str) -> TokenResponse:
        """
        JWT 토큰 생성
        
        @TODO: payload에 추가 클레임 삽입 기능 구현 
        1. permissions: 사용자 권한
        2. iss: 발급자
        """
        if not secret_key:
            raise AccessTokenService.SecretKeyNotFoundError("비밀 키가 제공되지 않았습니다.")

        sub = str(user_uuid)
        iat = self.now()  # 발급 시간
        exp = iat + self.__ACCESS_TOKEN_EXPIRE_MINUTES * 60 # 만료 시간

        header = {
            "alg": self.__ALGORITHM,
            "typ": "JWT",
            "kid": kid
        }

        payload = {
            "sub": sub,
            "iat": iat,
            "exp": exp
        }

        encoded_jwt = jwt.encode(
            payload, 
            secret_key, 
            algorithm=self.__ALGORITHM, 
            headers=header
            )
        if isinstance(encoded_jwt, bytes):
            encoded_jwt = encoded_jwt.decode("utf-8")
        return AccessTokenService.TokenResponse(
            token=encoded_jwt,
            created_at=iat,
            expires_at=exp
        )

    # Decode 함수는 shared/tools/token/decode.py 로 이동