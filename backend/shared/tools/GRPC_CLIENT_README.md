# gRPC Auth Client Wrapper

`backend/shared/tools`에서 Auth Service의 gRPC 메서드를 호출하기 위한 클라이언트 래퍼입니다.

## 파일 구조

- **grpc_auth_client.py**: gRPC 클라이언트 래퍼 클래스
- **test_grpc_client.py**: 사용 예시 및 테스트 스크립트

## 사용 방법

### 1. 기본 사용

```python
from backend.shared.tools.grpc_auth_client import get_grpc_auth_client

# 클라이언트 가져오기
client = get_grpc_auth_client(host="localhost", port=50051)

# 사용 후 종료
await client.close()
```

### 2. 토큰 재발급 (rotate_tokens)

```python
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

async def my_function(request: Request, db: AsyncSession, redis: Redis):
    client = get_grpc_auth_client()
    
    result = await client.rotate_tokens(request, db, redis)
    
    print(f"Access Token: {result.access_token.token}")
    print(f"Refresh Token: {result.refresh_token.token}")
    print(f"Session ID: {result.session_id}")
```

### 3. 사용자 생성 (create_auth_user)

```python
result = await client.create_auth_user(
    user_id="testuser",
    password="password123",
    email="test@example.com",
    email_token="verification_token"
)

print(f"User UUID: {result['user_uuid']}")
print(f"Email: {result['email']}")
```

### 4. OAuth 계정 연결 (link_oauth_account)

```python
result = await client.link_oauth_account(
    provider="google",
    provider_id="google_user_id",
    user_uuid="user_uuid_here"
)

print(f"Status: {result['status']}")
```

### 5. Google 토큰 조회 (google_code_to_token)

```python
result = await client.google_code_to_token(code="google_auth_code")

print(f"Provider ID: {result['provider_id']}")
print(f"Email: {result['email']}")
print(f"Name: {result['name']}")
```

### 6. 공개키 조회 (get_public_key)

```python
public_key_str = await client.get_public_key(kid="key_id_here")

print(f"Public Key: {public_key_str}")
```

## 통합된 파일들

### get_token_rotator.py 통합

기존 `get_token_rotator.py`에서 직접 import하던 방식을 gRPC 통신으로 변경했습니다:

### 변경 전:
```python
from app.service.auth.app.service import rotate_tokens, IssueTokenResponse
```

### 변경 후:
```python
from .grpc_auth_client import get_grpc_auth_client, IssueTokenResponse

# 사용
grpc_client = get_grpc_auth_client()
new_tokens = await grpc_client.rotate_tokens(request, db, redis)
```

### decode.py 통합

기존 `decode.py`에서 직접 import하던 방식을 gRPC 통신으로 변경했습니다:

### 변경 전:
```python
from app.service.auth.app.service import get_public_key
```

### 변경 후:
```python
from .grpc_auth_client import get_grpc_auth_client

# 사용
grpc_client = get_grpc_auth_client()
public_key = await grpc_client.get_public_key(kid)
```

## 제공되는 메서드

1. **rotate_tokens** - 토큰 재발급
2. **create_auth_user** - 사용자 생성
3. **link_oauth_account** - OAuth 계정 연결
4. **google_code_to_token** - Google 토큰 조회
5. **get_public_key** - 공개키 조회

## get_token_rotator.py 통합 (삭제)

기존 `get_token_rotator.py`에서 직접 import하던 방식을 gRPC 통신으로 변경했습니다:

### 변경 전:
```python
from app.service.auth.app.service import rotate_tokens, IssueTokenResponse
```

### 변경 후:
```python
from .grpc_auth_client import get_grpc_auth_client, IssueTokenResponse

# 사용
grpc_client = get_grpc_auth_client()
new_tokens = await grpc_client.rotate_tokens(request, db, redis)
```

## 환경 설정

### gRPC 서버 주소 변경

```python
# 다른 호스트/포트 사용
client = get_grpc_auth_client(host="auth-service", port=50051)
```

### 환경 변수로 설정

```python
import os

host = os.getenv("GRPC_AUTH_HOST", "localhost")
port = int(os.getenv("GRPC_AUTH_PORT", "50051"))

client = get_grpc_auth_client(host=host, port=port)
```

## 모델 클래스

### TokenData
```python
class TokenData(BaseModel):
    token: str
    expires_at: str
    expires_in: int
```

### IssueTokenResponse
```python
class IssueTokenResponse(BaseModel):
    access_token: TokenData
    refresh_token: TokenData
    session_id: Optional[str] = None
```

## 테스트

```bash
# 클라이언트 초기화 테스트
python backend/shared/tools/test_grpc_client.py

# Auth Service가 실행 중이어야 실제 gRPC 호출 가능
uvicorn backend.auth.main:app --reload
```

## 주의사항

1. **gRPC 서버 실행**: Auth Service가 실행 중이어야 gRPC 호출이 가능합니다
2. **Proto 파일 생성**: `backend/auth/grpc/generate_proto.sh` 실행 필요
3. **네트워크 연결**: 호스트와 포트가 올바르게 설정되어 있어야 합니다
4. **에러 처리**: gRPC 호출 실패 시 적절한 예외 처리 필요

## 에러 처리 예시

```python
import grpc

try:
    result = await client.rotate_tokens(request, db, redis)
except grpc.RpcError as e:
    print(f"gRPC Error: {e.code()}, {e.details()}")
except Exception as e:
    print(f"Error: {e}")
```

## 장점

1. **서비스 분리**: Auth Service와 다른 서비스 간 느슨한 결합
2. **성능**: HTTP REST API보다 빠른 통신
3. **타입 안정성**: Protocol Buffers를 통한 명확한 인터페이스
4. **확장성**: 마이크로서비스 아키텍처에 적합
