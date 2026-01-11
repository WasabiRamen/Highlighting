#!/bin/bash

# Generate Python code from proto file
# Usage: ./generate_proto.sh

PROTO_DIR="."
OUT_DIR="."

python -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=${OUT_DIR} \
    --grpc_python_out=${OUT_DIR} \
    --pyi_out=${OUT_DIR} \
    ${PROTO_DIR}/auth.proto

# Fix imports to use relative imports
echo "Fixing imports to use relative paths..."
sed -i 's/^import auth_pb2/from . import auth_pb2/g' auth_pb2_grpc.py

echo "Proto files generated successfully!"
echo "Generated files:"
echo "  - auth_pb2.py"
echo "  - auth_pb2_grpc.py"
echo "  - auth_pb2.pyi"
echo "  - Fixed imports for relative paths"
