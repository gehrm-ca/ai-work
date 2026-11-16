#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_PORT=8000
WEB_PORT=3000

# --- prerequisites -----------------------------------------------------------
# Many systems ship only `python3`, and macOS ships an old one, so look for the
# first interpreter that is actually Python 3.12 or newer.
PYTHON=""
for candidate in python3 python python3.13 python3.12; do
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo "Program OS needs Python 3.12 or newer, and none was found on your PATH."
  echo "Install it from https://www.python.org/downloads/ and run 'make demo' again,"
  echo "or use the container preview instead: docker compose up --build"
  exit 1
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Program OS needs Node.js 20.9 or newer (with npm), and none was found on your PATH."
  echo "Install it from https://nodejs.org/ and run 'make demo' again,"
  echo "or use the container preview instead: docker compose up --build"
  exit 1
fi
if ! node -e 'const [a, b] = process.versions.node.split(".").map(Number); process.exit(a > 20 || (a === 20 && b >= 9) ? 0 : 1)'; then
  echo "Program OS needs Node.js 20.9 or newer; found $(node --version)."
  echo "Update it from https://nodejs.org/ and run 'make demo' again."
  exit 1
fi

port_in_use() {
  "$PYTHON" - "$1" <<'PY'
import socket
import sys

with socket.socket() as sock:
    sock.settimeout(0.5)
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
PY
}
for port in "$API_PORT" "$WEB_PORT"; do
  if port_in_use "$port"; then
    echo "Port $port is already in use, so the demo cannot start."
    echo "Stop whatever is using it (another 'make demo' window, perhaps) and try again."
    exit 1
  fi
done

# --- install -----------------------------------------------------------------
if [[ ! -d ".venv" ]]; then
  echo "Creating a local Python environment in .venv ..."
  "$PYTHON" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
echo "Installing Python dependencies (the first run can take a minute) ..."
python -m pip install --quiet --disable-pip-version-check -r requirements.lock
python -m pip install --quiet --disable-pip-version-check --no-deps -e .

if [[ ! -d "web/node_modules" ]]; then
  echo "Installing web dependencies (the first run can take a minute) ..."
  (cd web && npm ci --no-audit --no-fund --loglevel=error)
fi

# --- run ---------------------------------------------------------------------
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

mkdir -p "$ROOT_DIR/var"
PROGRAM_OS_AUDIT_PATH="${PROGRAM_OS_AUDIT_PATH:-$ROOT_DIR/var/audit.jsonl}"
export PROGRAM_OS_AUDIT_PATH
mkdir -p "$(dirname "$PROGRAM_OS_AUDIT_PATH")"

wait_for() {
  # wait_for <url> <seconds>
  python - "$1" "$2" <<'PY'
import sys
import time
import urllib.error
import urllib.request

url, seconds = sys.argv[1], float(sys.argv[2])
deadline = time.monotonic() + seconds
while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                raise SystemExit(0)
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        pass
    time.sleep(0.25)
raise SystemExit(1)
PY
}

echo "Starting the API ..."
uvicorn program_os.api:app --host 127.0.0.1 --port "$API_PORT" >"$ROOT_DIR/var/api.log" 2>&1 &
API_PID=$!
if ! wait_for "http://127.0.0.1:$API_PORT/health" 30; then
  echo "The Program OS API did not start. Last lines of var/api.log:"
  tail -n 15 "$ROOT_DIR/var/api.log" || true
  exit 1
fi

echo "Starting the web UI ..."
(
  cd web
  PROGRAM_OS_API_URL="http://127.0.0.1:$API_PORT" npm run dev -- --hostname 127.0.0.1 --port "$WEB_PORT"
) >"$ROOT_DIR/var/web.log" 2>&1 &
WEB_PID=$!
if ! wait_for "http://127.0.0.1:$WEB_PORT/" 90; then
  echo "The web UI did not start. Last lines of var/web.log:"
  tail -n 15 "$ROOT_DIR/var/web.log" || true
  exit 1
fi

echo
echo "Program OS V2 demo is running."
echo "UI:  http://127.0.0.1:$WEB_PORT"
echo "API: http://127.0.0.1:$API_PORT"
echo
echo "Logs:"
echo "  var/api.log"
echo "  var/web.log"
echo
echo "Press Ctrl-C to stop both services."

wait "$WEB_PID"
