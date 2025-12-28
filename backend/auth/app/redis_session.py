# Standard Library
from uuid import UUID
from typing import Optional

# Third Party
import redis.asyncio as redis
from pydantic import BaseModel, Field

# Redis 세션 데이터 스키마
class SessionData(BaseModel):
    user_uuid: UUID = Field(..., description="사용자 UUID")
    refresh_token: str = Field(..., description="리프래시 토큰")
    expires_at: int = Field(..., description="만료 시각 (타임스탬프)")


class RedisSession:
    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def save(self, session_id: str, session: SessionData, session_ttl: int) -> None:
        await self.redis.set(
            session_id,
            session.model_dump_json(),
            ex=session_ttl
        )

    async def get(self, session_id: str) -> Optional[SessionData]:
        raw = await self.redis.get(session_id)
        if raw is None:
            return None
        return SessionData.model_validate_json(raw)

    async def delete(self, session_id: str) -> None:
        await self.redis.delete(session_id)