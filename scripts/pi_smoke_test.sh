#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
CONFIG="${CONFIG:-configs/rpi4-prod.json}"

"$PYTHON_BIN" -m catcam.cli --config "$CONFIG" verify-camera --frames 60
"$PYTHON_BIN" -m catcam.cli --config "$CONFIG" verify-model
"$PYTHON_BIN" -m catcam.cli --config "$CONFIG" benchmark --frames 180 --detector-mode motion-gated
"$PYTHON_BIN" -m catcam.cli --config "$CONFIG" bootstrap-storage

echo "Pi smoke test completed for $CONFIG"
