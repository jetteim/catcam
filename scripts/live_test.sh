#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/artifacts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/live-test.log"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"

echo "Starting CatCam live test at $(date)" | tee "$LOG_FILE"
"$PYTHON_BIN" -m catcam.cli --config configs/macos-dev.json run --max-frames 900 2>&1 | tee -a "$LOG_FILE"
