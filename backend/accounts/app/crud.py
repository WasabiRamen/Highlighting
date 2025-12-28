# service/accounts/app/crud.py

"""계정 CRUD 서비스"""

# Third Party imports
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# Shared imports
from .models import Account

async def create_account(
        db: AsyncSession,
        user_name: str,
        email: str,
        user_uuid: str,
        phone_number: str | None = None,
    ) -> Account:
    """새로운 계정 생성"""
    new_account = Account(
        user_uuid=user_uuid,
        user_name=user_name,
        email=email,
        phone_number=phone_number,
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account


async def get_account_by_uuid(
        db: AsyncSession,
        user_uuid: str,
    ) -> Account | None:
    """user_uuid로 계정 조회"""
    result = await db.execute(
        select(Account).where(Account.user_uuid == user_uuid)
    )
    account = result.scalars().first()
    return account


async def update_account_provider(
        db: AsyncSession,
        user_uuid: str,
        provider: str,
    ) -> Account | None:
    """
    계정을 소셜 프로바이더 정보로 업데이트
    
    추가시, 기존 것을 같이 보내줘야될 소요 필요함.
    """
    result = await db.execute(
        select(Account).where(Account.user_uuid == user_uuid)
    )
    account = result.scalars().first()
    if account:
        account.provider = provider
        await db.commit()
        await db.refresh(account)
    return account


async def update_account_profile_image(
        db: AsyncSession,
        user_uuid: str,
        profile_image_url: str,
    ) -> Account | None:
    """계정을 프로필 이미지 URL로 업데이트"""
    result = await db.execute(
        select(Account).where(Account.user_uuid == user_uuid)
    )
    account = result.scalars().first()
    if account:
        account.profile_image_url = profile_image_url
        await db.commit()
        await db.refresh(account)
    return account


async def append_linked_provider(
        db: AsyncSession,
        user_uuid: str,
        provider: str,
    ) -> Account | None:
    """계정에 소셜 프로바이더를 추가로 연결"""
    result = await db.execute(
        select(Account).where(Account.user_uuid == user_uuid)
    )
    account = result.scalars().first()
    if account:
        if account.linked_providers:
            providers = account.linked_providers.split(",")
            if provider not in providers:
                providers.append(provider)
                account.linked_providers = ",".join(providers)
        else:
            account.linked_providers = provider
        await db.commit()
        await db.refresh(account)
    return account