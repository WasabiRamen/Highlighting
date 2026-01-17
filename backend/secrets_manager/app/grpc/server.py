import asyncio
import os
import sys
from datetime import timezone
from pathlib import Path
from typing import Optional, Tuple
import base64

import grpc
from fastapi import FastAPI
from google.protobuf.timestamp_pb2 import Timestamp
from loguru import logger

from grpc_health.v1 import health as grpc_health
from grpc_health.v1 import health_pb2 as grpc_health_pb2
from grpc_health.v1 import health_pb2_grpc as grpc_health_pb2_grpc

from .. import service as sm_service
from ..tools.mk import read_master_key
from shared.core.database import DatabaseSettings, init_db, close_db, get_db


def _datetime_to_timestamp(dt) -> Timestamp:
    ts = Timestamp()
    if dt is None:
        return ts
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ts.FromDatetime(dt)
    return ts


def _ensure_proto_generated() -> Tuple[object, object]:
    """Load *_pb2 and *_pb2_grpc modules for secrets_manager.proto.

    This server expects pre-generated stubs at backend/secrets_manager/grpc/generated.
    """

    generated_dir = Path(__file__).resolve().parent / "generated"
    pb2_path = generated_dir / "secrets_manager_pb2.py"
    pb2_grpc_path = generated_dir / "secrets_manager_pb2_grpc.py"

    if not (pb2_path.exists() and pb2_grpc_path.exists()):
        raise RuntimeError(
            "gRPC stubs not found. Run: backend/secrets_manager/grpc/generate_stubs.sh\n"
            f"Expected: {pb2_path} and {pb2_grpc_path}"
        )

    gen_dir_str = str(generated_dir)
    if gen_dir_str not in sys.path:
        sys.path.insert(0, gen_dir_str)

    try:
        import secrets_manager_pb2 as pb2  # type: ignore
        import secrets_manager_pb2_grpc as pb2_grpc  # type: ignore
        return pb2, pb2_grpc
    except Exception as e:
        raise RuntimeError("Failed to import generated gRPC stubs") from e


