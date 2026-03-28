#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  "$ROOT/scripts/macos_setup.sh"
fi

PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
CONFIG="${CONFIG:-configs/macos-dev.json}"
LOG_DIR="${LOG_DIR:-$ROOT/artifacts}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/macos-quickstart.log}"
DISPLAY_FLAG="${DISPLAY_FLAG:-0}"
MAX_FRAMES="${MAX_FRAMES:-}"

mkdir -p "$LOG_DIR"

CMD=("$PYTHON_BIN" -m catcam.cli --config "$CONFIG" run)
if [[ "$DISPLAY_FLAG" == "1" ]]; then
  CMD+=(--display)
fi
if [[ -n "$MAX_FRAMES" ]]; then
  CMD+=(--max-frames "$MAX_FRAMES")
fi

echo "Starting macOS quickstart at $(date)" | tee "$LOG_FILE"
echo "Command: ${CMD[*]}" | tee -a "$LOG_FILE"
"${CMD[@]}" 2>&1 | tee -a "$LOG_FILE"
