#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

UNIT_PATH="${UNIT_PATH:-/etc/systemd/system/catcam.service}"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
SERVICE_USER="${SERVICE_USER:-$(id -un)}"
CONFIG_PATH="${CONFIG_PATH:-$ROOT/configs/rpi4-prod.json}"
TMP_UNIT="$(mktemp)"

"$PYTHON_BIN" -m catcam.cli print-systemd-unit \
  --project-root "$ROOT" \
  --service-user "$SERVICE_USER" \
  --config "$CONFIG_PATH" > "$TMP_UNIT"

sudo install -m 0644 "$TMP_UNIT" "$UNIT_PATH"
rm -f "$TMP_UNIT"
sudo systemctl daemon-reload
sudo systemctl enable --now catcam.service
sudo systemctl status catcam.service --no-pager
