#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Optional venv activation (only if it has uvicorn installed)
if [ -x "venv/bin/python" ]; then
	if "venv/bin/python" -c "import uvicorn" >/dev/null 2>&1; then
		# shellcheck disable=SC1091
		source "venv/bin/activate"
	fi
fi

# Set PYTHONPATH to include backend directory for shared module access
export PYTHONPATH="${SCRIPT_DIR}/..${PYTHONPATH:+:$PYTHONPATH}"

python -m uvicorn main:app --host 0.0.0.0 --port 8000