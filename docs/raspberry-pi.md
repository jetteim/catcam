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
git clone https://github.com/jetteim/catcam.git ~/catcam
cd ~/catcam
./scripts/pi_setup.sh
```

Run `./scripts/pi_setup.sh` as your normal user, not `root`. The script uses `sudo` only for `apt`, then creates `.venv` in your checkout so the repo stays writable without `sudo`.
It also enables `--system-site-packages`, which is required because `python3-picamera2` is provided by `apt` rather than `pip`.

## First Smoke Checks

Verify that the Pi camera backend starts and returns frames:

```bash
./scripts/pi_smoke_test.sh
```

The smoke script runs:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-model
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-camera --frames 60
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json benchmark --frames 180 --detector-mode motion-gated
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json bootstrap-storage
```

## Manual Run

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json run
```

## systemd Service

Install a unit rendered for the current checkout path and current user:

```bash
./scripts/pi_install_service.sh
```

Optional overrides:

```bash
SERVICE_USER=catcam CONFIG_PATH="$HOME/catcam/configs/rpi4-prod.json" ./scripts/pi_install_service.sh
```

Logs:

```bash
journalctl -u catcam.service -f
```
