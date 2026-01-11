"""gRPC server bootstrap using async DB sessions and request-scoped ContextVar."""

import asyncio
from typing import Optional

import grpc
from loguru import logger

from . import auth_pb2, auth_pb2_grpc
from .context import get_db
from .database import init_db, close_db
from .interceptor import DBSessionInterceptor
from ..core.settings import get_auth_settings, get_database_runtime
from .. import service



"""

CreateAuthUser
LinkOAuthAccount
GoogleCodeToToken
RotateTokens
GetPublicKey


"""




class AuthService(auth_pb2_grpc.AuthServiceServicer):
    def __init__(self, redis_client: Optional[object] = None):
        self.redis_client = redis_client

    async def CreateAuthUser(self, request, context):
        db = get_db()
        try:
            new_user = await service.create_auth_user(
                db=db,
                user_id=request.user_id,
                password=request.password,
                email=request.email,
                email_token=request.email_token,
            )
            return auth_pb2.CreateAuthUserResponse(
                user_uuid=str(new_user.user_uuid),
                user_id=new_user.user_id,
                email=new_user.email,
                is_active=new_user.is_active,
                created_at=str(new_user.created_at),
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            raise

    async def LinkOAuthAccount(self, request, context):
        db = get_db()
        try:
            result = await service.link_oauth_account(
                db=db,
                provider=request.provider,
                provider_id=request.provider_id,
                user_uuid=request.user_uuid,
            )
            return auth_pb2.LinkOAuthAccountResponse(status=result["status"])
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            raise

    async def GoogleCodeToToken(self, request, context):
        try:
            google_user_info = await service.google_code_to_token(code=request.code)
            return auth_pb2.GoogleCodeToTokenResponse(
                provider_id=google_user_info.get("provider_id", ""),
                email=google_user_info.get("email", ""),
                name=google_user_info.get("name", ""),
                picture=google_user_info.get("picture", ""),
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            raise

    async def RotateTokens(self, request, context):
        """Reissue tokens; minimal mock request for shared service compatibility."""
        db = get_db()
        try:
            class MockRequest:
                def __init__(self, cookies, headers, client_ip):
                    self.cookies = cookies
                    self.headers = headers
                    self.client = (client_ip, 0)
                    self.app = None

            mock_request = MockRequest(
                cookies={
                    "session_id": request.session_id,
                    "refresh_token": request.refresh_token,
                },
                headers={"user-agent": request.user_agent},
                client_ip=request.ip_address,
            )

            result = await service.rotate_tokens(
                request=mock_request,
                db=db,
                redis=self.redis_client,
            )

            return auth_pb2.IssueTokenResponse(
                access_token=auth_pb2.TokenData(
                    token=result.access_token.token,
                    expires_at=str(result.access_token.expires_at),
                    expires_in=result.access_token.expires_in,
                ),
                refresh_token=auth_pb2.TokenData(
                    token=result.refresh_token.token,
                    expires_at=str(result.refresh_token.expires_at),
                    expires_in=result.refresh_token.expires_in,
                ),
                session_id=result.refresh_token.session_id,
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            raise

    async def GetPublicKey(self, request, context):
        db = get_db()
        try:
            public_key_str = await service.get_public_key(db=db, kid=request.kid)
            return auth_pb2.GetPublicKeyResponse(public_key=public_key_str)
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            raise


async def serve() -> None:
    """Standalone gRPC server startup using ContextVar-scoped DB sessions."""
    auth_settings = get_auth_settings()
    db_settings = get_database_runtime()

    await init_db(db_settings)

    server = grpc.aio.server(interceptors=[DBSessionInterceptor()])
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)
    bind_addr = f"{getattr(auth_settings, 'GRPC_HOST', '0.0.0.0')}:{getattr(auth_settings, 'GRPC_PORT', 50051)}"
    server.add_insecure_port(bind_addr)

    await server.start()
    logger.info(f"gRPC Server started on {bind_addr}")
    try:
        await server.wait_for_termination()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(serve())
