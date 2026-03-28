#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

sudo apt update
sudo apt install --yes git python3-venv python3-pip python3-picamera2 python3-libcamera ffmpeg

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[ml]"

echo "Pi setup complete in $ROOT"
