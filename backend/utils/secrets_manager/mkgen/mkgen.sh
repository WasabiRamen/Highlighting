#!/bin/bash
# Usage: ./generate_master_key.sh /secure/path/master.key

MASTER_KEY_PATH=${1:-../keys/master.key}

# Python 스크립트 실행
python3 mkgen.py --path "$MASTER_KEY_PATH"

# 권한 설정: 소유자만 읽기/쓰기
chmod 600 "$MASTER_KEY_PATH"

# 소유자 변경 (필요시)
# chown secretmgr:secretmgr "$MASTER_KEY_PATH"

echo "Master key is ready at $MASTER_KEY_PATH"
