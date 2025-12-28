# core/security/google_oauth2.py
import httpx


class GoogleOAuth2Client:
    """
    구글 OAuth2 인증 유틸리티
    """
    def __init__(self, ux_mode: str = "popup", client_id: str = None, secret_key: str = None):
        allow_ux_modes = ["popup", "redirect"]
        if ux_mode not in allow_ux_modes:
            raise GoogleOAuth2Client.UXModeError(f"지원하지 않는 UX 모드입니다. 지원 UX 모드: {allow_ux_modes}")

        if not client_id:
            raise GoogleOAuth2Client.NotFoundClientIdError("구글 OAuth2 클라이언트 ID가 설정되지 않았습니다.")

        if not secret_key:
            raise GoogleOAuth2Client.NotFoundSecretKeyError("구글 OAuth2 비밀 키가 설정되지 않았습니다.")

        self.__TOKEN_URL = "https://oauth2.googleapis.com/token"
        self.__USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.__CLIENT_ID = client_id
        self.__SECRET_KEY = secret_key
        self.__POPUP_REDIRECT_URI = "postmessage"
        self.__UX_MODE = ux_mode


    class UXModeError(Exception):
        """지원하지 않는 UX 모드 예외"""
        pass

    
    class NotFoundSecretKeyError(Exception):
        """구글 OAuth2 비밀 키 미설정 예외"""
        pass


    class NotFoundClientIdError(Exception):
        """구글 OAuth2 클라이언트 ID 미설정 예외"""
        pass

    class TokenRequestError(Exception):
        """구글 OAuth2 토큰 요청 실패 예외"""
        pass


    async def code_to_token(self, code: str, redirect_uri: str = None) -> dict:
        """
        구글 OAuth2 인증 코드로 액세스 토큰 요청
        """
        if self.__UX_MODE == "popup":
            redirect_uri = self.__POPUP_REDIRECT_URI
        elif self.__UX_MODE == "redirect":
            redirect_uri = redirect_uri
        else:
            raise GoogleOAuth2Client.UXModeError("지원하지 않는 UX 모드입니다.")

        try:
            # 타임아웃 및 커넥션 풀 설정으로 성능 개선
            timeout = httpx.Timeout(10.0, connect=5.0)
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            
            async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
                token_response = await client.post(self.__TOKEN_URL, data={
                    "code": code,
                    "client_id": self.__CLIENT_ID,
                    "client_secret": self.__SECRET_KEY,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                })

                if token_response.status_code != 200:
                    raise GoogleOAuth2Client.TokenRequestError("구글 OAuth2 토큰 요청에 실패하였습니다.")
                
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    raise GoogleOAuth2Client.TokenRequestError("구글 액세스 토큰이 반환되지 않았습니다.")
                    
                # 2. 액세스 토큰으로 사용자 정보 요청
                user_response = await client.get(self.__USER_INFO_URL, headers={
                    "Authorization": f"Bearer {access_token}"
                })

                if user_response.status_code != 200:
                    raise GoogleOAuth2Client.TokenRequestError("구글 OAuth2 사용자 정보 요청에 실패하였습니다.")

                return user_response.json()

        except httpx.RequestError as e:
            raise GoogleOAuth2Client.TokenRequestError("구글 OAuth2 요청 중 네트워크 오류가 발생했습니다.") from e

