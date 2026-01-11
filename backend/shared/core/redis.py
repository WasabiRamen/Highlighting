# backend/auth/app/redis.py
from typing import Optional
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from loguru import logger
import redis.asyncio as redis


class RedisSettings(BaseModel):
    host: str = Field(..., description="Redis 호스트")
    port: int = Field(..., description="Redis 포트")
    db: int = Field(..., description="Redis DB 번호")
    user: Optional[str] = Field(None, description="Redis 사용자명")
    password: Optional[str] = Field(None, description="Redis 비밀번호")


# gRPC Usage Variables
_redis_client: redis.Redis | None = None


async def init_redis(setting: RedisSettings, app: FastAPI = None) -> None:
    """
    Redis 클라이언트 초기화
    커넥션 풀 설정으로 성능 개선
    """
    redis_client = redis.Redis(
        host=setting.host,
        port=setting.port,
        db=setting.db,
        username=setting.user,
        password=setting.password,
        decode_responses=True,
        max_connections=50,  # 커넥션 풀 크기
        socket_keepalive=True,  # TCP keepalive 활성화
        retry_on_timeout=True,  # 타임아웃 시 재시도
        health_check_interval=30  # 30초마다 헬스체크
    )
    
    if isinstance(app, FastAPI):
        app.state.redis_client = redis_client
    else:
        global _redis_client
        _redis_client = redis_client
    
    # 연결 테스트
    try:
        await redis_client.ping()
        logger.info(f"Redis Successfully connected : {setting.host}:{setting.port}")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise


async def close_redis(app: FastAPI = None) -> None:
    """Redis 클라이언트 종료"""
    if isinstance(app, FastAPI):
        redis_client: Optional[redis.Redis] = getattr(app.state, "redis_client", None)
    else:
        global _redis_client
        redis_client = _redis_client

    if redis_client is not None:
        await redis_client.close()
        logger.info("Redis Successfully disconnected")


async def get_redis(request: Request = None) -> redis.Redis:
    """Redis 클라이언트 의존성"""
    if isinstance(request, Request):
        redis_client = getattr(request.app.state, "redis_client", None)
    else:
        global _redis_client
        redis_client = _redis_client
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized on app.state")
    return redis_client


# Redis 유틸리티 클래스
class Redis:
    def __init__(self, client: redis.Redis):
        self.client = client
    
    async def set_with_ttl(self, key: str, value: str, ttl: int) -> bool:
        """키-값 쌍을 TTL과 함께 저장"""
        return await self.client.setex(key, ttl, value)
    
    async def get(self, key: str) -> Optional[str]:
        """키로 값 조회"""
        return await self.client.get(key)
    
    async def delete(self, key: str) -> bool:
        """키 삭제"""
        return await self.client.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        return await self.client.exists(key) > 0
