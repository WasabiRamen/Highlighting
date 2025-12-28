from fastapi.requests import Request
from aiosmtplib import SMTP
from pydantic import BaseModel
from email.message import EmailMessage
from loguru import logger

class AsyncEmailClient:
    """기본 비동기 SMTP 메일러"""
    class EmailClientConfig(BaseModel):
        smtp_host: str
        smtp_port: int
        username: str
        password: str
        from_email: str
        use_tls: bool = True


    def __init__(self, setting: EmailClientConfig):
        self.smtp_host = setting.smtp_host
        self.smtp_port = setting.smtp_port
        self.username = setting.username
        self.password = setting.password
        self.from_email = setting.from_email
        self.use_tls = setting.use_tls

    async def connect(self):
        self.smtp = SMTP(hostname=self.smtp_host, port=self.smtp_port, start_tls=self.use_tls)
        await self.smtp.connect()
        await self.smtp.login(self.username, self.password)

        logger.info(f"SMTP Successfully connected : {self.smtp_host}")

    async def disconnect(self):
        if self.smtp:
            logger.info(f"SMTP Successfully disconnected : {self.smtp_host}")
            await self.smtp.quit()

    async def send_email(self, to: str, subject: str, body: str, subtype="plain"):
        """
        이메일 전송
        
        Note: lifespan에서 이미 connect()가 호출되므로 체크 불필요
        """
        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body, subtype=subtype)

        await self.smtp.send_message(msg)


async def get_smtp_client(request: Request) -> AsyncEmailClient:
    """
    FastAPI Request에서 AsyncEmailClient 가져오기
    - app.state.smtp에 이미 초기화되어 있다면 그대로 반환
    - 없으면 예외 발생 또는 초기화 처리 가능
    """
    smtp_client: AsyncEmailClient | None = getattr(request.app.state, "smtp", None)
    
    if smtp_client is None:
        raise RuntimeError("SMTP client is not initialized in app.state.smtp")
    
    # 연결 확인 후 필요하면 connect
    if not getattr(smtp_client, "smtp", None):
        await smtp_client.connect()
    
    return smtp_client