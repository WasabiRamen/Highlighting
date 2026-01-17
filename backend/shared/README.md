# Highlighting Shared Library

`highlighting-shared`는 Highlighting 프로젝트의 마이크로서비스 아키텍처(MSA) 환경에서 여러 서비스들이 공유하는 로직과 유틸리티를 제공하는 공유 라이브러리입니다.

## 📋 개요

각 마이크로서비스(accounts, auth, news, secrets_manager 등)는 독립적으로 동작하지만, 데이터베이스 연결, gRPC 통신, Redis 세션 관리, 로깅, 메일 발송 등 공통적으로 필요한 기능들이 있습니다.

`highlighting-shared`는 이러한 공통 로직을 한곳에 집중시켜 다음과 같은 이점을 제공합니다:

- **코드 중복 제거**: 공통 기능을 한 번만 작성하고 모든 서비스에서 재사용
- **일관성 유지**: 모든 서비스가 동일한 방식으로 데이터베이스, 인증, 로깅을 처리
- **유지보수 용이**: 공통 기능 변경 시 모든 서비스에 자동 반영
- **버전 관리**: Wheel 패키지로 배포되어 버전 관리 가능

## 📦 포함되는 모듈

```
core/
├── database.py          # 데이터베이스 연결 및 세션 관리
├── logging.py           # 통일된 로깅 설정
├── settings.py          # 공통 설정 관리
├── async_mail_client.py # 비동기 메일 발송 클라이언트
├── cookie_handler.py    # HTTP 쿠키 처리
├── redis.py            # Redis 클라이언트 래퍼
└── rabbitmq.py         # RabbitMQ 연결 관리

grpc/
├── channel.py           # gRPC 채널 관리
├── auth/               # Auth 서비스 gRPC 클라이언트
├── secrets_manager/    # Secrets Manager gRPC 클라이언트
└── ...

tools/
├── decode.py           # 인코딩/디코딩 유틸리티
├── exceptions.py       # 공용 예외 클래스
└── ...
```

## 🔧 패키징 방법

### 1. 자동 버전 설정

기본적으로 버전은 자동으로 생성됩니다 (타임스탬프 + git short SHA):

```bash
./package.sh
```

생성되는 형식: `highlighting_shared-20260117105003+gb06e36d-py3-none-any.whl`

### 2. 수동 버전 지정

특정 버전으로 패키징하려면:

```bash
./package.sh "1.0.0"
```

### 3. 패키징 과정

`package.sh` 스크립트는 다음 작업을 자동으로 수행합니다:

1. **임시 디렉토리 생성**: dist-info, build 등 빌드 산물을 임시 디렉토리에서 관리
2. **Wheel 빌드**: setuptools를 사용해 wheel 파일 생성
3. **정리**: 빌드 산물 정리 및 dist 디렉토리 삭제
4. **배포**: 최종 wheel 파일을 `package/` 디렉토리에 저장

### 4. 결과

패키징 후 `package/` 디렉토리에 설치 가능한 wheel 파일이 생성됩니다:

```bash
package/
└── highlighting_shared-20260117105003+gb06e36d-py3-none-any.whl
```

## 📥 사용법

### 1. 설치

각 마이크로서비스에서 `highlighting-shared`를 설치합니다:

```bash
# 상대 경로로 설치 (로컬 개발 환경)
pip install ../shared/package/highlighting_shared-*.whl

# 또는 wheel 파일을 지정해서 설치
pip install /path/to/highlighting_shared-20260117105003+gb06e36d-py3-none-any.whl
```

### 2. 데이터베이스 연결 사용

```python
from shared.core.database import DatabaseSettings, init_db, get_db

# 데이터베이스 설정 로드
db_settings = DatabaseSettings(
    user="postgres",
    password="password",
    name="app_db",
    host="localhost",
    port=5432
)

# 데이터베이스 초기화
async def startup():
    await init_db(db_settings.async_database_url)

# 세션 사용
async def get_session():
    async with get_db() as db:
        # db 세션 사용
        pass
```

### 3. gRPC 클라이언트 사용

```python
from shared.grpc.auth.clinet import AuthServiceClient

# Auth 서비스 클라이언트 생성
auth_client = AuthServiceClient(channel="localhost:50051")

# gRPC 호출
response = auth_client.verify_token(token="...")
```

### 4. 로깅 사용

```python
from shared.core.logging import get_logger

logger = get_logger(__name__)

logger.info("작업 시작")
logger.error("에러 발생", exc_info=True)
```

### 5. Redis 사용

```python
from shared.core.redis import RedisClient

redis = RedisClient(host="localhost", port=6379)
await redis.set("key", "value")
value = await redis.get("key")
```

### 6. 메일 발송

```python
from shared.core.async_mail_client import AsyncMailClient

mail_client = AsyncMailClient(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    sender_email="sender@example.com",
    sender_password="password"
)

await mail_client.send_email(
    to="recipient@example.com",
    subject="제목",
    body="본문"
)
```

## 🚀 배포 워크플로우

1. **개발**: `backend/shared/` 디렉토리에서 공유 로직 개발
2. **패키징**: `./package.sh` 실행하여 wheel 파일 생성
3. **배포**: 생성된 wheel 파일을 각 서비스에 설치
4. **검증**: 각 서비스에서 정상 작동 확인

## 📝 주의사항

- 공유 라이브러리 변경 후 모든 서비스에 새 버전을 설치해야 합니다
- `package.sh`는 빌드 후 `dist/` 디렉토리를 자동 삭제하므로, 최종 wheel 파일은 `package/` 디렉토리에서만 찾을 수 있습니다
- Wheel 파일명의 형식이 pip에서 인식 가능해야 합니다 (버전 정보 포함)

## 🔗 관련 서비스

- **accounts**: 사용자 계정 관리 서비스
- **auth**: 인증 및 토큰 관리 서비스
- **news**: 뉴스 크롤링 및 API 서비스
- **secrets_manager**: 시크릿 키 관리 서비스
