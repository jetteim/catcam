# CatCam

Offline event-triggered video capture for cat or baby movement, with macOS development first and Raspberry Pi 4 deployment next.

## Quick Start

### macOS

```bash
./scripts/macos_quickstart.sh
```

Debuggable live run:

```bash
DISPLAY_FLAG=1 MAX_FRAMES=900 ./scripts/macos_quickstart.sh
```

Smoke checks:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json verify-model
.venv/bin/python -m catcam.cli --config configs/macos-dev.json verify-camera --frames 30
```

Live run:

```bash
./scripts/macos_quickstart.sh
```

### Raspberry Pi

Pi bring-up is documented in [docs/raspberry-pi.md](docs/raspberry-pi.md).

Minimal smoke sequence on the Pi:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-camera --frames 60
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-model
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json bootstrap-storage
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json benchmark --frames 180 --detector-mode motion-gated
```

## Brand-New Pi Setup

Use this on a fresh Raspberry Pi OS 64-bit install.

1. Install system packages:

```bash
sudo apt update
sudo apt install --yes git python3-venv python3-pip python3-picamera2 python3-libcamera ffmpeg
```

2. Clone the repo and install the project:

```bash
git clone https://github.com/jetteim/catcam.git ~/catcam
cd ~/catcam
./scripts/pi_setup.sh
```

The Pi setup script creates `.venv` with `--system-site-packages` so the `apt`-installed `picamera2` module remains visible inside the virtualenv.
It also downloads the YOLOX ONNX model into the ignored `models/` directory so `verify-model` and the smoke benchmark can run on a fresh clone.

3. Verify the hardware, model, and baseline throughput:

```bash
./scripts/pi_smoke_test.sh
```

4. Start a manual run:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json run
```

5. Optional: install the `systemd` service:

```bash
./scripts/pi_install_service.sh
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

Benchmark detector throughput:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json benchmark --frames 180 --detector-mode motion-gated
```

Run the test suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Current Defaults

- `macos-dev` currently runs cat-only by default with `baby_resolver.mode = disabled`.
- `rpi4-prod` keeps ROI-based baby resolution enabled.
- Both shipped profiles use `3` seconds of pre-roll and `3` seconds of inactivity hold-open.
- Both shipped profiles use a more sensitive motion gate than before, plus cat-specific activation rules: a `0.2` cat track-motion threshold scale, a `0.01` cat motion-fraction floor, and an OR condition on cat box shift/size change so small cat movement such as grooming or posture changes can still count as active once a cat is detected.
- macOS uses the frame-based recorder.
- Raspberry Pi uses the Picamera2 native circular H.264 recorder path and remuxes to MP4 with `ffmpeg`.

## Raspberry Pi Notes

- Install `python3-picamera2` from `apt`, not `pip`.
- The Pi virtualenv must include system site-packages so it can import the `apt`-installed `picamera2` module.
- Run `./scripts/pi_setup.sh` as your normal user. The script uses `sudo` only for `apt`, and keeps the repo plus `.venv` owned by that user.
- Keep the legacy camera stack disabled.
- Use [deploy/systemd/catcam.service](deploy/systemd/catcam.service) as the home-directory example unit file.
- Use [pi_setup.sh](scripts/pi_setup.sh), [pi_smoke_test.sh](scripts/pi_smoke_test.sh), and [pi_install_service.sh](scripts/pi_install_service.sh) on a fresh Pi clone.
- Pi-specific recording has unit coverage in this repo, but still needs on-device validation for your exact camera, OS image, and thermals.

## Contributor Guide

Development workflow:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .
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
