#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   clean_pycache.sh [--dry-run|-n] [target-dir]
# Examples:
#   clean_pycache.sh           # clean current directory
#   clean_pycache.sh -n .     # list files/dirs that would be removed

TARGET="."
DRY_RUN=0

if [[ "${1:-}" == "-n" || "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  TARGET="${2:-.}"
elif [[ -n "${1:-}" ]]; then
  TARGET="$1"
fi

echo "Cleaning Python caches under: $TARGET"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run — listing matching paths:"
  find "$TARGET" -type d -name '__pycache__' -print
  find "$TARGET" -name '*.py[co]' -print
  find "$TARGET" -type d -name '.pytest_cache' -print
  exit 0
fi

find "$TARGET" -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf || true
find "$TARGET" -name '*.py[co]' -print0 | xargs -0 -r rm -f || true
find "$TARGET" -type d -name '.pytest_cache' -print0 | xargs -0 -r rm -rf || true

echo "Done."
