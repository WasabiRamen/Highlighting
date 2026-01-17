#!/usr/bin/env bash
set -euo pipefail

# Development environment initializer (moved to backend/utils)
# Creates per-service Python venvs and installs requirements.
# Services: accounts, auth, news/api, secrets_manager
#
# Usage:
#   ./utils/dev-init.sh [--recreate] [--skip-install] [--python PYTHON]
#
# Options:
#   --recreate       Remove existing venvs before creating new ones
#   --skip-install   Create venvs but skip installing requirements
#   --python         Python interpreter to use (default: python3)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Backend root is the parent directory of utils
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="python3"
RECREATE=false
SKIP_INSTALL=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --recreate)
      RECREATE=true
      shift
      ;;
    --skip-install)
      SKIP_INSTALL=true
      shift
      ;;
    --python)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --python" >&2
        exit 1
      fi
      PYTHON="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: utils/dev-init.sh [--recreate] [--skip-install] [--python PYTHON]" >&2
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

SERVICES=(
  "accounts"
  "auth"
  "news/api"
  "secrets_manager"
)

echo "Using Python: $PYTHON"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Error: Python interpreter '$PYTHON' not found in PATH" >&2
  exit 1
fi

create_and_setup_venv() {
  local service_rel="$1"
  local service_dir="$BACKEND_DIR/$service_rel"
  local venv_dir="$service_dir/venv"
  local req_file="$service_dir/requirements.txt"

  if [[ ! -d "$service_dir" ]]; then
    echo "[SKIP] Service directory not found: $service_rel" >&2
    return 0
  fi

  if [[ "$RECREATE" == true && -d "$venv_dir" ]]; then
    echo "[CLEAN] Removing existing venv: $service_rel/venv"
    rm -rf "$venv_dir"
  fi

  if [[ ! -d "$venv_dir" ]]; then
    echo "[CREATE] venv for $service_rel"
    "$PYTHON" -m venv "$venv_dir"
  else
    echo "[EXISTS] venv already present for $service_rel"
  fi

  # Activate venv
  # shellcheck disable=SC1091
  source "$venv_dir/bin/activate"

  python -V
  python -m pip install --upgrade pip

  if [[ "$SKIP_INSTALL" == true ]]; then
    echo "[SKIP] Install requirements for $service_rel"
    deactivate
    return 0
  fi

  if [[ -f "$req_file" ]]; then
    echo "[INSTALL] $service_rel requirements"
    python -m pip install -r "$req_file"
  else
    echo "[WARN] requirements.txt not found for $service_rel, skipping install" >&2
  fi

  deactivate
}

for svc in "${SERVICES[@]}"; do
  create_and_setup_venv "$svc"
done

echo "All done. Venvs created under each service at venv"
