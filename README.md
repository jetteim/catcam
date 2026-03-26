# CatCam

Offline video event capture for cat or baby movement.

Current repository contents:

- architecture and stack decision notes in [docs/architecture.md](docs/architecture.md);
- functional and non-functional requirements in [docs/requirements.md](docs/requirements.md);
- phased implementation tracker in [TODO.md](TODO.md).
- Python scaffold under `src/catcam` for config loading, event logic, buffering, storage, and CLI utilities.

Planned delivery path:

1. build and validate on macOS with the MacBook camera;
2. migrate camera and recorder backends to Raspberry Pi 4 with Raspberry Pi camera;
3. optimize inference and recording for headless offline operation.

Current CLI examples:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json verify-model
.venv/bin/python -m catcam.cli --config configs/macos-dev.json run
.venv/bin/python -m unittest discover -s tests -v
```

Live macOS camera test:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json run --display
```

Replay-file test:

```bash
.venv/bin/python -m catcam.cli --config configs/macos-dev.json run --input /path/to/video.mp4 --display
```

Current detection behavior:

- `cat` uses the bundled OpenCV Zoo YOLOX COCO detector model at `models/opencv_yolox/object_detection_yolox_2022nov.onnx`.
- `baby` uses the configured ROI rule on `person` detections for the MVP path.
- clips are written under `records/YYYY/MM/DD` with adjacent JSON metadata.
