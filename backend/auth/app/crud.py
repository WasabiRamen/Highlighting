from datetime import datetime, timezone

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AuthUser,
    AuthOAuthAccount, 
    AuthEmailVerification, 
    AuthRefreshToken,
    RSAKey
)

from .core.security.refresh_token import RefreshTokenService

# -------------------------------- Function Logic ---------------------------

def ts_to_dt(timestamp: int):
    """타임스탬프를 datetime 객체로 변환"""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

# -------------------------------- Exception Logic ---------------------------

class RefreshTokenNotFound(Exception):
    """Refresh token not found exception"""
    pass

# -------------------------------- Token CRUD Logic ---------------------------

async def existing_user_id(db: AsyncSession, user_id: str):
    """사용자 아이디 존재 여부 확인"""
    result = await db.execute(
        select(AuthUser).where(
            AuthUser.user_id == user_id
        )
    )
    user = result.scalars().first()
    return user is not None

async def get_user_by_user_id(db: AsyncSession, user_id: str):
    """사용자 아이디로 사용자 조회"""
    result = await db.execute(
        select(AuthUser).where(
            AuthUser.user_id == user_id
        )
    )
    user = result.scalars().first()
    return user

async def deactivate_refresh_token(
        db: AsyncSession, 
        refresh_token: str | None = None,
        rotate: bool = False
        ) -> None:
    """
    리프래시 토큰 비활성화
    
    Note: commit은 호출자에서 처리하도록 변경
    """
    result = await db.execute(
        select(AuthRefreshToken).where(
            AuthRefreshToken.refresh_token == refresh_token,
            AuthRefreshToken.is_active == True
        )
    )
    db_token = result.scalars().first()
    if not db_token:
        if rotate:
            raise RefreshTokenNotFound()
        return None

    db_token.is_active = False
    db.add(db_token)


