"""
gRPC Auth Client 사용 예시 및 테스트
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from shared.tools.grpc_auth_client import get_grpc_auth_client


async def test_grpc_client():
    """gRPC 클라이언트 테스트"""
    client = get_grpc_auth_client(host="localhost", port=50051)
    
    print("gRPC Auth Client initialized")
    print(f"Host: {client.host}")
    print(f"Port: {client.port}")
    
    # 실제 통신 테스트는 서버가 실행 중일 때 가능
    print("\nTo test actual gRPC calls, make sure:")
    print("1. Auth service is running: uvicorn backend.auth.main:app")
    print("2. gRPC server is started on port 50051")
    print("\nExample usage:")
    print("""
    # 토큰 재발급
    result = await client.rotate_tokens(request, db, redis)
    
    # 사용자 생성
    result = await client.create_auth_user(
        user_id="testuser",
        password="password123",
        email="test@example.com",
        email_token="token"
    )
    
    # OAuth 계정 연결
    result = await client.link_oauth_account(
        provider="google",
        provider_id="google_id",
        user_uuid="user_uuid"
    )
    
    # Google 토큰 조회
    result = await client.google_code_to_token(code="google_code")
    
    # 공개키 조회
    public_key = await client.get_public_key(kid="key_id")
    """)


if __name__ == "__main__":
    asyncio.run(test_grpc_client())
