# gRPC Secrets Manager Client
from secrets_manager_pb2_grpc import SecretsManagerServiceStub
from secrets_manager_pb2 import GetSecretByNameRequest


class SecretsClient:
    def __init__(self, stub: SecretsManagerServiceStub):
        self._stub = stub

    def get_secret(self, key_name: str) -> str:
        response = self._stub.GetSecretByName(
            GetSecretByNameRequest(key_name=key_name)
        )
        return response.value
    
    def get_secret_bytes(self, key_name: str) -> bytes:
        response = self._stub.GetSecretByName(
            GetSecretByNameRequest(key_name=key_name)
        )
        return response.value_bytes