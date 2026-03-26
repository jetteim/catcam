# CatCam

Offline event-triggered video capture for cat or baby movement, with macOS development first and Raspberry Pi 4 deployment next.

## Quick Start

### macOS

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e ".[ml]"
```

Smoke checks:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json verify-model
.venv/bin/python -m catcam.cli --config configs/macos-dev.json verify-camera --frames 30
```

Live run:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json run
```

### Raspberry Pi

Pi bring-up is documented in [docs/raspberry-pi.md](docs/raspberry-pi.md).

Minimal smoke sequence on the Pi:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-camera --frames 60
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-model
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json bootstrap-storage
```

## Brand-New Pi Setup

Use this on a fresh Raspberry Pi OS 64-bit install.

1. Install system packages:

```bash
sudo apt update
sudo apt install --yes git python3-venv python3-pip python3-picamera2 python3-libcamera ffmpeg
```

2. Clone the repo and create the virtual environment:

```bash
git clone git@github.com:jetteim/poc-macbook.git
cd poc-macbook
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e ".[ml]"
```

3. Verify the hardware and model:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-camera --frames 60
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-model
```

4. Start a manual run:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json run
```

5. Optional: install the `systemd` service:

```bash
sudo cp deploy/systemd/catcam.service /etc/systemd/system/catcam.service
sudo systemctl daemon-reload
sudo systemctl enable --now catcam.service
sudo systemctl status catcam.service
```

## Usage

Show resolved config:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json show-config
```

Create today’s storage directory:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json bootstrap-storage
```

Preview a sample output path:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json sample-clip-path
```

Replay a saved input for deterministic testing:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json run --input /path/to/video.mp4 --display
```

Run the test suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Current Defaults

- `macos-dev` currently runs cat-only by default with `baby_resolver.mode = disabled`.
- `rpi4-prod` keeps ROI-based baby resolution enabled.
- Both shipped profiles use `3` seconds of pre-roll and `3` seconds of inactivity hold-open.
- macOS uses the frame-based recorder.
- Raspberry Pi uses the Picamera2 native circular H.264 recorder path and remuxes to MP4 with `ffmpeg`.

## Raspberry Pi Notes

- Install `python3-picamera2` from `apt`, not `pip`.
- Keep the legacy camera stack disabled.
- Use [deploy/systemd/catcam.service](deploy/systemd/catcam.service) as the starting unit file.
- Pi-specific recording has unit coverage in this repo, but still needs on-device validation for your exact camera, OS image, and thermals.

## Contributor Guide

Development workflow:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e ".[ml]"
.venv/bin/python -m unittest discover -s tests -v
```

When changing behavior:

- Update the matching config defaults in `configs/`.
- Keep `README.md`, [docs/requirements.md](docs/requirements.md), and [docs/architecture.md](docs/architecture.md) aligned.
- Prefer replay-based or fake-backend tests for runtime/recorder changes.
- Treat Pi-specific code as hardware-adjacent: add unit tests for API-shape assumptions even if you cannot run on the Pi locally.

Full contributor notes: [docs/contributing.md](docs/contributing.md)

## Repository Docs

- Requirements: [docs/requirements.md](docs/requirements.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- Raspberry Pi bring-up: [docs/raspberry-pi.md](docs/raspberry-pi.md)
- Project tracker: [TODO.md](TODO.md)
