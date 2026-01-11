#!/usr/bin/env bash
set -euo pipefail

# Generate Python gRPC stubs from secrets_manager.proto
#
# Usage:
#   ./backend/secrets_manager/grpc/generate_stubs.sh [OUT_DIR]
#
# Example:
#   ./backend/secrets_manager/grpc/generate_stubs.sh ./clients/python
#
# Output files:
#   secrets_manager_pb2.py
#   secrets_manager_pb2_grpc.py

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROTO_DIR="$ROOT_DIR/backend/secrets_manager/proto"
PROTO_FILE="$PROTO_DIR/secrets_manager.proto"

OUT_DIR="${1:-$ROOT_DIR/backend/secrets_manager/grpc/generated}"
mkdir -p "$OUT_DIR"

python -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$OUT_DIR" \
  --grpc_python_out="$OUT_DIR" \
  "$PROTO_FILE"

# Convenience: make OUT_DIR importable as a package when it lives inside the repo.
if [[ ! -f "$OUT_DIR/__init__.py" ]]; then
  : > "$OUT_DIR/__init__.py"
fi

echo "Generated stubs in: $OUT_DIR"
ls -1 "$OUT_DIR" | grep -E '^secrets_manager_pb2(_grpc)?\.py$' || true
