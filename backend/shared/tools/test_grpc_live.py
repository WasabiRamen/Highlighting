"""
실제 gRPC 서버 통신 테스트
Auth Service가 실행 중이어야 합니다.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from shared.tools.grpc_auth_client import get_grpc_auth_client


async def test_get_public_key():
    """
    공개키 조회 테스트
    """
    print("\n=== Testing GetPublicKey ===")
    client = get_grpc_auth_client()
    
    try:
        # 테스트용 kid (실제 DB에 존재하는 kid 필요)
        kid = "test_key_id"
        result = await client.get_public_key(kid)
        print(f"✓ GetPublicKey succeeded")
        print(f"  Public key length: {len(result)} bytes")
        print(f"  First 50 chars: {result[:50]}...")
        return True
    except Exception as e:
        print(f"✗ GetPublicKey failed: {e}")
        return False


async def test_google_code_to_token():
    """
    Google 토큰 조회 테스트 (실제 코드 없이는 실패 예상)
    """
    print("\n=== Testing GoogleCodeToToken ===")
    client = get_grpc_auth_client()
    
    try:
        result = await client.google_code_to_token(code="test_code")
        print(f"✓ GoogleCodeToToken succeeded")
        print(f"  Result: {result}")
        return True
    except Exception as e:
        print(f"✗ GoogleCodeToToken failed (expected): {e}")
        return False


async def test_connection():
    """
    기본 연결 테스트
    """
    print("\n=== Testing gRPC Connection ===")
    client = get_grpc_auth_client()
    
    print(f"Client initialized:")
    print(f"  Host: {client.host}")
    print(f"  Port: {client.port}")
    
    try:
        # Try to get the client - this will test if we can import the module
        grpc_client = await client._get_client()
        print(f"✓ gRPC client created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create gRPC client: {e}")
        return False


async def main():
    """
    모든 테스트 실행
    """
    print("=" * 60)
    print("gRPC Auth Service Test Suite")
    print("=" * 60)
    print("\nMake sure Auth service is running:")
    print("  uvicorn backend.auth.main:app --reload")
    print("=" * 60)
    
    results = []
    
    # 연결 테스트
    results.append(await test_connection())
    
    # 개별 메서드 테스트
    results.append(await test_get_public_key())
    results.append(await test_google_code_to_token())
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
    else:
        print(f"✗ {total - passed} test(s) failed")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
