#!/bin/bash
# Usage: ./mkgen.sh /secure/path/master.key
set -euo pipefail

# 스크립트 위치 기준으로 경로 설정 (어디서 실행하든 동작)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MASTER_KEY_PATH="${1:-$SCRIPT_DIR/../keys/master.key}"

# 키 파일 디렉토리 생성
mkdir -p "$(dirname "$MASTER_KEY_PATH")"

# Python 스크립트 실행 (스크립트 상대 경로)
python3 "$SCRIPT_DIR/mkgen.py" --path "$MASTER_KEY_PATH"

# 권한 설정: 소유자만 읽기/쓰기
chmod 600 "$MASTER_KEY_PATH"

# 소유자 변경 (필요시)
# chown secretmgr:secretmgr "$MASTER_KEY_PATH"

echo "Master key is ready at $MASTER_KEY_PATH"
