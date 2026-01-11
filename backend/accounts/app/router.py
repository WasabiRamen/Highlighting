# service/accounts/app/router.py
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

# App imports
from . import schemas, service, exceptions

# Shared imports
from ...shared.core.database import get_db
from ...shared.tools.get_token_rotator import get_token_rotator, AccessTokenPayload

router = APIRouter(prefix="/accounts")

@router.post("", description="Create a new account")
async def create_account(
    account_data: schemas.CreateAccount,
    db: AsyncSession = Depends(get_db)
):
    new_account = await service.create_account(
        db=db,
        user_id=account_data.user_id,
        password=account_data.password,
        user_name=account_data.user_name,
        email=account_data.email,
        email_token=account_data.token,
        phone_number=account_data.phone_number
    )
    return {"status": "Account created successfully", "account": new_account}


@router.get("/me", description="Get current user's account information")
async def get_current_user_account(
    db: AsyncSession = Depends(get_db),
    token_payload: AccessTokenPayload = Depends(get_token_rotator)
):
    user = await service.get_current_user(db, token_payload)
    if not user:
        raise exceptions.AccountNotFoundException()
    return user


@router.post("/link_provider")
async def link_provider(
    form: schemas.LinkProviderRequest,
    db: AsyncSession = Depends(get_db),
    token_payload: AccessTokenPayload = Depends(get_token_rotator)
):
    """구글 OAuth2 계정 연결 처리"""
    result = await service.link_provider(db, form.code, "google", token_payload)
    return result