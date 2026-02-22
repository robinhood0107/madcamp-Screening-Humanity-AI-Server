#!/usr/bin/env bash
set -euo pipefail

PY_BIN="${PY_BIN:-python3}"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  PY_BIN="python"
fi

export GPT_SOVITS_ROOT="${GPT_SOVITS_ROOT:-/workspace/GPT-SoVITS}"

echo "[files-api] Using Python: ${PY_BIN}"
echo "[files-api] GPT_SOVITS_ROOT=${GPT_SOVITS_ROOT}"

exec "$PY_BIN" -m uvicorn file_scanner_api:app \
  --app-dir /opt/gpt-sovits-automation \
  --host 0.0.0.0 \
  --port 10001
