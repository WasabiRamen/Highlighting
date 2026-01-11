from sqlalchemy import Column, Boolean, String, DateTime, LargeBinary, Integer
from sqlalchemy.sql import func

# Shared imports
from ...shared.core.database import Base


class SecretsManagerSecret(Base):
    """
    비밀 정보 관리 모델

    Columns:
        key_name: String, 비밀 정보의 이름
        value: String, 비밀 정보의 값
        created_at: DateTime, 비밀 정보 생성 시간
        is_active: Boolean, 비밀 정보의 활성화 상태

    Description:
        이 모델은 애플리케이션에서 사용하는 다양한 비밀 정보를 안전하게 저장하고 관리합니다.
    """
    __tablename__ = 'secrets_manager_secret'

    kid = Column(String, primary_key=True, unique=True)
    key_name = Column(String, nullable=False, index=True)
    key_type = Column(String)
    value = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    mk_version = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


class AsymmetricKeyPair(Base):
    """
    비대칭 키 쌍 관리 모델

    Columns:
        key_uuid: UUID, 기본 키로 사용되는 고유 키 식별자
        key_name: String, 키 쌍의 이름
        public_key: String, 공개 키
        private_key: String, 개인 키
        created_at: DateTime, 키 생성 시간
        is_active: Boolean, 키 활성화 여부

    Description:
        이 모델은 비대칭 암호화에 사용되는 공개 키와 개인 키를 안전하게 저장하고 관리합니다.
    """
    __tablename__ = 'asymmetric_key_pair'

    kid = Column(String, primary_key=True, unique=True)
    key_name = Column(String, nullable=False, index=True)
    key_type = Column(String)
    public_key = Column(LargeBinary, nullable=False)
    private_key = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    mk_version = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


class SymmetricKey(Base):
    """
    대칭 키 관리 모델

    Columns:
        key_uuid: UUID, 기본 키로 사용되는 고유 키 식별자
        key_name: String, 대칭 키의 이름
        key_value: String, 대칭 키 값
        created_at: DateTime, 키 생성 시간
        is_active: Boolean, 키 활성화 여부

    Description:
        이 모델은 대칭 암호화에 사용되는 키를 안전하게 저장하고 관리합니다.
    """
    __tablename__ = 'symmetric_key'

    kid = Column(String, primary_key=True, unique=True)
    key_name = Column(String, nullable=False, index=True)
    key_type = Column(String, nullable=False)
    key_value = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    mk_version = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

