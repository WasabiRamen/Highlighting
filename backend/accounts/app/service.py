# Standard library imports
import json
from datetime import datetime, timezone

# Third-party imports
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# App imports
from . import crud

# Shared imports
from app.shared.tools.token.get_token_rotator import get_token_rotator

# Auth Service imports (차후 gRPC로 분리 예정)
from app.service.auth.app.service import create_auth_user, link_oauth_account, google_code_to_token


class InvalidGoogleTokenException(Exception):
    pass


async def create_account(
    db: AsyncSession,
    user_id: str,
    password: str,
    user_name: str,
    email: str,
    email_token: str,
    phone_number: str
):
    """
    계정 생성 서비스

    프로필 생성 -> 인증생성
    """
    logger.info(f"Creating account for user_id: {user_id}")
    auth_user = await create_auth_user(
        db=db,
        user_id=user_id,
        password=password,
        email=email,
        email_token=email_token,
    )

    user_uuid = auth_user.user_uuid

    new_account = await crud.create_account(
        db=db,
        user_name=user_name,
        email=email,
        user_uuid=user_uuid,
        phone_number=phone_number
    )
    logger.info(f"Account created successfully for user_id: {user_id}")
    return new_account


async def get_current_user(
        db: AsyncSession,
        token_payload: get_token_rotator
    ):
    result = await crud.get_account_by_uuid(
        db=db,
        user_uuid=token_payload.sub
    )
    return result


async def link_provider(
         db: AsyncSession,
         code: str,
         provider: str,
         token_payload: get_token_rotator
):
    """
    APP TOKEN으로 OAuth 계정 연결 처리

    Description:
        access token이 유효한 상태여야함.
    """
    allowd_providers = ['google']
    if provider not in allowd_providers:
        raise ValueError("지원하지 않는 OAuth 제공자입니다.")

    if provider == 'google':
        oauth_user_info = await google_code_to_token(code)
        if not oauth_user_info:
            raise InvalidGoogleTokenException("구글 인증에 실패했습니다.")
        provider_id = oauth_user_info.get("id")
        
    user_uuid = token_payload.sub

    await link_oauth_account(
        db=db,
        user_uuid=user_uuid,
        provider=provider,
        provider_id=provider_id
    )

    await crud.append_linked_provider(
        db=db,
        user_uuid=user_uuid,
        provider=provider
    )

    return {
        'status': True
    }