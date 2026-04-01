#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this script as your normal user, not root. It will use sudo only for apt packages." >&2
  exit 1
fi

sudo apt update
sudo apt install --yes curl git python3-venv python3-pip python3-picamera2 python3-libcamera ffmpeg

python3 -m venv --clear --system-site-packages .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
bash "$ROOT/scripts/fetch_model_assets.sh"

echo "Pi setup complete in $ROOT"
