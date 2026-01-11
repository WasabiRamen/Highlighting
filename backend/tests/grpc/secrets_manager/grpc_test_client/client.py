#!/usr/bin/env python3
"""
gRPC Test Client for Secrets Manager Service

This client provides functions to test all gRPC endpoints:
- CreateSecret / GetSecretByName
- CreateAsymmetricKeyPair / GetAsymmetricKeyPairByKeyName
- CreateSymmetricKey / GetSymmetricKeyByKeyName

Usage:
    python client.py
"""

import sys
import grpc
from pathlib import Path
from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime

# Add the generated stubs to the path
generated_dir = Path(__file__).resolve().parent.parent / "backend" / "secrets_manager" / "grpc" / "generated"
if str(generated_dir) not in sys.path:
    sys.path.insert(0, str(generated_dir))

try:
    import secrets_manager_pb2
    import secrets_manager_pb2_grpc
except ImportError as e:
    print(f"Error importing gRPC stubs: {e}")
    print(f"Please generate stubs first by running: backend/secrets_manager/grpc/generate_stubs.sh")
    sys.exit(1)


class SecretsManagerClient:
    """Client for testing Secrets Manager gRPC service"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the gRPC client
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.address = f"{host}:{port}"
        self.channel = None
        self.stub = None
    
    def connect(self):
        """Establish connection to the gRPC server"""
        print(f"🔗 Connecting to gRPC server at {self.address}...")
        self.channel = grpc.insecure_channel(self.address)
        self.stub = secrets_manager_pb2_grpc.SecretsManagerServiceStub(self.channel)
        print("✅ Connected successfully!")
    
    def close(self):
        """Close the gRPC channel"""
        if self.channel:
            self.channel.close()
            print("👋 Connection closed")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # =====================
    # Secret Operations
    # =====================
    
    def create_secret(self, key_name: str, value: str, key_type: str = "", mk_version: int = 0):
        """Create a new secret
        
        Args:
            key_name: Name of the secret
            value: Secret value (plaintext)
            key_type: Optional key type
            mk_version: Optional master key version
            
        Returns:
            Secret response
        """
        print(f"\n📝 Creating secret: {key_name}")
        request = secrets_manager_pb2.CreateSecretRequest(
            key_name=key_name,
            value=value,
            key_type=key_type,
            mk_version=mk_version
        )
        
        try:
            response = self.stub.CreateSecret(request)
            self._print_secret(response)
            return response
        except grpc.RpcError as e:
            print(f"❌ Error: {e.code()} - {e.details()}")
            raise
    
    def get_secret_by_name(self, key_name: str):
        """Get a secret by name
        
        Args:
            key_name: Name of the secret
            
        Returns:
            Secret response with decrypted value
        """
        print(f"\n🔍 Getting secret: {key_name}")
        request = secrets_manager_pb2.GetSecretByNameRequest(key_name=key_name)
        
        try:
            response = self.stub.GetSecretByName(request)
            self._print_secret(response)
            return response
        except grpc.RpcError as e:
            print(f"❌ Error: {e.code()} - {e.details()}")
            raise
    
    # =====================
    # Asymmetric Key Operations
    # =====================
    
    def create_asymmetric_key_pair(self, key_name: str, key_size: int = 2048, 
                                   key_type: str = "", mk_version: int = 0):
        """Create a new asymmetric key pair (RSA)
        
        Args:
            key_name: Name of the key pair
            key_size: Key size in bits (e.g., 2048, 4096)
            key_type: Optional key type
            mk_version: Optional master key version
            
        Returns:
            AsymmetricKeyPair response
        """
        print(f"\n🔐 Creating asymmetric key pair: {key_name} ({key_size} bits)")
        request = secrets_manager_pb2.CreateAsymmetricKeyPairRequest(
            key_name=key_name,
            key_size=key_size,
            key_type=key_type,
            mk_version=mk_version
        )
        
        try:
            response = self.stub.CreateAsymmetricKeyPair(request)
            self._print_asymmetric_key_pair(response)
            return response
        except grpc.RpcError as e:
            print(f"❌ Error: {e.code()} - {e.details()}")
            raise
    
    def get_asymmetric_key_pair_by_name(self, key_name: str, return_key_type: str = "public"):
        """Get an asymmetric key pair by name
        
        Args:
            key_name: Name of the key pair
            return_key_type: "public" (only public key) or "pair" (both keys)
            
        Returns:
            AsymmetricKeyPair response
        """
        print(f"\n🔍 Getting asymmetric key pair: {key_name} (return_type={return_key_type})")
        request = secrets_manager_pb2.GetAsymmetricKeyPairByKeyNameRequest(
            key_name=key_name,
            return_key_type=return_key_type
        )
        
        try:
            response = self.stub.GetAsymmetricKeyPairByKeyName(request)
            self._print_asymmetric_key_pair(response)
            return response
        except grpc.RpcError as e:
            print(f"❌ Error: {e.code()} - {e.details()}")
            raise
    
    # =====================
    # Symmetric Key Operations
    # =====================
    
    def create_symmetric_key(self, key_name: str, key_size: int = 32, 
                            key_type: str = "", mk_version: int = 0):
        """Create a new symmetric key (AES)
        
        Args:
            key_name: Name of the symmetric key
            key_size: Key size in bytes (e.g., 16, 24, 32 for AES-128/192/256)
            key_type: Optional key type
            mk_version: Optional master key version
            
        Returns:
            SymmetricKey response
        """
        print(f"\n🔑 Creating symmetric key: {key_name} ({key_size} bytes)")
        request = secrets_manager_pb2.CreateSymmetricKeyRequest(
            key_name=key_name,
            key_size=key_size,
            key_type=key_type,
            mk_version=mk_version
        )
        
        try:
            response = self.stub.CreateSymmetricKey(request)
            self._print_symmetric_key(response)
            return response
        except grpc.RpcError as e:
            print(f"❌ Error: {e.code()} - {e.details()}")
            raise
    
    def get_symmetric_key_by_name(self, key_name: str):
        """Get a symmetric key by name
        
        Args:
            key_name: Name of the symmetric key
            
        Returns:
            SymmetricKey response
        """
        print(f"\n🔍 Getting symmetric key: {key_name}")
        request = secrets_manager_pb2.GetSymmetricKeyByKeyNameRequest(key_name=key_name)
        
        try:
            response = self.stub.GetSymmetricKeyByKeyName(request)
            self._print_symmetric_key(response)
            return response
        except grpc.RpcError as e:
            print(f"❌ Error: {e.code()} - {e.details()}")
            raise
    
    # =====================
    # Helper Methods
    # =====================
    
    @staticmethod
    def _format_timestamp(ts: Timestamp) -> str:
        """Format protobuf timestamp to readable string"""
        if ts and ts.seconds:
            dt = datetime.fromtimestamp(ts.seconds)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        return "N/A"
    
    def _print_secret(self, secret):
        """Pretty print a Secret message"""
        print("✅ Secret:")
        print(f"  KID: {secret.kid}")
        print(f"  Key Name: {secret.key_name}")
        print(f"  Key Type: {secret.key_type}")
        print(f"  Value: {secret.value}")
        print(f"  Created At: {self._format_timestamp(secret.created_at)}")
        print(f"  MK Version: {secret.mk_version}")
        print(f"  Is Active: {secret.is_active}")
    
    def _print_asymmetric_key_pair(self, key_pair):
        """Pretty print an AsymmetricKeyPair message"""
        print("✅ Asymmetric Key Pair:")
        print(f"  KID: {key_pair.kid}")
        print(f"  Key Name: {key_pair.key_name}")
        print(f"  Key Type: {key_pair.key_type}")
        print(f"  Public Key: {key_pair.public_key[:100]}..." if len(key_pair.public_key) > 100 else f"  Public Key: {key_pair.public_key}")
        if key_pair.private_key:
            print(f"  Private Key: {key_pair.private_key[:100]}..." if len(key_pair.private_key) > 100 else f"  Private Key: {key_pair.private_key}")
        else:
            print("  Private Key: [Not returned]")
        print(f"  Created At: {self._format_timestamp(key_pair.created_at)}")
        print(f"  MK Version: {key_pair.mk_version}")
        print(f"  Is Active: {key_pair.is_active}")
    
    def _print_symmetric_key(self, key):
        """Pretty print a SymmetricKey message"""
        print("✅ Symmetric Key:")
        print(f"  KID: {key.kid}")
        print(f"  Key Name: {key.key_name}")
        print(f"  Key Type: {key.key_type}")
        print(f"  Key Value (base64): {key.key_value}")
        print(f"  Created At: {self._format_timestamp(key.created_at)}")
        print(f"  MK Version: {key.mk_version}")
        print(f"  Is Active: {key.is_active}")


def run_tests():
    """Run a comprehensive test suite"""
    import time
    
    # Create unique names using timestamp to avoid duplicate key errors
    timestamp = int(time.time())
    secret_name = f"test_password_{timestamp}"
    keypair_name = f"test_rsa_keypair_{timestamp}"
    symkey_name = f"test_aes_key_{timestamp}"
    
    print("=" * 60)
    print("🧪 Secrets Manager gRPC Client - Test Suite")
    print("=" * 60)
    
    with SecretsManagerClient() as client:
        try:
            # Test 1: Create and get a secret
            print("\n" + "=" * 60)
            print("TEST 1: Secret Operations")
            print("=" * 60)
            client.create_secret(
                key_name=secret_name,
                value="SuperSecretPassword123!",
                key_type="password"
            )
            client.get_secret_by_name(secret_name)

            # Create another secret with the same key_name to test deactivation of the previous one
            print("\n-- Creating a second secret with the same key_name to trigger deactivation --")
            client.create_secret(
                key_name=secret_name,
                value="NewSecretValue456$",
                key_type="password"
            )
            client.get_secret_by_name(secret_name)
            
            # Test 2: Create and get an asymmetric key pair
            print("\n" + "=" * 60)
            print("TEST 2: Asymmetric Key Pair Operations")
            print("=" * 60)
            client.create_asymmetric_key_pair(
                key_name=keypair_name,
                key_size=2048,
                key_type="RSA"
            )
            client.get_asymmetric_key_pair_by_name(keypair_name, "public")
            client.get_asymmetric_key_pair_by_name(keypair_name, "pair")
            # Create another asymmetric key pair with the same name to replace the previous one
            print("\n-- Creating a second asymmetric key pair with the same key_name to trigger deactivation --")
            client.create_asymmetric_key_pair(
                key_name=keypair_name,
                key_size=2048,
                key_type="RSA"
            )
            client.get_asymmetric_key_pair_by_name(keypair_name, "public")
            client.get_asymmetric_key_pair_by_name(keypair_name, "pair")
            
            # Test 3: Create and get a symmetric key
            print("\n" + "=" * 60)
            print("TEST 3: Symmetric Key Operations")
            print("=" * 60)
            client.create_symmetric_key(
                key_name=symkey_name,
                key_size=32,  # AES-256
                key_type="AES-256"
            )
            client.get_symmetric_key_by_name(symkey_name)
            # Create another symmetric key with the same name to replace the previous one
            print("\n-- Creating a second symmetric key with the same key_name to trigger deactivation --")
            client.create_symmetric_key(
                key_name=symkey_name,
                key_size=32,  # AES-256
                key_type="AES-256"
            )
            client.get_symmetric_key_by_name(symkey_name)
            
            print("\n" + "=" * 60)
            print("✅ All tests completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


def interactive_mode():
    """Run in interactive mode with menu"""
    print("=" * 60)
    print("🔐 Secrets Manager gRPC Client - Interactive Mode")
    print("=" * 60)
    
    with SecretsManagerClient() as client:
        while True:
            print("\n" + "=" * 60)
            print("Choose an operation:")
            print("  1. Create Secret")
            print("  2. Get Secret by Name")
            print("  3. Create Asymmetric Key Pair")
            print("  4. Get Asymmetric Key Pair by Name")
            print("  5. Create Symmetric Key")
            print("  6. Get Symmetric Key by Name")
            print("  7. Run All Tests")
            print("  0. Exit")
            print("=" * 60)
            
            choice = input("\nEnter your choice: ").strip()
            
            try:
                if choice == "1":
                    key_name = input("Key name: ").strip()
                    value = input("Secret value: ").strip()
                    key_type = input("Key type (optional): ").strip()
                    client.create_secret(key_name, value, key_type)
                    
                elif choice == "2":
                    key_name = input("Key name: ").strip()
                    client.get_secret_by_name(key_name)
                    
                elif choice == "3":
                    key_name = input("Key name: ").strip()
                    key_size = input("Key size (default 2048): ").strip()
                    key_size = int(key_size) if key_size else 2048
                    key_type = input("Key type (optional): ").strip()
                    client.create_asymmetric_key_pair(key_name, key_size, key_type)
                    
                elif choice == "4":
                    key_name = input("Key name: ").strip()
                    return_type = input("Return type (public/pair, default public): ").strip() or "public"
                    client.get_asymmetric_key_pair_by_name(key_name, return_type)
                    
                elif choice == "5":
                    key_name = input("Key name: ").strip()
                    key_size = input("Key size in bytes (default 32): ").strip()
                    key_size = int(key_size) if key_size else 32
                    key_type = input("Key type (optional): ").strip()
                    client.create_symmetric_key(key_name, key_size, key_type)
                    
                elif choice == "6":
                    key_name = input("Key name: ").strip()
                    client.get_symmetric_key_by_name(key_name)
                    
                elif choice == "7":
                    run_tests()
                    
                elif choice == "0":
                    print("Goodbye! 👋")
                    break
                    
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Goodbye! 👋")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Secrets Manager gRPC Test Client")
    parser.add_argument("--host", default="localhost", help="gRPC server host (default: localhost)")
    parser.add_argument("--port", type=int, default=50051, help="gRPC server port (default: 50051)")
    parser.add_argument("--test", action="store_true", help="Run automated tests")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Update default host/port if provided
    if args.host != "localhost" or args.port != 50051:
        SecretsManagerClient.__init__.__defaults__ = (args.host, args.port)
    
    if args.test:
        run_tests()
    elif args.interactive:
        interactive_mode()
    else:
        # Default: run tests
        run_tests()
