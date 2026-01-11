from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import SecretsManagerSecret, AsymmetricKeyPair, SymmetricKey

#------------------------------- Secret CRUD Logic ---------------------------

async def create_secret(
        db: AsyncSession, 
        kid: str,
        key_name: str,
    key_type: str | None,
        value: bytes,
        created_at,
        mk_version: int
    ):
    db_secret = SecretsManagerSecret(
        kid=kid,
        key_name=key_name,
        key_type=key_type,
        value=value,
        created_at=created_at,
        mk_version=mk_version
    )

    # 기존 항목 불러오기 / 비활성화
    old_secret = await get_secret_by_key_name(db, key_name)
    if old_secret:
        old_secret.is_active = False
        db.add(old_secret)
        await db.commit()
        await db.refresh(old_secret)

    db.add(db_secret)
    await db.commit()
    await db.refresh(db_secret)
    return db_secret

async def get_secret_by_key_name(db: AsyncSession, key_name: str) -> SecretsManagerSecret:
    result = await db.execute(
        select(SecretsManagerSecret)
        .where(SecretsManagerSecret.key_name == key_name)
        .where(SecretsManagerSecret.is_active.is_(True))
    )
    return result.scalar_one_or_none()

# --------------------------- Asymmetric Key Pair CRUD Functions ---------------------------

async def create_asymmetric_key_pair(
        db: AsyncSession,
        kid: str,
        key_name: str,
        private_key: bytes,
        public_key: bytes,
        created_at,
        mk_version: int = 1,
        key_type: str | None = None,
        key_size: int | None = None,
        expires_at=None,
    ) -> None:
    """비대칭 키 쌍 생성"""
    db_key_pair = AsymmetricKeyPair(
        kid=kid,
        key_name=key_name,
        private_key=private_key,
        public_key=public_key,
        created_at=created_at,
        key_type=key_type,
        mk_version=mk_version
    )
    # 기존 항목 불러오기 / 비활성화 (동일 key_name이 있을 경우 이전 항목을 비활성화)
    old_pair = await get_asymmetric_key_pair_by_key_name(db, key_name, return_key_type='pair')
    if old_pair:
        old_pair.is_active = False
        db.add(old_pair)
        await db.commit()
        await db.refresh(old_pair)

    db.add(db_key_pair)
    await db.commit()
    await db.refresh(db_key_pair)
    return db_key_pair


async def get_asymmetric_key_pair_by_key_name(
        db: AsyncSession,
        key_name: str,
        return_key_type: str = 'public'
    ) -> AsymmetricKeyPair | None:
    """비대칭 키 쌍 조회"""
    allow_key_types = ['pair', 'public']
    if return_key_type not in allow_key_types:
        raise ValueError(f"Invalid key_type: {return_key_type}. Allowed types are: {allow_key_types}")
    
    result = await db.execute(
        select(AsymmetricKeyPair)
        .where(AsymmetricKeyPair.key_name == key_name)
        .where(AsymmetricKeyPair.is_active.is_(True))
        .order_by(AsymmetricKeyPair.created_at.desc())
        .execution_options(populate_existing=True)
    )
    result = result.scalar_one_or_none()

    if result and return_key_type == 'public':
        result.private_key = None

    return result


# --------------------------- Symmetric Key CRUD Functions ---------------------------

async def create_symmetric_key(
        db: AsyncSession,
        kid: str,
        key_name: str,
        key_type: str,
        key_value: bytes,
        created_at,
        mk_version: int = 1,
        key_size: int | None = None,
        expires_at=None,
    ) -> None:
    """대칭 키 생성"""
    db_symmetric_key = SymmetricKey(
        kid=kid,
        key_name=key_name,
        key_type=key_type,
        key_value=key_value,
        created_at=created_at,
        mk_version=mk_version,
    )
    # 기존 항목 불러오기 / 비활성화
    old_sym = await get_symmetric_key_by_key_name(db, key_name)
    if old_sym:
        old_sym.is_active = False
        db.add(old_sym)
        await db.commit()
        await db.refresh(old_sym)

    db.add(db_symmetric_key)
    await db.commit()
    await db.refresh(db_symmetric_key)
    return db_symmetric_key


async def get_symmetric_key_by_key_name(
        db: AsyncSession,
        key_name: str
    ) -> SymmetricKey | None:
    """대칭 키 조회"""
    result = await db.execute(
        select(SymmetricKey)
        .where(SymmetricKey.key_name == key_name)
        .where(SymmetricKey.is_active.is_(True))
        .order_by(SymmetricKey.created_at.desc())
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()
