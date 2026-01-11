"""
gRPC Auth Service Client Wrapper
공유 모듈에서 Auth Service의 gRPC 메서드를 호출하기 위한 클라이언트
"""
from typing import Dict, Optional
from pydantic import BaseModel
from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


class TokenData(BaseModel):
    """토큰 데이터"""
    token: str
    expires_at: str
    expires_in: int


class IssueTokenResponse(BaseModel):
    """토큰 발급 응답"""
    access_token: TokenData
    refresh_token: TokenData
    session_id: Optional[str] = None


class GrpcAuthClient:
    """
    gRPC Auth Service 클라이언트
    """
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        """
        Initialize gRPC client
        
        Args:
            host: gRPC 서버 호스트
            port: gRPC 서버 포트
        """
        self.host = host
        self.port = port
        self._client = None
    
    async def _get_client(self):
        """Get or create gRPC client instance"""
        if self._client is None:
            try:
                # Import from the auth service grpc module
                from ...auth.grpc import get_auth_client
                self._client = get_auth_client(host=self.host, port=self.port)
            except ImportError as e:
                raise ImportError(f"gRPC auth client module not found: {e}. Make sure proto files are generated.")
        return self._client
    
    async def rotate_tokens(
        self,
        request: Request,
        db: AsyncSession,
        redis: Redis
    ) -> IssueTokenResponse:
        """
        리프래시 토큰으로 액세스 토큰 재발급 (gRPC 호출)
        
        Args:
            request: FastAPI Request
            db: Database session
            redis: Redis client
            
        Returns:
            IssueTokenResponse: 발급된 토큰 정보
        """
        client = await self._get_client()
        
        session_id = request.cookies.get("session_id")
        refresh_token = request.cookies.get("refresh_token")
        user_agent = request.headers.get("user-agent", "")
        
        # Get client IP
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else "unknown"
        
        result = await client.rotate_tokens(
            session_id=session_id,
            refresh_token=refresh_token,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        return IssueTokenResponse(
            access_token=TokenData(**result['access_token']),
            refresh_token=TokenData(**result['refresh_token']),
            session_id=result.get('session_id')
        )
    
    async def create_auth_user(
        self,
        user_id: str,
        password: str,
        email: str,
        email_token: str
    ) -> Dict:
        """
        새로운 인증 사용자 생성 (gRPC 호출)
        
        Args:
            user_id: 사용자 ID
            password: 비밀번호
            email: 이메일
            email_token: 이메일 인증 토큰
            
        Returns:
            Dict: 생성된 사용자 정보
        """
        client = await self._get_client()
        return await client.create_auth_user(
            user_id=user_id,
            password=password,
            email=email,
            email_token=email_token
        )
    
    async def link_oauth_account(
        self,
        provider: str,
        provider_id: str,
        user_uuid: str
    ) -> Dict:
        """
        OAuth 계정 연결 (gRPC 호출)
        
        Args:
            provider: OAuth 제공자
            provider_id: OAuth 제공자의 사용자 ID
            user_uuid: 연결할 사용자 UUID
            
        Returns:
            Dict: 연결 결과
        """
        client = await self._get_client()
        return await client.link_oauth_account(
            provider=provider,
            provider_id=provider_id,
            user_uuid=user_uuid
        )
    
    async def google_code_to_token(self, code: str) -> Dict:
        """
        Google OAuth2 코드로 토큰 및 사용자 정보 조회 (gRPC 호출)
        
        Args:
            code: Google OAuth2 인증 코드
            
        Returns:
            Dict: Google 사용자 정보
        """
        client = await self._get_client()
        return await client.google_code_to_token(code=code)
    
    async def get_public_key(self, kid: str) -> str:
        """
        공개키 조회 (gRPC 호출)
        
        Args:
            kid: 키 ID
            
        Returns:
            str: 공개키 문자열 (PEM 형식)
        """
        client = await self._get_client()
        return await client.get_public_key(kid=kid)
    
    async def close(self):
        """Close gRPC client connection"""
        if self._client:
            await self._client.close()
            self._client = None


# Singleton instance
_grpc_auth_client: Optional[GrpcAuthClient] = None


def get_grpc_auth_client(host: str = "localhost", port: int = 50051) -> GrpcAuthClient:
    """
    Get or create GrpcAuthClient instance
    
    Args:
        host: gRPC 서버 호스트
        port: gRPC 서버 포트
        
    Returns:
        GrpcAuthClient: 클라이언트 인스턴스
    """
    global _grpc_auth_client
    if _grpc_auth_client is None:
        _grpc_auth_client = GrpcAuthClient(host=host, port=port)
    return _grpc_auth_client


async def close_grpc_auth_client():
    """Close global GrpcAuthClient instance"""
    global _grpc_auth_client
    if _grpc_auth_client:
        await _grpc_auth_client.close()
        _grpc_auth_client = None
