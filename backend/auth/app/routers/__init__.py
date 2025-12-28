# auth/app/routers/__init__.py
"""Auth Service Routers Package"""
from fastapi import APIRouter
from .token_router import token_router
from .email_verify_router import email_verify_router
from .google_auth2_router import google_oauth2_router

router = APIRouter(prefix="/auth", tags=["Auth"])

router.include_router(token_router)
router.include_router(email_verify_router)
router.include_router(google_oauth2_router)

__all__ = ["router"]