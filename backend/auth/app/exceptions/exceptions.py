# Token Exceptions
# ---------------- Exception 정의 ----------------
class UserNotFoundError(Exception):
    """사용자 없음 예외"""
    pass

class InvalidAccessTokenError(Exception):
    """액세스 토큰이 변조되었거나 유효하지 않음"""
    pass

class InvalidRefreshTokenError(Exception):
    """리프레시 토큰 변조 또는 형식 오류"""
    pass

class ExpiredRefreshTokenError(Exception):
    """리프레시 토큰 만료 (완전 재로그인 필요)"""
    pass

class RefreshSessionMismatchError(Exception):
    """session_id가 Redis와 불일치 (탈취/재사용 의심)"""
    pass

class RefreshSessionNotFoundError(Exception):
    """session_id가 쿠키에 없거나 Redis에 없음"""
    pass

class RefreshTokenNotFoundError(Exception):
    """DB/Redis에서 토큰 기록 없음 (존재하지 않는 토큰)"""
    pass

class RefreshTokenReusedError(Exception):
    """이미 사용된 리프레시 토큰 재사용 시도"""
    pass

class RefreshTokenRevokedError(Exception):
    """폐기(로그아웃 등)된 리프레시 토큰 사용"""
    pass

class RefreshTokenRequiredError(Exception):
    """갱신 요청인데 Refresh Token 없음"""
    pass


# Email Verification Exceptions
# ---------------- Exception 정의 ----------------
class EmailVerificationTokenExpiredError(Exception):
    """이메일 인증 토큰이 만료됨"""
    pass

class EmailVerificationInvalidTokenError(Exception):
    """이메일 인증 토큰이 유효하지 않음"""
    pass

class EmailVerificationCodeMismatchError(Exception):
    """이메일 인증 코드 불일치"""
    pass

class EmailVerificationNotFoundError(Exception):
    """이메일 인증 기록이 없음"""
    pass

class EmailAlreadyVerifiedError(Exception):
    """이미 인증된 이메일 주소"""
    pass

# OAuth Exceptions
# ---------------- Exception 정의 ----------------
class InvalidGoogleTokenException(Exception):
    """구글 인증 토큰이 유효하지 않음"""
    pass
class ProviderAccountAlreadyLinkedException(Exception):
    """OAuth 제공자 계정이 이미 연결되어 있음"""
    pass