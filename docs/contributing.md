# Contributing

## Local Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e ".[ml]"
```

On Raspberry Pi, install `python3-picamera2` from `apt` and keep the project installed in editable mode from the repo checkout.

## Before You Change Code

- Read [docs/requirements.md](requirements.md) and [docs/architecture.md](architecture.md).
- Check the active defaults in `configs/macos-dev.json` and `configs/rpi4-prod.json`.
- If you are changing recorder, timing, or detection behavior, inspect the existing tests first.

## Test Expectations

Run the full suite before finishing a change:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

When adding platform-specific code:

- add replay or fake-backend tests for pure logic;
- add API-shape tests for external libraries such as Picamera2;
- document any remaining hardware validation that still needs a real device.

## Documentation Expectations

Keep these files aligned with behavior changes:

- `README.md`
- `docs/requirements.md`
- `docs/architecture.md`
- `docs/raspberry-pi.md`
- `TODO.md`

## Pi Validation Workflow

Use the Pi itself for these commands:

```bash
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-camera --frames 60
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json verify-model
.venv/bin/python -m catcam.cli --config configs/rpi4-prod.json run
```
