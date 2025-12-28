# service/accounts/app/models.py

# Third Party imports
from sqlalchemy import Column, Boolean, String
from sqlalchemy.dialects.postgresql import UUID

# Shared imports
from app.shared.core.database import Base


class Account(Base):
    """
    사용자 모델

    Columns:
        user_uuid: UUID, 사용자 식별자
        user_name: String, 사용자 이름
        phone_number: String, 사용자 전화번호
        email: String, 사용자 이메일 주소
        link_provider: String, 사용자 소셜 로그인 제공자
        is_admin: Boolean, 사용자의 관리자 권한 여부
        is_active: Boolean, 사용자의 활성화 상태

    Description:
        이 모델은 애플리케이션의 사용자 정보를 저장합니다.

        UI/UX에 사용 -> 사용자 프로필, 관리자 페이지 등
        Auth 서비스의 user_uuid와 연동됨. (FK)
    """
    __tablename__ = 'account'

    user_uuid = Column(UUID(as_uuid=True), unique=True, primary_key=True)
    user_name = Column(String, nullable=False)                          
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)
    is_admin = Column(Boolean, default=False)
    link_provider = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)