# Standard library imports
import asyncio
import json
from datetime import datetime, timezone

# Third-party imports
import ipaddress
from loguru import logger
from pydantic import BaseModel, ConfigDict
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.hazmat.primitives.asymmetric import rsa

# FastAPI imports
from fastapi.requests import Request
from fastapi.security import OAuth2PasswordRequestForm

# App imports
from . import crud, redis_session
from .exceptions import exceptions
from .core.security.password_hasher import PasswordHasher
from .core.security.access_token import AccessTokenService
from .core.security.refresh_token import RefreshTokenService
from .core.security.email_token import EmailTokenManager
from .core.security.google_oauth2 import GoogleOAuth2Client
from .core.form.verify_email_form import verify_email_form
from .tools.rsa_keys.loader import load_public_key


# Shared Core imports
from ...shared.core.async_mail_client import AsyncEmailClient
from .core.settings import (
    get_auth_settings, 
    get_email_verify_settings, 
    get_google_oauth_settings
    )

auth_settings = get_auth_settings()
email_verify_settings = get_email_verify_settings()
google_oauth_settings = get_google_oauth_settings()

# ------------------------------ Functional Business Logic -------------------------

def _get_client_ip(request: Request) -> str:
    """
    클라이언트 IP 주소 추출

    x-forwarded-for, x-real-ip 헤더 우선, 없으면 request.client.host 사용
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            pass  # 유효하지 않은 IP는 무시
    xrip = request.headers.get("x-real-ip")
    if xrip:
        try:
            ipaddress.ip_address(xrip)
            return xrip
        except ValueError:
            pass
    if request.client:
        return request.client.host or ""
    return ""

# -------------------------------- Token Business Logic ---------------------------

password_hasher = PasswordHasher(auth_settings.BCRYPT_ROUNDS)
access_token_service = AccessTokenService("RS256", auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
refresh_token_service = RefreshTokenService(
    expire_days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS,
    store_hashed=auth_settings.REFRESH_TOKEN_STORE_HASHED,
    byte_length=auth_settings.REFRESH_TOKEN_BYTE_LENGTH
)

# ------------------------------------------------------------------------


class IssueTokenResponse(BaseModel):
    """
    토큰 발급 응답 커스텀 클래스
    """
    access_token: AccessTokenService.TokenResponse
    refresh_token: RefreshTokenService.TokenResponse


class _KeyResponse(BaseModel):
    """
    비밀 키 응답 모델
    """
    private_key: rsa.RSAPrivateKey
    kid: str

    model_config = ConfigDict(arbitrary_types_allowed=True)

def get_current_private_key(app) -> _KeyResponse:
    """
    애플리케이션의 비밀 키 및 키 ID 반환
    """

    return _KeyResponse(
        private_key=app.state.rsa_key_rotation.private_key,
        kid=app.state.rsa_key_rotation.current_key_pair.kid
    )

def get_jwt_header_kid(token: str) -> str:
    """
    JWT 토큰 헤더에서 키 ID (kid) 추출
    """
    try:
        headers = AccessTokenService.decode_header(token)
        kid = headers.get("kid")
        if not kid:
            raise exceptions.RefreshSessionNotFoundError("키 ID(kid)가 토큰 헤더에 없습니다.")
        return kid
    except Exception as e:
        logger.error(f"Failed to decode JWT headers: {e}")
        raise


async def revoke_tampered_tokens(
    db: AsyncSession,
    redis: Redis,
    session_id: str = None,
) -> None:
    """
    변조된 토큰 무력화 처리
    
    Description:
        토큰 변조나 탈취가 감지되었을 때 세션을 무효화
        - Redis 세션 삭제
        - DB의 모든 리프레시 토큰 비활성화
    
    Args:
        db: 데이터베이스 세션
        redis: Redis 클라이언트
    """
    session = await redis_session.RedisSession(redis).get(session_id)
    if session:
        refresh_token = session.refresh_token
        await redis_session.RedisSession(redis).delete(session_id)
        await crud.deactivate_refresh_token(db, refresh_token)
    


async def create_auth_user(
    db: AsyncSession,
    user_id: str,
    password: str,
    email: str,
    email_token: str
):
    """
    새로운 인증 사용자 생성

    Description:
        가입 순서:
            Email 인증 완료 -> 사용자 생성
        비밀번호는 해시저장
    """
    existing_email_token = await crud.existing_email_token(
        db,
        token=email_token
    )
    if not existing_email_token:
        raise exceptions.EmailVerificationNotFoundError("이메일 인증 토큰이 유효하지 않습니다.")
    verify_email = await crud.is_email_verified(
        db,
        token=email_token
    )

    if not verify_email:
        raise exceptions.EmailVerificationInvalidTokenError("이메일 인증이 완료되지 않았습니다.")
    
    await crud.update_email_verification_code_as_used(
        db,
        token=email_token
    )

    hashed_password = await password_hasher.hash_password(password)

    new_user = crud.AuthUser(
        user_id=user_id,
        password=hashed_password,
        email=email,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def _issue_token(
    request: Request,
    db: AsyncSession,
    redis: Redis,
    user_uuid: str = None,
) -> IssueTokenResponse:
    """
    액세스 토큰 및 리프래시 토큰 발급

    Description:
        내부 함수로, 토큰 발급 로직을 캡슐화
        DB 작업은 순차 처리(트랜잭션), Redis는 병렬 처리
    """
    # Access Token Generation
    current_private_key = get_current_private_key(request.app)
    private_key = current_private_key.private_key
    kid = current_private_key.kid
    access_token = access_token_service.issue_token(user_uuid, private_key, kid)

    # Refresh Token Generation
    refresh_token = refresh_token_service.create_token(user_uuid=str(user_uuid))
    
    # DB 작업: 순차적으로 처리 (같은 트랜잭션)
    await crud.deactivate_refresh_token(db)
    await crud.issue_refresh_token(
        db,
        user_uuid=user_uuid,
        token=refresh_token,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )
    
    # DB commit과 Redis 저장을 병렬로 처리
    await asyncio.gather(
        db.commit(),
        redis_session.RedisSession(redis).save(
            session_id=refresh_token.session_id,
            session=redis_session.SessionData(
                user_uuid=user_uuid,
                refresh_token=refresh_token.token,
                expires_at=refresh_token.expires_at
            ),
            session_ttl=refresh_token.expires_in
        )
    )

    return IssueTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


async def issue_token_by_login_form(
    request: Request,
    db: AsyncSession,
    redis: Redis,
    form_data: OAuth2PasswordRequestForm
) -> IssueTokenResponse:
    """
    액세스 토큰 발급
    
    아이디 > 비밀번호 순으로 검증하고 발급

    social_mode가 True면 form_data 무시하고 user_uuid로 바로 발급

    @TODO 소셜 로그인 처리 로직 분리
    """
    user = await crud.get_user_by_user_id(db, form_data.username)
    if not user:
        raise exceptions.UserNotFoundError("사용자를 찾을 수 없습니다.")
    
    await password_hasher.verify_password(form_data.password, user.password)

    user_uuid = user.user_uuid

    tokens =  await _issue_token(
        request,
        db,
        redis=redis,
        user_uuid=user_uuid
    )

    return tokens


async def verify_access_token(
    request: Request,
    access_token: str
) -> str:
    """
    액세스 토큰 검증

    Description:
        - 액세스 토큰의 유효성을 검사하고, 필요한 경우 사용자 정보를 반환
    """
    kid = get_jwt_header_kid(access_token)
    public_key = await get_public_key(request.app, kid)

    if not public_key:
        logger.error(f"Public key not found for kid: {kid}")
        raise exceptions.InvalidAccessTokenError("유효한 공개 키를 찾을 수 없습니다.")

    try:
        payload = access_token_service.decode_token(access_token, public_key)
        user_uuid = payload.get("sub")
        return user_uuid
    except Exception as e:
        logger.error(f"Failed to verify access token: {e}")
        raise exceptions.InvalidAccessTokenError("유효하지 않은 액세스 토큰입니다.")


async def rotate_tokens(request: Request, db: AsyncSession, redis: Redis) -> IssueTokenResponse:
    """
    리프래시 토큰으로 액세스 토큰 재발급

    # gRPC 지원하도록 재설계 해야됨.

    description:
        발급 예외처리 과정
        1. 토큰이 DB에 존재하지 않음 -> RefreshTokenNotFound 예외 발생
        2. 토큰이 만료됨 -> InvalidTokenException 예외 발생, 비활성화 처리
        3. 토큰 소유자 불일치 -> InvalidTokenException 예외 발생
    """

    current_private_key = get_current_private_key(request.app)
    private_key = current_private_key.private_key
    kid = current_private_key.kid
    session_id = request.cookies.get("session_id")
    session_info = await redis_session.RedisSession(redis).get(session_id)

    # Redis 내에 session_id가 없는 상태 (탈취 됨, 모든 토큰 무효화 처리)
    if not session_info:
        raise exceptions.RefreshSessionNotFoundError("리프래시 토큰이 유효하지 않습니다.")

    old_refresh_token = request.cookies.get("refresh_token")

    # Redis에 저장된 리프래시 토큰과 요청의 리프래시 토큰이 불일치
    if session_info.refresh_token != old_refresh_token:
        await revoke_tampered_tokens(
            db,
            redis,
            session_id=session_id
        )
        raise exceptions.RefreshSessionMismatchError("리프래시 토큰이 유효하지 않습니다.")

    old_refresh_token_data = await crud.get_refresh_token(db, old_refresh_token)

    # DB 내에 리프래시 토큰이 없는 상태 (탈취 혹은 변조 의심)
    if not old_refresh_token_data:
        await revoke_tampered_tokens(
            db,
            redis,
            session_id=session_id
        )
        raise exceptions.RefreshTokenNotFoundError("리프래시 토큰이 유효하지 않습니다.")
    
    # 리프래시 토큰이 만료된 상태
    now_utc = datetime.now(timezone.utc).timestamp()
    if old_refresh_token_data.expires_at.timestamp() < now_utc:
        await revoke_tampered_tokens(
            db,
            redis,
            session_id=session_id
        )
        raise exceptions.ExpiredRefreshTokenError("리프래시 토큰이 만료되었습니다.")
    
    user_uuid = old_refresh_token_data.user_uuid

    refresh_token = refresh_token_service.create_token(user_uuid=str(user_uuid))
    access_token = access_token_service.issue_token(user_uuid, private_key, kid=kid)

    await crud.issue_refresh_token(
        db,
        user_uuid=user_uuid,
        token=refresh_token,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )
    
    # DB와 Redis 작업을 병렬로 처리하여 성능 개선
    await asyncio.gather(
        db.commit(),
        redis_session.RedisSession(redis).save(
            session_id=refresh_token.session_id,
            session=redis_session.SessionData(
                user_uuid=user_uuid,
                refresh_token=refresh_token.token,
                expires_at=refresh_token.expires_at
            ),
            session_ttl=refresh_token.expires_in
        )
    )

    return IssueTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


async def revoke_token(
    request: Request,
    db: AsyncSession,
    redis: Redis
) -> None:
    """
    토큰 무효화 처리
    """
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    session_id = request.cookies.get("session_id")

    await redis_session.RedisSession(redis).delete(session_id)

    access_token_user_uuid = access_token_service.decode_token_without_validation(access_token).get("sub")
    refresh_token = await crud.get_refresh_token(db, refresh_token)
    refresh_token_user_uuid = refresh_token.user_uuid

    if str(access_token_user_uuid) != str(refresh_token_user_uuid):
        logger.warning("액세스 토큰과 리프래시 토큰의 소유자 정보가 일치하지 않습니다.")
        raise exceptions.InvalidAccessTokenError("토큰의 소유자 정보가 일치하지 않습니다.")

    await crud.deactivate_refresh_token(db, refresh_token.refresh_token)


async def get_public_key(
        db: AsyncSession,
        kid: str
        ) -> dict:
    """
    공개키 조회 후 있으면, 문자열로 반환
    """
    public_key = await crud.get_rsa_public_key(db, kid)
    if not public_key:
        raise exceptions.InvalidAccessTokenError("유효한 공개 키를 찾을 수 없습니다.")
    key_str = await load_public_key(public_key.public_key_path)
    return key_str

# -------------------------- Email Verification Business Logic --------------------

email_token_manager = EmailTokenManager(
    email_verify_settings.VERIFY_TOKEN_EXPIRE_MINUTES,
    email_verify_settings.VERIFY_CODE_LENGTH
)

# ------------------------------------------------------------------------

async def send_email_verification(
    db: AsyncSession,
    redis: Redis,
    smtp: AsyncEmailClient,
    email: str
):
    """
    이메일 인증 토큰 및 코드 발급
    """
    if await crud.existing_email_verified(db, email):
        raise exceptions.EmailAlreadyVerifiedError("이미 인증된 이메일 주소입니다.")

    verify: EmailTokenManager.EmailVerifyResponse = email_token_manager.create_token(email)

    body = verify_email_form(
        code=verify.code,
        expiry=verify.expires_in // 60
    )

    await smtp.send_email(
        to=email,
        subject="이메일 인증 안내 — Hilighting",
        body=body,
        subtype="html"
    )

    redis_value = {
            "email": email,
            "code": verify.code,
            "expires_at": verify.expires_at,
            "created_at": verify.created_at
        }

    await redis.set(
        verify.token, 
        json.dumps(redis_value), 
        ex=verify.expires_in
        )

    await crud.save_email_verification_code(
        db=db,
        email=email,
        token=verify.token,
        code=verify.code,
        expires_at=verify.expires_at
    )

    return verify

async def verify_email_token(
    db: AsyncSession,
    redis: Redis,
    token: str,
    code: str,
) -> None:
    """
    이메일 인증 토큰 및 코드 검증

    예외 혹은 None 반환
    """
    redis_data = await redis.get(token)
    if not redis_data:
        raise exceptions.EmailVerificationInvalidTokenError("이메일 인증 토큰이 유효하지 않거나 만료되었습니다.")

    data = json.loads(redis_data)

    if data.get("code") != code:
        raise exceptions.EmailVerificationCodeMismatchError("이메일 인증 코드가 일치하지 않습니다.")

    # 검증 성공 시, Redis에서 해당 토큰 삭제
    await redis.delete(token)
    await crud.update_email_verification_code_as_verified(db, token)

    return data.get("email")

# -------------------------------- Google Business Logic --------------------------

google_oauth2_client = GoogleOAuth2Client(
    "popup",
    google_oauth_settings.OAUTH_CLIENT_ID,
    google_oauth_settings.OAUTH_CLIENT_SECRET,
)

# ----------------------------- Exception Handling -----------------------

class InvalidGoogleTokenException(Exception):
    """잘못된 구글 인증 토큰 예외"""
    pass

class ProviderAccountAlreadyLinkedException(Exception):
    """OAuth 제공자 계정이 이미 연결된 예외"""
    pass

# ------------------------------------------------------------------------

async def google_login(
       request: Request,
       db: AsyncSession,
       code: str
):
    """
    구글 OAuth2 로그인 처리

    Description:
        구글에서 제공한 code로 사용자 정보 조회
        기존 사용자면 토큰 발급
        신규 사용자면 예외 발생 (추후 회원가입 로직 필요)
    """
    google_user_info = await google_oauth2_client.code_to_token(code)
    if not google_user_info:
       raise InvalidGoogleTokenException("구글 인증에 실패했습니다.")
    
    user = await crud.get_user_by_provider_id(
        db,
        provider="google",
        provider_id=google_user_info.get("id")
    )
    if not user:
        # 신규 사용자 생성 로직 필요
        raise exceptions.UserNotFoundError("구글 계정과 연동된 사용자를 찾을 수 없습니다.")

    tokens =  await _issue_token(
        request,
        db,
        user_uuid=user.user_uuid
    )

    return tokens


async def google_code_to_token(
       code: str
):
    """
    구글 OAuth2 코드로 토큰 및 사용자 정보 조회
    """
    google_user_info = await google_oauth2_client.code_to_token(code)
    if not google_user_info:
       raise exceptions.InvalidGoogleTokenException("구글 인증에 실패했습니다.")
    
    return google_user_info


async def link_oauth_account(
         db: AsyncSession,
         provider: str,
         provider_id: str,
         user_uuid: str,
):
    """
    APP TOKEN으로 OAuth 계정 연결 처리

    Description:
        access token이 유효한 상태여야함.
    """
    # 연동 가능한 계정인지 파악
    if not await crud.validate_provider_id(
        db,
        user_uuid=user_uuid,
        provider=provider,
        provider_id=provider_id
    ):
        raise exceptions.ProviderAccountAlreadyLinkedException("해당 OAuth 계정은 이미 연결되어 있거나 연동할 수 없습니다.")

    # 4. OAuth 계정 연결
    await crud.link_oauth_account(
        db=db,
        user_uuid=user_uuid,
        provider=provider,
        provider_id=provider_id,
    )

    return {
        'status': True
    }
