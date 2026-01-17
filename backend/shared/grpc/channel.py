# gRPC 채널 Tools

import grpc
from fastapi import FastAPI

def get_grpc_channel(app: FastAPI) -> grpc.Channel:
    if "grpc_channel" not in app.state:
        app.state.grpc_channel = grpc.insecure_channel("secrets-manager:50051")
    return app.state.grpc_channel