class _SecretsManagerGrpcServicer:
    """gRPC servicer that delegates to backend/secrets_manager/service.py."""

    def __init__(self, master_key: bytes):
        self._master_key = master_key
        self._pb2, self._pb2_grpc = _ensure_proto_generated()

    def add_to_server(self, server: grpc.aio.Server) -> None:
        # Dynamically create a concrete Servicer implementation class that matches generated base.
        pb2 = self._pb2
        pb2_grpc = self._pb2_grpc

        master_key = self._master_key

        class Servicer(pb2_grpc.SecretsManagerServiceServicer):
            async def CreateSecret(self, request, context):
                mk = master_key
                if not mk:
                    await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Master key not loaded")

                mk_version = int(request.mk_version) if request.mk_version else 1

                try:
                    async for db in get_db():
                        result = await sm_service.create_secrets_key(
                            db=db,
                            key_name=request.key_name,
                            value=request.value.encode("utf-8"),
                            mk=mk,
                            mk_version=mk_version,
                            key_type=request.key_type or None,
                        )
                        break

                    return pb2.Secret(
                        kid=result.get("kid", ""),
                        key_name=result.get("key_name", ""),
                        key_type=result.get("key_type", "") or "",
                        # Do not return ciphertext; return plaintext that client sent.
                        value=request.value,
                        created_at=_datetime_to_timestamp(result.get("created_at")),
                        mk_version=int(result.get("mk_version") or mk_version),
                        is_active=bool(result.get("is_active", True)),
                    )
                except Exception as e:
                    logger.exception("CreateSecret failed")
                    await context.abort(grpc.StatusCode.INTERNAL, str(e))

            async def GetSecretByName(self, request, context):
                mk = master_key
                if not mk:
                    await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Master key not loaded")

                try:
                    async for db in get_db():
                        result = await sm_service.get_secret_by_name(db=db, key_name=request.key_name, mk=mk)
                        break

                    return pb2.Secret(
                        kid=result.get("kid", ""),
                        key_name=result.get("key_name", ""),
                        key_type=result.get("key_type", "") or "",
                        value=(result.get("value") or b"").decode("utf-8"),
                        created_at=_datetime_to_timestamp(result.get("created_at")),
                        mk_version=int(result.get("mk_version") or 1),
                        is_active=bool(result.get("is_active", True)),
                    )
                except sm_service.SecretNotFoundError as e:
                    await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
                except sm_service.DecryptionError as e:
                    await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
                except UnicodeDecodeError:
                    await context.abort(grpc.StatusCode.DATA_LOSS, "Stored secret is not valid UTF-8")
                except Exception as e:
                    logger.exception("GetSecretByName failed")
                    await context.abort(grpc.StatusCode.INTERNAL, str(e))

            async def CreateAsymmetricKeyPair(self, request, context):
                mk = master_key
                if not mk:
                    await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Master key not loaded")

                mk_version = int(request.mk_version) if request.mk_version else 1

                try:
                    async for db in get_db():
                        result = await sm_service.create_asymmetric_key_pair(
                            db=db,
                            key_size=int(request.key_size),
                            key_name=request.key_name,
                            mk=mk,
                            mk_version=mk_version,
                            key_type=request.key_type or None,
                        )

                        # Always return plaintext to clients (string fields).
                        # Fetch decrypted keys via the read path.
                        decrypted = await sm_service.get_asymmetric_key_pair_by_key_name(
                            db=db,
                            key_name=request.key_name,
                            mk=mk,
                            return_key_type="pair",
                        )
                        break

                    return pb2.AsymmetricKeyPair(
                        kid=result.get("kid", ""),
                        key_name=result.get("key_name", ""),
                        key_type=result.get("key_type", "") or "",
                        public_key=(decrypted.get("public_key") or b"").decode("utf-8"),
                        private_key=(decrypted.get("private_key") or b"").decode("utf-8"),
                        created_at=_datetime_to_timestamp(result.get("created_at")),
                        mk_version=int(result.get("mk_version") or mk_version),
                        is_active=bool(result.get("is_active", True)),
                    )
                except Exception as e:
                    logger.exception("CreateAsymmetricKeyPair failed")
                    await context.abort(grpc.StatusCode.INTERNAL, str(e))

            async def GetAsymmetricKeyPairByKeyName(self, request, context):
                mk = master_key
                if not mk:
                    await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Master key not loaded")

                return_key_type = request.return_key_type or "public"

                try:
                    async for db in get_db():
                        result = await sm_service.get_asymmetric_key_pair_by_key_name(
                            db=db,
                            key_name=request.key_name,
                            mk=mk,
                            return_key_type=return_key_type,
                        )
                        break

                    return pb2.AsymmetricKeyPair(
                        kid=result.get("kid", ""),
                        key_name=result.get("key_name", ""),
                        key_type=result.get("key_type", "") or "",
                        public_key=(result.get("public_key") or b"").decode("utf-8"),
                        private_key=(result.get("private_key") or b"").decode("utf-8") if result.get("private_key") else "",
                        created_at=_datetime_to_timestamp(result.get("created_at")),
                        mk_version=int(result.get("mk_version") or 1),
                        is_active=bool(result.get("is_active", True)),
                    )
                except sm_service.SecretNotFoundError as e:
                    await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
                except sm_service.DecryptionError as e:
                    await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
                except UnicodeDecodeError:
                    await context.abort(grpc.StatusCode.DATA_LOSS, "Stored asymmetric key is not valid UTF-8 PEM")
                except Exception as e:
                    logger.exception("GetAsymmetricKeyPairByKeyName failed")
                    await context.abort(grpc.StatusCode.INTERNAL, str(e))

            async def CreateSymmetricKey(self, request, context):
                mk = master_key
                if not mk:
                    await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Master key not loaded")

                mk_version = int(request.mk_version) if request.mk_version else 1

                try:
                    async for db in get_db():
                        result = await sm_service.create_symmetric_key(
                            db=db,
                            key_size=int(request.key_size),
                            key_name=request.key_name,
                            mk=mk,
                            mk_version=mk_version,
                            key_type=request.key_type or None,
                        )

                        # Always return plaintext to clients (string fields).
                        decrypted = await sm_service.get_symmetric_key_by_key_name(
                            db=db,
                            key_name=request.key_name,
                            mk=mk,
                        )
                        break

                    return pb2.SymmetricKey(
                        kid=result.get("kid", ""),
                        key_name=result.get("key_name", ""),
                        key_type=result.get("key_type", "") or "",
                        key_value=base64.b64encode(decrypted.get("key_value") or b"").decode("ascii"),
                        created_at=_datetime_to_timestamp(result.get("created_at")),
                        mk_version=int(result.get("mk_version") or mk_version),
                        is_active=bool(result.get("is_active", True)),
                    )
                except Exception as e:
                    logger.exception("CreateSymmetricKey failed")
                    await context.abort(grpc.StatusCode.INTERNAL, str(e))

            async def GetSymmetricKeyByKeyName(self, request, context):
                mk = master_key
                if not mk:
                    await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Master key not loaded")

                try:
                    async for db in get_db():
                        result = await sm_service.get_symmetric_key_by_key_name(db=db, key_name=request.key_name, mk=mk)
                        break

                    return pb2.SymmetricKey(
                        kid=result.get("kid", ""),
                        key_name=result.get("key_name", ""),
                        key_type=result.get("key_type", "") or "",
                        key_value=base64.b64encode(result.get("key_value") or b"").decode("ascii"),
                        created_at=_datetime_to_timestamp(result.get("created_at")),
                        mk_version=int(result.get("mk_version") or 1),
                        is_active=bool(result.get("is_active", True)),
                    )
                except sm_service.SecretNotFoundError as e:
                    await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
                except sm_service.DecryptionError as e:
                    await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
                except Exception as e:
                    logger.exception("GetSymmetricKeyByKeyName failed")
                    await context.abort(grpc.StatusCode.INTERNAL, str(e))

        pb2_grpc.add_SecretsManagerServiceServicer_to_server(Servicer(), server)


