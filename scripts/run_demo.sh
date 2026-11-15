#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

command -v python >/dev/null 2>&1 || { echo "python is required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm is required"; exit 1; }

if [[ ! -d ".venv" ]]; then
  python -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -e ".[dev]" >/dev/null

if [[ ! -d "web/node_modules" ]]; then
  (cd web && npm install --no-audit --no-fund)
fi

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${WEB_PID:-}" ]] && kill "$WEB_PID" 2>/dev/null || true
  wait "${API_PID:-}" 2>/dev/null || true
  wait "${WEB_PID:-}" 2>/dev/null || true
  exit "$exit_code"
}
trap cleanup EXIT INT TERM

PROGRAM_OS_AUDIT_PATH="${PROGRAM_OS_AUDIT_PATH:-$ROOT_DIR/var/audit.jsonl}"
export PROGRAM_OS_AUDIT_PATH
mkdir -p "$(dirname "$PROGRAM_OS_AUDIT_PATH")"

uvicorn program_os.api:app --host 127.0.0.1 --port 8000 >"$ROOT_DIR/var/api.log" 2>&1 &
API_PID=$!

python - <<'PY'
import time
import urllib.error
import urllib.request

url = "http://127.0.0.1:8000/health"
for _ in range(60):
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            if response.status == 200:
                break
    except (urllib.error.URLError, TimeoutError):
        time.sleep(0.25)
else:
    raise SystemExit("Program OS API did not become healthy.")
PY

(
  cd web
  PROGRAM_OS_API_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
) >"$ROOT_DIR/var/web.log" 2>&1 &
WEB_PID=$!

echo
echo "Program OS V2 demo is running."
echo "UI:  http://127.0.0.1:3000"
echo "API: http://127.0.0.1:8000"
echo
echo "Logs:"
echo "  var/api.log"
echo "  var/web.log"
echo
echo "Press Ctrl-C to stop both services."

wait "$WEB_PID"
