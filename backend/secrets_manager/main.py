# secrets_manager/main.py

# Standard Librarys
from contextlib import asynccontextmanager
import os
import asyncio

# RestAPI Libraries
from fastapi import FastAPI, Request
from fastapi.responses import Response
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# gRPC Libraries
import grpc
from grpc_health.v1 import health_pb2 as grpc_health_pb2
from grpc_health.v1 import health_pb2_grpc as grpc_health_pb2_grpc

# Local Libraries
from app.grpc.server import start_grpc_server, stop_grpc_server
from app.core.settings import (
    get_fastapi_settings,
    get_database_settings,
    get_security_settings
)

try:
    from shared.core.database import init_db, close_db
except ImportError:
    from backend.shared.core.database import init_db, close_db

from app.tools.mk import read_master_key


# Settings
database_settings = get_database_settings()
fastapi_settings = get_fastapi_settings()
security_settings = get_security_settings()


# Master Key path
MASTER_KEY_PATH = security_settings.MASTER_KEY_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Startup / Shutdown handler.

    Startup
        - Start gRPC server (aio)
    Shutdown
        - Stop gRPC server (graceful)
    """
    # Database Initialization
    await init_db(database_settings, app)
    logger.info("[Database] Database connection initialized")

    app.state.master_key = await read_master_key(MASTER_KEY_PATH)
    logger.info("[Security] Master key loaded from {}", MASTER_KEY_PATH)

    # gRPC Server Startup
    grpc_server = await start_grpc_server(
        app,
        database_settings=database_settings,
        master_key_path=MASTER_KEY_PATH,
    )
    app.state.grpc_server = grpc_server

    try:
        yield
    finally:
        # gRPC Server Shutdown
        grpc_server = getattr(app.state, "grpc_server", None)
        if grpc_server is not None:
            await stop_grpc_server(app, grpc_server)

        # Database Disconnection
        await close_db(app)
        logger.info("[Database] Database connection closed")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=fastapi_settings.NAME, 
    version=fastapi_settings.VERSION,
    lifespan=lifespan
    )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
@limiter.limit("5/minute")
async def root(request: Request):
    """
    Root endpoint
    루트 엔드포인트
    """
    return {
        "service": "secrets_manager", "status": "running"
        }


@app.get("/health")
@limiter.limit("5/minute")
async def health(request: Request):
    """
    Health check endpoint
    헬스체크 엔드포인트
    """
    return {"status": "healthy"}


@app.get("/grpc-health")
@limiter.limit("5/minute")
async def grpc_health(request: Request):
    """gRPC health check endpoint.

    Calls the standard gRPC Health service exposed by this application.
    """

    grpc_port = int(os.getenv("GRPC_PORT", "50051"))
    grpc_host = os.getenv("GRPC_HOST", "0.0.0.0")
    target_host = "127.0.0.1" if grpc_host in {"0.0.0.0", "::"} else grpc_host
    target = f"{target_host}:{grpc_port}"
    
    try:
        # TLS 설정에 따라 channel 생성
        if security_settings.GRPC_TLS_ENABLED and security_settings.GRPC_CA_CERT_PATH:
            # TLS enabled: CA 인증서 로드
            try:
                with open(security_settings.GRPC_CA_CERT_PATH, "rb") as f:
                    ca_cert = f.read()
                channel_creds = grpc.ssl_channel_credentials(root_certificates=ca_cert)
                channel = grpc.aio.secure_channel(target, channel_creds)
            except FileNotFoundError:
                logger.error(f"[gRPC Health] CA cert not found: {security_settings.GRPC_CA_CERT_PATH}")
                return {"status": "unhealthy", "error": "CA cert not found"}
        else:
            # TLS disabled: insecure channel (개발 환경 전용)
            channel = grpc.aio.insecure_channel(target)
        
        async with channel:
            stub = grpc_health_pb2_grpc.HealthStub(channel)
            resp = await stub.Check(
                grpc_health_pb2.HealthCheckRequest(service="secrets_manager.v1.SecretsManagerService"),
                timeout=2.0,
            )

        status_name = grpc_health_pb2.HealthCheckResponse.ServingStatus.Name(resp.status)
        return {"status": "healthy" if resp.status == resp.SERVING else "unhealthy", "grpc": status_name}
    except asyncio.TimeoutError:
        logger.error("[gRPC Health] Timeout connecting to gRPC server at {}", target)
        return {"status": "unhealthy", "error": "gRPC server timeout"}
    except grpc.aio.AioRpcError as e:
        logger.error("[gRPC Health] gRPC error: {} - {}", e.code(), e.details())
        return {"status": "unhealthy", "error": f"gRPC error: {e.code()}"}
    except Exception as e:
        logger.exception("[gRPC Health] Health check failed")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/metrics")
@limiter.limit("5/minute")
async def metrics(request: Request):
    """
    Metrics endpoint
    메트릭 엔드포인트
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
