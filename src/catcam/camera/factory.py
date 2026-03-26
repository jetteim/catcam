from __future__ import annotations

from catcam.camera.base import CameraBackend
from catcam.camera.mac_camera import MacCameraBackend
from catcam.camera.pi_camera import PiCameraBackend
from catcam.camera.replay_camera import ReplayCameraBackend
from catcam.config import AppConfig


def create_camera_backend(config: AppConfig, input_path: str | None = None) -> CameraBackend:
    if input_path:
        return ReplayCameraBackend(
            path=input_path,
            width=config.camera.width,
            height=config.camera.height,
        )

    if config.camera.backend == "mac":
        device = 0 if config.camera.device == "default" else config.camera.device
        return MacCameraBackend(
            device=device,
            width=config.camera.width,
            height=config.camera.height,
            fps=config.camera.fps,
        )

    if config.camera.backend == "picamera2":
        return PiCameraBackend(
            width=config.camera.width,
            height=config.camera.height,
            fps=config.camera.fps,
        )

    raise ValueError(f"Unsupported camera backend: {config.camera.backend}")
