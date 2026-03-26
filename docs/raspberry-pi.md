# Raspberry Pi Bring-Up

This project now has a Pi-oriented camera smoke path and a `systemd` unit template, but it has not been hardware-validated in this macOS workspace. Use this document on the Pi itself.

## OS Baseline

- Raspberry Pi OS 64-bit, Bullseye or later.
- Do not enable the legacy camera stack.

## System Packages

Install Picamera2 from `apt`, not `pip`, so it stays aligned with the underlying `libcamera` packages:

```bash
sudo apt update
sudo apt install --yes python3-picamera2 python3-libcamera ffmpeg
```

## Project Setup

```bash
git clone <repo-url> /opt/catcam
cd /opt/catcam
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e ".[ml]"
```

## First Smoke Checks

Verify that the Pi camera backend starts and returns frames:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-camera --frames 60
```

Verify that the detector model is readable:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-model
```

Bootstrap the dated storage tree:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json bootstrap-storage
```

## Manual Run

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json run
```

## systemd Service

Copy the unit template and adjust paths if your installation root is not `/opt/catcam`:

```bash
sudo cp deploy/systemd/catcam.service /etc/systemd/system/catcam.service
sudo systemctl daemon-reload
sudo systemctl enable --now catcam.service
sudo systemctl status catcam.service
```

Logs:

```bash
journalctl -u catcam.service -f
```
