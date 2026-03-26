# CatCam

Offline video event capture for cat or baby movement.

Current repository contents:

- architecture and stack decision notes in [docs/architecture.md](docs/architecture.md);
- functional and non-functional requirements in [docs/requirements.md](docs/requirements.md);
- phased implementation tracker in [TODO.md](TODO.md).

Planned delivery path:

1. build and validate on macOS with the MacBook camera;
2. migrate camera and recorder backends to Raspberry Pi 4 with Raspberry Pi camera;
3. optimize inference and recording for headless offline operation.
