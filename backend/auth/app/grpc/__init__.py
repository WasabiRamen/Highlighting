"""
gRPC module for Auth Service
"""

from .server import AuthServiceServicer, serve

__all__ = [
    'AuthServiceServicer',
    'serve'
]
