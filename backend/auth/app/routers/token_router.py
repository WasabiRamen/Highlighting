# auth/routers/email_verify_router.py
# FastAPI imports
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

# SQLAlchemy & Third Party imports
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from loguru import logger
from time import time

# App imports
from .. import service, schemas

# Shared imports
from ....shared.core.database import get_db
from ....shared.core.redis import get_redis
from ....shared.core.cookie_handler import AuthCookieHandler
from ..core.settings import get_cookie_settings

# ------------------------- Settings Initialization -------------------------

CookieSettings = get_cookie_settings()

# ------------------------- Functional Logic -------------------------

auth_cookie_handler = AuthCookieHandler(
    secure=CookieSettings.SECURE,
    path=CookieSettings.PATH,
    samesite=CookieSettings.SAMESITE,
)

# ------------------------- Token Router -------------------------

token_router = APIRouter(prefix="/token")

@token_router.post('', description="로그인 하여 액세스 토큰 및 리프래시 토큰 발급")
async def issue_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> JSONResponse:
    """
    로그인 하여 액세스 토큰 및 리프래시 토큰 발급
    """
    start_time = time()
    tokens: service.IssueTokenResponse = await service.issue_token_by_login_form(request, db, redis, form_data)
    logger.info(f"User '{form_data.username}' logged in and tokens issued.")
    
    auth_cookie_handler.set_token_cookies(
        response=response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token
    )

    logger.info(f"Token issuance process took {time() - start_time:.4f} seconds.")

    return schemas.AuthTokenIssueResponse(
        access_token=tokens.access_token.token,
        token_type="bearer"
    )


@token_router.post('/refresh', description="리프래시 토큰으로 액세스 토큰 직접 재발급")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> JSONResponse:
    """리프래시 토큰으로 액세스 토큰 직접 재발급"""
    tokens: service.IssueTokenResponse = await service.rotate_tokens(request, db, redis)
    logger.info(f"Refresh token used to issue new access token.")

    auth_cookie_handler.set_token_cookies(
        response=response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token
    )

    return schemas.AuthTokenIssueResponse(
        access_token=tokens.access_token.token
    )


@token_router.delete("", description="로그아웃 처리 및 토큰 무효화")
async def revoke_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    await service.revoke_token(request, db, redis)
    auth_cookie_handler.delete_token_cookies(response)
    return schemas.AuthTokenRevokeResponse()