async def start_grpc_server(
    app: FastAPI,
    *,
    database_settings: DatabaseSettings,
    master_key_path: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> grpc.aio.Server:
    grpc_host = host or os.getenv("GRPC_HOST", "0.0.0.0")
    grpc_port = port or int(os.getenv("GRPC_PORT", "50051"))

    # gRPC uses its own DB engine/sessionmaker (globals in shared.core.database)
    await init_db(database_settings, app=None)
    logger.info("[gRPC][Database] Database connection initialized")

    # gRPC uses its own master key instance loaded from file (same method as FastAPI)
    master_key = await read_master_key(master_key_path)
    logger.info("[gRPC][Security] Master key loaded from {}", master_key_path)

    server = grpc.aio.server()

    # gRPC standard health check service
    health_servicer = grpc_health.HealthServicer()
    grpc_health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    servicer = _SecretsManagerGrpcServicer(master_key)
    servicer.add_to_server(server)

    bind_addr = f"{grpc_host}:{grpc_port}"
    server.add_insecure_port(bind_addr)

    # Report health for overall server and specific service
    health_servicer.set("", grpc_health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set(
        "secrets_manager.v1.SecretsManagerService",
        grpc_health_pb2.HealthCheckResponse.SERVING,
    )
    app.state.grpc_health_servicer = health_servicer

    await server.start()
    logger.info("[gRPC] Server started on {}", bind_addr)

    # Keep a background task to observe termination.
    app.state.grpc_serve_task = asyncio.create_task(server.wait_for_termination())

    return server


async def stop_grpc_server(app: FastAPI, server: grpc.aio.Server, *, grace: Optional[float] = None) -> None:
    grpc_grace = grace or float(os.getenv("GRPC_SHUTDOWN_GRACE", "5.0"))

    try:
        health_servicer = getattr(app.state, "grpc_health_servicer", None)
        if health_servicer is not None:
            health_servicer.set("", grpc_health_pb2.HealthCheckResponse.NOT_SERVING)
            health_servicer.set(
                "secrets_manager.v1.SecretsManagerService",
                grpc_health_pb2.HealthCheckResponse.NOT_SERVING,
            )
        await server.stop(grpc_grace)
        logger.info("[gRPC] Server stopped")
    finally:
        serve_task = getattr(app.state, "grpc_serve_task", None)
        if serve_task is not None and not serve_task.done():
            serve_task.cancel()
            try:
                await serve_task
            except asyncio.CancelledError:
                pass

        # Close gRPC DB engine (globals in shared.core.database)
        await close_db(app=None)
        logger.info("[gRPC][Database] Database connection closed")
