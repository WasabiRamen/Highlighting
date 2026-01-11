#!/usr/bin/env bash
set -euo pipefail

# Optional venv activation (only if it has uvicorn installed)
if [ -x "venv/bin/python" ]; then
	if "venv/bin/python" -c "import uvicorn" >/dev/null 2>&1; then
		# shellcheck disable=SC1091
		source "venv/bin/activate"
	fi
fi

python -m uvicorn backend.secrets_manager.main:app --host 0.0.0.0 --port 8000