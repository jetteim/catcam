from __future__ import annotations

from catcam.config import AppConfig
from catcam.recording.base import RecorderBackend
from catcam.recording.pi_native import PiNativeRecorder
from catcam.recording.writer import ClipRecorder


def create_recorder(config: AppConfig, camera_backend) -> RecorderBackend:
    if config.camera.backend == "picamera2" and camera_backend is not None:
        return PiNativeRecorder(config, camera_backend=camera_backend)
    return ClipRecorder(config)
