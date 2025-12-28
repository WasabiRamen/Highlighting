# auth/routers/google_auth2_router.py
# FastAPI imports
from fastapi import APIRouter, Depends
from fastapi.requests import Request

# SQLAlchemy & Third Party imports
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

# App imports
from .. import service, schemas

# Shared imports
from app.shared.core.database import get_db

# ------------------------- Google Router -------------------------

google_oauth2_router = APIRouter(prefix="/google")

@google_oauth2_router.post("/login")
async def google_login(
    request: Request,
    form: schemas.GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """구글 OAuth2 로그인 콜백 처리"""
    result = await service.google_login(request, db, form.code)
    logger.info(f"Google OAuth2 login processed.")
    return result