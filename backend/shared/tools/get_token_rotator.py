import jwt
from pydantic import BaseModel, Field
from fastapi import Depends
from fastapi.requests import Request
from fastapi.responses import Response
import redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.settings import get_cookie_settings
from ..core.cookie_handler import AuthCookieHandler
from ..core.database import get_db
from ..core.redis import get_redis
from .decode import decode_token, AccessTokenPayload

# Auth Service gRPC Client
from .grpc_auth_client import get_grpc_auth_client, IssueTokenResponse

cookie_settings = get_cookie_settings()
auth_cookie_handler = AuthCookieHandler(
    secure=cookie_settings.SECURE,
    path=cookie_settings.PATH,
    samesite=cookie_settings.SAMESITE,
)

async def get_token_rotator(
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db),
        redis: redis.Redis = Depends(get_redis)
        ) -> AccessTokenPayload:
    """
    scenario 01. 액세스 토큰이 유효한 상황
        -> 액세스 토큰의 payload 반환
    scenario 02. 액세스 토큰이 만료 / 삭제된 상황
        -> 리프래시 토큰으로 토큰 재발급 수행 후, 새로운 액세스 토큰의 payload 반환
    scenario 03. 리프래시 토큰이 유효하지 않거나, 삭제된 상황
        -> 예외 발생 (토큰 재발급 불가)
        -> Front-End에서는 
            1. 예기치 않은 오류로 인하여, 로그아웃 되었습니다 처리
            2. 로그인 유효기간이 만료되어, 로그아웃 되었습니다 처리

    추가 예외:
        기존 엑세스 토큰의 Secret Key가 변경되어 검증에 실패하는 경우 
            -> 토큰 재발급 처리
    """

    access_token = request.cookies.get("access_token")
    
    # scenario 01: 액세스 토큰이 존재하고 유효한 경우
    if access_token:
        try:
            decoded_token = await decode_token(request, db,access_token)
            token_payload: AccessTokenPayload = AccessTokenPayload(**decoded_token)
            return token_payload
        except jwt.ExpiredSignatureError:
            # scenario 02: 액세스 토큰이 만료된 경우 -> 토큰 재발급
            pass
        except jwt.InvalidTokenError:
            # 추가 예외: Secret Key 변경 등으로 검증 실패 -> 토큰 재발급
            pass
        except Exception:
            # 기타 예외 (토큰 형식 오류 등) -> 토큰 재발급 시도
            pass
        except ValueError:
            pass
    
    # scenario 02: 액세스 토큰이 없거나 만료/무효화된 경우 -> 리프래시 토큰으로 재발급
    # scenario 03: 리프래시 토퀴이 유효하지 않으면 rotate_tokens에서 예외 발생
    grpc_client = get_grpc_auth_client()
    new_tokens: IssueTokenResponse = await grpc_client.rotate_tokens(request, db, redis)
    auth_cookie_handler.set_token_cookies(
        response=response,
        access_token=new_tokens.access_token,
        refresh_token=new_tokens.refresh_token
    )
    
    # rotate_tokens에서 생성한 토큰을 직접 디코딩하지 않고 payload 추출
    decoded_token = jwt.decode(
        new_tokens.access_token.token,
        options={"verify_signature": False}  # 이미 생성한 토큰이므로 검증 불필요
    )
    token_payload: AccessTokenPayload = AccessTokenPayload(**decoded_token)
    
    return token_payload