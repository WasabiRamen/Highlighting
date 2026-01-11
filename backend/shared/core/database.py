# backend/shared/core/database.py  
# Usage : FastAPI / gRPC Shared

from typing import AsyncGenerator, Optional
from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import URL
from sqlalchemy import text
from pydantic import BaseModel, Field
from loguru import logger

Base = declarative_base()

# gRPC Only Usage Variables
_SessionLocal: sessionmaker | None = None
_db_engine: AsyncEngine | None = None

class DatabaseSettings(BaseModel):
    # URL Setting
    host: str = Field(..., description="데이터베이스 호스트")
    port: int = Field(..., description="데이터베이스 포트")
    user: str = Field(..., description="데이터베이스 사용자 이름")
    password: str = Field(..., description="데이터베이스 비밀번호")
    name: str = Field(..., description="데이터베이스 이름")

    # Engine Setting
    pool_pre_ping: bool = Field(True, description="커넥션 풀의 연결 상태를 확인할지 여부")
    pool_size: int = Field(20, description="기본 연결 풀 크기")
    max_overflow: int = Field(30, description="풀 초과 시 추가 생성 가능한 연결 수")
    pool_recycle: int = Field(3600, description="연결 재생성 주기 (초 단위)")
    pool_timeout: int = Field(30, description="연결 대기 시간 (초)")

def get_database_url(setting: DatabaseSettings) -> str:
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=setting.user,
        password=setting.password,
        host=setting.host,
        port=setting.port,
        database=setting.name,
    )
    return url.render_as_string(hide_password=False)


async def init_db(setting: DatabaseSettings, app: FastAPI = None) -> None:
    """
    Lifespan에서 호출: 엔진/세션메이커를 1회 생성하여 app.state에 저장
    """
    engine: AsyncEngine = create_async_engine(
        get_database_url(setting),
        pool_pre_ping=setting.pool_pre_ping,  # 끊어진 커넥션 자동 감지
        pool_size=setting.pool_size,  # 기본 연결 풀 크기 (기본값: 5)
        max_overflow=setting.max_overflow,  # 풀 초과 시 추가 생성 가능한 연결 수 (기본값: 10)
        pool_recycle=setting.pool_recycle,  # 1시간마다 연결 재생성 (초 단위)
        pool_timeout=setting.pool_timeout,  # 연결 대기 시간 (초)
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    if isinstance(app, FastAPI):
        app.state.db_engine = engine
        app.state.async_session_maker = SessionLocal
    else:
        global _SessionLocal, _db_engine
        _db_engine = engine
        _SessionLocal = SessionLocal

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("DB initial connection test failed")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        logger.exception("DB schema create_all 실패")

    logger.info(f"DB Successfully connected : {setting.host}")


async def close_db(app: FastAPI = None) -> None:
    """
    Lifespan 종료 시 호출: 엔진 정리
    """
    if isinstance(app, FastAPI):
        engine: Optional[AsyncEngine] = getattr(app.state, "db_engine", None)
    else:
        global _db_engine
        engine = _db_engine
    
    if engine is not None:
        logger.info(f"DB Successfully disconnected")
        await engine.dispose()

async def get_db(request: Request = None) -> AsyncGenerator[AsyncSession, None]:
    """
    요청 단위 의존성: 세션을 열고, 요청 처리 후 자동 닫기
    """
    if isinstance(request, Request):
        SessionLocal = getattr(request.app.state, "async_session_maker", None)
    else:
        global _SessionLocal
        SessionLocal = _SessionLocal

    if SessionLocal is None:
        raise RuntimeError("Async session maker is not initialized on app.state")
    async with SessionLocal() as session:
        yield session


# 간단한 DB 헬스체크 쿼리 예시 유틸
async def db_healthcheck(session: AsyncSession) -> bool:
    try:
        result = await session.execute(text("SELECT 1"))
        return (result.scalar() == 1)
    except Exception:
        logger.exception("DB healthcheck failed")
        return False