async def issue_refresh_token(
        db: AsyncSession, 
        user_uuid: str,
        token: RefreshTokenService.TokenResponse,
        ip_address: str = None, 
        user_agent: str = None
    ) -> None:
    """
    리프래시 토큰 발급 및 저장
    
    Note: commit은 호출자에서 처리하도록 변경
    """
    # 새로운 리프래시 토큰 생성
    db_refresh_token = AuthRefreshToken(
        refresh_token=token.token,
        user_uuid=user_uuid,
        expires_at=ts_to_dt(token.expires_at),
        created_at=ts_to_dt(token.created_at),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(db_refresh_token)

async def get_refresh_token(
        db: AsyncSession,
        refresh_token: str
    ) -> AuthRefreshToken | None:
    """리프래시 토큰 조회"""
    result = await db.execute(
        select(AuthRefreshToken).where(
            AuthRefreshToken.refresh_token == refresh_token,
            AuthRefreshToken.is_active == True
        )
    )
    db_token = result.scalars().first()
    return db_token


async def get_rsa_public_key(db: AsyncSession, kid: str):
    """활성화된 공개 키 목록 조회"""
    result = await db.execute(
        select(RSAKey).where(
            RSAKey.kid == kid
        )
    )
    key = result.scalars().first()
    return key

# Email CRUD Functions
# -----------------------------------------------------------------

async def existing_email_token(db: AsyncSession, token: str) -> bool:
    """이메일 인증 토큰 존재 여부 확인"""
    result = await db.execute(
        select(AuthEmailVerification).where(
            AuthEmailVerification.token == token,
        )
    )
    code = result.scalars().first()
    return code is not None

async def existing_email_verified(db: AsyncSession, email: str) -> bool:
    """
    이메일이 이미 인증되었는지 확인

    인증이 되었고, 사용된 토큰이 존재하면, True 반환
    """
    result = await db.execute(
        select(AuthEmailVerification).where(
            AuthEmailVerification.email == email,
            AuthEmailVerification.is_verified == True,
            AuthEmailVerification.is_used == True
        )
    )
    code = result.scalars().first()
    return code is not None


async def is_email_verified(db: AsyncSession, token: str) -> str | None:
    """
    이메일이 인증되었는지 확인

    인증 된 이메일이면 이메일 주소를 반환
    """
    result = await db.execute(
        select(AuthEmailVerification).where(
            AuthEmailVerification.token == token,
            AuthEmailVerification.is_verified == True,
            AuthEmailVerification.is_used == False
        )
    )
    code = result.scalars().first()

    if code:
        return code.email

    return None


async def save_email_verification_code(
        db: AsyncSession,
        email: str,
        token: str,
        code: str,
        expires_at: int
    ) -> None:
    """이메일 인증 코드 저장"""
    db_code = AuthEmailVerification(
        token=token,
        code=code,
        email=email,
        expires_at=ts_to_dt(expires_at)
    )
    db.add(db_code)
    await db.commit()


async def update_email_verification_code_as_verified(db: AsyncSession, token: str) -> None:
    """이메일 인증 코드 검증 처리"""
    result = await db.execute(
        select(AuthEmailVerification).where(
            AuthEmailVerification.token == token,
            AuthEmailVerification.is_used == False,
            AuthEmailVerification.is_verified == False
        )
    )
    db_code = result.scalars().first()
    if not db_code:
        return

    db_code.is_verified = True
    db.add(db_code)
    await db.commit()


async def update_email_verification_code_as_used(db: AsyncSession, token: str) -> None:
    """이메일 인증 코드 사용 처리"""
    result = await db.execute(
        select(AuthEmailVerification).where(
            AuthEmailVerification.token == token,
        )
    )
    db_code = result.scalars().first()
    if not db_code:
        return

    db_code.is_used = True
    db.add(db_code)
    await db.commit()


# OAuth CRUD Functions
# -----------------------------------------------------------------


async def validate_provider_id(
        db: AsyncSession,
        user_uuid: str,
        provider: str,
        provider_id: str
    ) -> bool:
    """연동 가능한 상태인지 확인 / 존재 유무 파악"""
    # user_uuid로 이미 동일 provider가 연결 된 경우
    result = await db.execute(
        select(AuthOAuthAccount).where(
            AuthOAuthAccount.user_uuid == user_uuid,
            AuthOAuthAccount.provider == provider
        )
    )
    oauth_account = result.scalars().first()
    if oauth_account:
        return False
    
    # 동일 provider, provider_id가 이미 연결 된 경우
    result = await db.execute(
        select(AuthOAuthAccount).where(
            AuthOAuthAccount.provider == provider,
            AuthOAuthAccount.provider_id == provider_id
        )
    )
    oauth_account = result.scalars().first()
    if oauth_account:
        return False
    
    return True


async def link_oauth_account(
        db: AsyncSession,
        user_uuid: str,
        provider: str,
        provider_id: str,
    ) -> AuthOAuthAccount:
    """OAuth 계정 연결 처리"""
    db_oauth_account = AuthOAuthAccount(
        oauth_id=f"{provider}_{provider_id}",
        user_uuid=user_uuid,
        provider=provider,
        provider_id=provider_id
    )
    db.add(db_oauth_account)
    await db.commit()
    await db.refresh(db_oauth_account)
    return db_oauth_account

async def get_user_by_provider_id(
        db: AsyncSession,
        provider: str,
        provider_id: str,
    ) -> AuthOAuthAccount:
    """
    로그인용 CRUD
    
    provider_id -> DB 조회 후 연결된 User 정보 반환
    """
    result = await db.execute(
        select(AuthOAuthAccount).where(
            AuthOAuthAccount.provider == provider,
            AuthOAuthAccount.provider_id == provider_id
        )
    )
    user_uuid = result.scalars().first()
    
    result = await db.execute(
        select(AuthUser).where(
            AuthUser.user_uuid == user_uuid.user_uuid
        )
    )
    user = result.scalars().first()

    return user