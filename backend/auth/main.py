from fastapi import FastAPI

app = FastAPI(title="Accounts Service")


@app.get("/")
async def root():
    return {"service": "accounts", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}



#--------------------------------------------------------------------------


# Standard Library
import asyncio
from contextlib import asynccontextmanager

# Third Party
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from crypto_toolkit.key_management import asymmetric

# FastAPI
from fastapi import FastAPI, Depends
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware

# Settings
from backend.shared.core._old.settings import (
    get_database_runtime,
    get_redis_runtime,
    get_smtp_runtime,
    get_auth_settings,
    get_app_settings,
    get_cors_settings
)

# Core
from backend.shared.core._old.database import (
    init_db,
    close_db,
    get_db,
    db_healthcheck
)
from backend.shared.core._old.redis import (
    init_redis,
    close_redis
)
from app.shared.core.async_mail_client import AsyncEmailClient

# Services
from app.service.auth.tools.rsa_keys.key_rotation import RSAKeyRotation
from app.service.auth import router as auth_router
from app.service.accounts import router as accounts_router

# Exception handlers
from app.service.auth import (
    register_token_exception_handlers,
    register_email_verification_exception_handlers,
    register_oauth_exception_handlers,
)
from app.service.accounts import (
    register_accounts_exception_handlers,
)


"""
@Todo:
    - 예외 처리 및 리팩토링 (Auth Service / Shared Tool - Token)
    - Email Token -> Cookie 처리 변경 검토
    - 로깅 상세화
    - 테스트 케이스 작성
    - 문서화
    - API 성능 테스트 (부하 테스트)
"""


auth_settings = get_auth_settings()
smtp_runtime = get_smtp_runtime()
app_settings = get_app_settings()
cors_settings = get_cors_settings()
database_runtime = get_database_runtime()
redis_runtime = get_redis_runtime()
smtp_runtime = get_smtp_runtime()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB 먼저 초기화 (다른 컴포넌트가 세션메이커를 사용하므로 선행)
    await init_db(app, database_runtime)

    rsa_key_rotation = asymmetric.KeyRotator(
        key_size = asymmetric.RSAKeySize.RSA2048,
        rotation_interval_days=10,
        load_type=asymmetric.LoadType.FILE,
        options=asymmetric.FileLoadOptions(
            private_key_path="/workspaces/FastAPI-MSA-Ready-Template/backend/keys/private_key.json",
            public_key_path="/workspaces/FastAPI-MSA-Ready-Template/backend/keys/public_key.json",
        )
    )
    await rsa_key_rotation.init()
    app.state.rsa_key_rotation = rsa_key_rotation

    # # JWT Key Manager (DB 초기화 이후에 실행, app 전달)
    # rsa_key_rotation = RSAKeyRotation(
    #     private_key_path=auth_settings.RSA_PRIVATE_KEY_PATH,
    #     public_key_path=auth_settings.RSA_PUBLIC_KEY_PATH,
    # )
    # await rsa_key_rotation.init(app)
    # app.state.rsa_key_manager = rsa_key_rotation

    # Redis
    await init_redis(app, redis_runtime)

    # SMTP
    app.state.smtp = AsyncEmailClient(smtp_runtime)
    await app.state.smtp.connect()

    try:
        yield
    finally:
        # Shutdown: 전역 리소스 정리 (순서 및 예외 안전성 강화)
        cleanup_tasks = [
            ("SMTP", app.state.smtp.disconnect),
            ("Redis", lambda: close_redis(app)),
            ("DB", lambda: close_db(app)),
            ("Scheduler", lambda: asyncio.to_thread(rsa_key_rotation.scheduler.shutdown, wait=False)),
        ]
        for name, task in cleanup_tasks:
            try:
                await task()
            except Exception as e:
                logger.error(f"[Shutdown] Failed to close {name}: {e}")


# app Instance
app = FastAPI(
    title=app_settings.NAME,
    version=app_settings.VERSION,
    lifespan=lifespan,
    prefix="/api"
    )

# Register Exception Handlers
register_token_exception_handlers(app)
register_email_verification_exception_handlers(app)
register_oauth_exception_handlers(app)
register_accounts_exception_handlers(app)

# Bind Routers
app.include_router(auth_router)
app.include_router(accounts_router)

app.state.public_keys = {}  # 초기값 설정

# CORS 설정 - HTTP 테스트 가능하도록 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings.origins_list,  # 허용할 출처 목록
    allow_credentials=cors_settings.ALLOW_CREDENTIALS,  # 쿠키 포함 요청 허용
    allow_methods=["*"],     # 모든 HTTP 메서드 허용
    allow_headers=["*"],     # 모든 헤더 허용
)


@app.get("/health", description="Health Check")
async def read_root(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """헬스체크 엔드포인트"""
    db_health = await db_healthcheck(db)
    
    # Redis 비동기 ping
    try:
        redis_health = await request.app.state.redis.ping()
    except Exception:
        redis_health = False

    return {
        "status": "ok",
        "database": "ok" if db_health else "error",
        "redis": "ok" if redis_health else "error"
    }


@app.get("/keys/current-rsa-private-key", description="Get Current RSA Private Key")
async def get_current_rsa_private_key(request: Request):
    print(request.app.state.rsa_key_manager_v2.private_key)
    return {
        "current_rsa_private_key": request.app.state.rsa_key_manager_v2.current_key_pair.private_key
    }