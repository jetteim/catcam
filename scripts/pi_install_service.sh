#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

UNIT_PATH="${UNIT_PATH:-/etc/systemd/system/catcam.service}"

sudo cp deploy/systemd/catcam.service "$UNIT_PATH"
sudo systemctl daemon-reload
sudo systemctl enable --now catcam.service
sudo systemctl status catcam.service --no-pager
