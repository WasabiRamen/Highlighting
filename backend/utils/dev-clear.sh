#!/usr/bin/env bash
set -euo pipefail

# Development environment cleaner
# Removes per-service Python venvs and Python caches (__pycache__, *.pyc, *.pyo).
# Services: accounts, auth, news/api, secrets_manager
#
# Usage:
#   ./utils/dev-clear.sh [--dry-run] [--yes]
#
# Options:
#   --dry-run   Show what would be deleted without deleting
#   --yes       Do not prompt for confirmation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DRY_RUN=false
ASSUME_YES=false

SERVICES=(
  "accounts"
  "auth"
  "news/api"
  "secrets_manager"
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --yes|-y)
      ASSUME_YES=true
      shift
      ;;
    -h|--help)
      echo "Usage: utils/dev-clear.sh [--dry-run] [--yes]" >&2
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

echo "Target backend dir: $BACKEND_DIR"

venv_paths=()
for svc in "${SERVICES[@]}"; do
  svc_dir="$BACKEND_DIR/$svc"
  venv_dir="$svc_dir/.venv"
  if [[ -d "$venv_dir" ]]; then
    venv_paths+=("$venv_dir")
  fi
done

pycache_paths=$(find "$BACKEND_DIR" -type d -name "__pycache__" -print || true)
pyc_files=$(find "$BACKEND_DIR" \( -name "*.pyc" -o -name "*.pyo" \) -print || true)

echo "Would remove venvs for services: ${SERVICES[*]}"
if [[ ${#venv_paths[@]} -gt 0 ]]; then
  printf 'Venv directories (%d):\n' "${#venv_paths[@]}"
  printf '  %s\n' "${venv_paths[@]}"
else
  echo "No venv directories found."
fi

echo "\nPython cache directories (__pycache__):"
if [[ -n "$pycache_paths" ]]; then
  echo "$pycache_paths" | sed 's/^/  /'
else
  echo "  None found"
fi

echo "\nPython bytecode files (*.pyc, *.pyo):"
if [[ -n "$pyc_files" ]]; then
  echo "$pyc_files" | sed 's/^/  /'
else
  echo "  None found"
fi

if [[ "$DRY_RUN" == true ]]; then
  echo "\nDry-run enabled. No files will be deleted."
  exit 0
fi

if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "\nProceed with deletion? [y/N] " ans
  case "${ans:-N}" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 1;;
  esac
fi

echo "\nRemoving venvs..."
for v in "${venv_paths[@]}"; do
  echo "  rm -rf $v"
  rm -rf "$v"
done

echo "Removing __pycache__ directories..."
if [[ -n "$pycache_paths" ]]; then
  echo "$pycache_paths" | while IFS= read -r d; do
    echo "  rm -rf $d"
    rm -rf "$d"
  done
fi

echo "Removing *.pyc/*.pyo files..."
if [[ -n "$pyc_files" ]]; then
  echo "$pyc_files" | while IFS= read -r f; do
    echo "  rm -f $f"
    rm -f "$f"
  done
fi

echo "\nCleanup complete."