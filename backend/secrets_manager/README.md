# Secrets Manager Service

RDBMS에 저장되는 Secret/키(대칭/비대칭)를 **마스터키로 암복호화**하여 안전하게 관리하고, 애플리케이션은 **gRPC로 조회/생성**할 수 있게 하는 서비스입니다.

## 1) 최초 가동 시: 마스터키 생성

서버는 시작 시 `MASTER_KEY_PATH`에 지정된 파일에서 마스터키를 읽어옵니다. 기본값은 [backend/secrets_manager/.env.dev](backend/secrets_manager/.env.dev)에 설정된 `keys/master.key` 입니다.

- 마스터키 생성(최초 1회)
	- `python mkgen/mkgen.py --path keys/master.key`

마스터키 파일은 JSON이며, `key`는 **AES-256(32바이트) 키를 hex 문자열로 저장**합니다.

중요:
- 마스터키를 **재생성/덮어쓰기**하면 기존에 DB에 저장된 값들을 복호화할 수 없게 됩니다.
- 운영 환경에서는 파일로 관리하기보다 KMS/Secret Manager 등 외부 비밀관리 시스템을 사용하는 것을 권장합니다.

## 2) 어떤 기능이 있는가?

### gRPC API (secrets_manager.v1.SecretsManagerService)

- Secret
	- `CreateSecret`: Secret 생성
	- `GetSecretByName`: Secret 조회(복호화된 값 반환)

- Asymmetric Key Pair
	- `CreateAsymmetricKeyPair`: 비대칭 키페어 생성
	- `GetAsymmetricKeyPairByKeyName`: 키페어 조회(`return_key_type`에 따라 public 또는 pair)

- Symmetric Key
	- `CreateSymmetricKey`: 대칭키 생성
	- `GetSymmetricKeyByKeyName`: 대칭키 조회

### HTTP 엔드포인트(운영 편의)

- `/health`: HTTP 헬스체크
- `/grpc-health`: gRPC 헬스체크(내부적으로 gRPC Health 서비스 호출)
- `/metrics`: Prometheus metrics

## 3) 가동 방법

### 3-1. Postgres 실행

`docker-compose.yml`에는 Postgres만 포함되어 있습니다.

- `docker compose up -d`

기본 포트: `5432` (환경 설정은 [backend/secrets_manager/.env.dev](backend/secrets_manager/.env.dev) 참고)

### 3-2. Python 의존성 설치

- `python -m venv venv && source venv/bin/activate`
- `pip install -r requirements.txt`

### 3-3. 환경변수 설정

- 개발용 기본 파일: [backend/secrets_manager/.env.dev](backend/secrets_manager/.env.dev)
- 예시 템플릿: [backend/secrets_manager/.env.example](backend/secrets_manager/.env.example)

### 3-4. 마스터키 생성(최초 1회)

- `python mkgen/mkgen.py --path keys/master.key`

### 3-5. 서버 실행

FastAPI 실행과 함께 gRPC 서버도 같이 올라옵니다.

- `./service_start.sh`

기본 설정:
- HTTP: `0.0.0.0:8000` (스크립트 기준)
- gRPC: `0.0.0.0:50051` (기본값, 필요 시 `GRPC_HOST`/`GRPC_PORT`로 변경)

### 3-6. gRPC 테스트 클라이언트 실행

- `python grpc_test_client/client.py`
- 대화형: `python grpc_test_client/client.py --interactive`

프로토콜 변경 후 stub 재생성:
- `./backend/secrets_manager/grpc/generate_stubs.sh`

## 4) 유의사항

- 마스터키 파일(`keys/master.key`)은 **절대 커밋하지 마세요**. 운영 환경에서는 KMS/Secret Manager 등 사용 권장.
- 마스터키를 교체/재발급하면 기존 데이터 복호화에 영향을 줍니다(덮어쓰기 금지, 키 로테이션/마이그레이션 전략 필요).
- DB에는 `key_name`에 유니크 제약이 있습니다. 같은 이름으로 `Create*`를 반복 호출하면 중복 오류가 날 수 있습니다.
- gRPC 포트는 기본 `50051`이며, 방화벽/보안그룹에서 포트 오픈 여부를 확인하세요.

---

이 문서는 GitHub Copilot (GPT-5.2)가 작성했습니다.