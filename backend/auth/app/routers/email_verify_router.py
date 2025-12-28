# auth/routers/email_verify_router.py
# FastAPI imports
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import Response

# SQLAlchemy & Third Party imports
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# App imports
from .. import service, schemas

# Shared imports
from app.shared.core.redis import Redis, get_redis
from app.shared.core.async_mail_client import get_smtp_client, AsyncEmailClient
from app.shared.core.database import get_db
from app.shared.core.cookie_handler import EmailVerifyCookieHandler
from app.shared.core.settings import get_cookie_settings


cookie_settings = get_cookie_settings()

email_verify_cookie_handler = EmailVerifyCookieHandler(
    secure=cookie_settings.SECURE,
    path=cookie_settings.PATH,
    samesite=cookie_settings.SAMESITE
)

# ------------------------- Email Router -------------------------

email_verify_router = APIRouter(prefix="/email")

@email_verify_router.post("")
async def send_email_verification(
    response: Response,
    form: schemas.SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    smtp: AsyncEmailClient = Depends(get_smtp_client)
):
    """
    이메일 인증 토큰 및 코드 발급

    예외:
        - 이미 인증된 이메일인 경우 예외 발생
    """
    result = await service.send_email_verification(db, redis, smtp, form.email)
    email_verify_cookie_handler.set_email_verify_cookie(response, result.token, result.expires_in)
    logger.info(f"Email verification sent to '{form.email}'.")
    return schemas.EmailTokenIssueResponse(
        email = result.email,
    )


@email_verify_router.post("/verify")
async def verify_email_code(
    request: Request,
    form: schemas.VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    이메일 인증 코드 검증
    예외:
        - 인증 토큰이 없거나 만료된 경우 예외 발생
        - 인증 코드가 일치하지 않는 경우 예외 발생
    """
    verify_token = email_verify_cookie_handler.get_email_verify_cookie(request)
    # 예외처리 필요
    result = await service.verify_email_token(db, redis, verify_token, form.code)
    logger.info(f"Email verification token checked for token '{verify_token}'.")
    return schemas.EmailVerifySuccessResponse(
        email = result,
    )