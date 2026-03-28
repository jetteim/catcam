#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  "$ROOT/scripts/macos_setup.sh"
fi

PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
CONFIG="${CONFIG:-configs/macos-dev.json}"

"$PYTHON_BIN" -m catcam.cli --config "$CONFIG" run
