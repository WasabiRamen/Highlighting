from sqlalchemy import Column, Boolean, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

# Shared imports
from app.shared.core.database import Base

class AuthUser(Base):
    """
    사용자 인증 모델

    Columns:
        user_uuid: UUID, 기본 키로 사용되는 고유 사용자 식별자
        user_id: String, 사용자 아이디
        password: String, 사용자 비밀번호 / 해시값 저장
        email: String, 사용자 이메일 주소
        created_at: DateTime, 계정 생성 시간
        is_active: Boolean, 사용자의 활성화 상태

    Description:
        이 모델은 사용자 인증에 필요한 기본 정보를 저장합니다.
        차후, 비밀번호 재설정 모델을 추가함으로써, 업데이트 시간을 관리 할 예정
    """
    __tablename__ = 'auth_user'

    user_uuid = Column(UUID(as_uuid=True), default=uuid4, primary_key=True, unique=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=False)


class AuthRefreshToken(Base):
    """
    리프래시 토큰 로깅 및 검증용 모델

    Columns:
        refresh_token: String, 기본 키로 사용되는 리프래시 토큰
        user_uuid: UUID, 토큰이 발급된 사용자 식별자
        expires_at: DateTime, 토큰 만료 시간
        created_at: DateTime, 토큰 생성 시간
        user_agent: String, 토큰이 발급된 클라이언트의 사용자 에이전트
        ip_address: String, 토큰이 발급된 클라이언트의 IP 주소
        is_active: Boolean, 토큰 활성화 여부
    """

    __tablename__ = 'auth_refresh_token'

    refresh_token = Column(String, nullable=False, primary_key=True, unique=True)
    user_uuid = Column(UUID(as_uuid=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(String)
    ip_address = Column(String)
    is_active = Column(Boolean, default=True)  # 토큰 활성화 여부 


class AuthOAuthAccount(Base):
    """
    OAuth 계정 - 서버 링크 모델

    Columns:
        oauth_id: String, 기본 키로 사용되는 OAuth 계정 식별자
        user_uuid: UUID, 연결된 사용자 식별자
        provider: String, OAuth 제공자 이름 (예: 'google', 'facebook' 등)
        provider_id: String, OAuth 제공자에서의 사용자 ID
        created_at: DateTime, 계정 연결 생성 시간
        last_login: DateTime, 마지막 로그인 시간
        is_active: Boolean, 계정 링크 활성화 여부
    """

    __tablename__ = 'auth_oauth_account'

    oauth_id = Column(String, nullable=False, primary_key=True, unique=True)
    user_uuid = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String, nullable=False)
    provider_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uq_provider_provider_id"),
    )   


class AuthEmailVerification(Base):
    """
    이메일 인증 코드 모델

    Columns:
        token: String, 기본 키로 사용되는 인증 토큰
        code: String, 이메일 인증 코드
        email: String, 인증 대상 이메일 주소
        expires_at: DateTime, 인증 코드 만료 시간
        created_at: DateTime, 인증 코드 생성 시간
        is_verified: Boolean, 이메일 인증 완료 여부
        is_used: Boolean, 인증 코드 사용 여부

        이메일 인증 완료 -> 인증 코드 사용 순으로,
        사용이 완료되면 재사용 불가함.
    """

    __tablename__ = 'auth_email_verification'

    token = Column(String, nullable=False, primary_key=True)
    code = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_verified = Column(Boolean, default=False)
    is_used = Column(Boolean, default=False)


class RSAKey(Base):
    """
    RSA 키 메타데이터 ORM 모델

    Columns:
        kid: String, 기본 키로 사용되는 키 식별자
        private_key_path: String, RSA 개인키 파일 경로
        public_key_path: String, RSA 공개키 파일 경로
        created_at: DateTime, 키 생성 시간
        expires_at: DateTime, 키 만료 시간
        verify_until: DateTime, 키 검증 유효 기간 (선택적)
    """

    __tablename__ = "rsa_key"

    kid = Column(String, primary_key=True, nullable=False)
    private_key_path = Column(String, nullable=False)
    public_key_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verify_until = Column(DateTime(timezone=True), nullable=True)