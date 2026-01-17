#!/usr/bin/env bash
set -euo pipefail

# Packaging script for highlighting-shared
# Usage:
#   ./package.sh [version]
# If no version is provided, a timestamp + short git SHA is used.
# Outputs:
#   - Only one file: package/highlighting_shared-*.whl

NAME="highlighting-shared"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR"
OUT_DIR="$SCRIPT_DIR/dist"

show_usage() {
	echo "Usage: $(basename "$0") [version]" >&2
	echo "Packages backend/shared and outputs wheel to package/" >&2
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
	show_usage
	exit 0
fi

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
	SHORT_SHA="nosha"
	if command -v git >/dev/null 2>&1; then
		# Resolve repo root and get short SHA if available
		REPO_ROOT="$(git -C "$SCRIPT_DIR/.." rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"
		SHORT_SHA="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "nosha")"
	fi
	# Use PEP 440-compliant version: timestamp + local version for git sha
	# Example: 20260111093810+gabcdef1
	VERSION="$(date -u +%Y%m%d%H%M%S)+g$SHORT_SHA"
fi

mkdir -p "$OUT_DIR"

# Create temporary directory for dist-info and build artifacts
TEMP_DIR="$(mktemp -d)"
trap "rm -rf '$TEMP_DIR'" EXIT

# Verify required paths exist
for path in "$SRC_DIR/__init__.py" "$SRC_DIR/core" "$SRC_DIR/grpc" "$SRC_DIR/tools"; do
	if [[ ! -e "$path" ]]; then
		echo "Missing required path: $path" >&2
		exit 1
	fi
done

echo "Packing (wheel) $NAME → package/"
echo "Temp directory: $TEMP_DIR"

# Build wheel using setuptools; version is provided via env var PACKAGE_VERSION
export PACKAGE_VERSION="$VERSION"

# Ensure build tooling is available
python3 -m pip install --quiet --upgrade pip setuptools wheel >/dev/null

# Build wheel directly to dist directory
python3 "$SCRIPT_DIR/setup.py" bdist_wheel -d "$OUT_DIR"

# Move dist-info and build artifacts to temp directory
for artifact in "$SRC_DIR"/*-info "$SRC_DIR"/build; do
	if [[ -e "$artifact" ]]; then
		mv "$artifact" "$TEMP_DIR/"
	fi
done

echo ""
echo "Built wheels:" 
ls -1 "$OUT_DIR"/*.whl 2>/dev/null || echo "(no wheel found)"

# Get the latest wheel
LATEST_WHL="$(ls -t "$OUT_DIR"/*.whl 2>/dev/null | head -n1 || true)"
if [[ -n "$LATEST_WHL" ]]; then
	# Remove other wheels and any tarballs to keep only one file
	find "$OUT_DIR" -maxdepth 1 -type f -name '*.whl' ! -name "$(basename "$LATEST_WHL")" -exec rm -f {} +
	rm -f "$OUT_DIR"/*.tar.gz
	
	# Copy wheel to package directory with original filename
	PACKAGE_DIR="$SCRIPT_DIR/package"
	mkdir -p "$PACKAGE_DIR"
	WHL_FILENAME="$(basename "$LATEST_WHL")"
	cp "$LATEST_WHL" "$PACKAGE_DIR/$WHL_FILENAME"
	echo "Copied wheel to package directory: $PACKAGE_DIR/$WHL_FILENAME"
	
	# Clean up dist directory
	rm -rf "$OUT_DIR"
	echo "Cleaned dist directory"
else
	echo "No wheel found in $OUT_DIR" >&2
	exit 1
fi

