from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from catcam.camera.base import CameraBackend
from catcam.camera.factory import create_camera_backend
from catcam.config import AppConfig, load_config
from catcam.pipeline.event_engine import EventEngine
from catcam.recording.buffer import PreEventBuffer
from catcam.storage.paths import ensure_day_directory
from catcam.types import FramePacket


@dataclass
class AppContext:
    config: AppConfig
    pre_event_buffer: PreEventBuffer[FramePacket]
    event_engine: EventEngine
    camera: CameraBackend | None


def build_context(
    config_path: str | Path,
    input_path: str | None = None,
    include_camera: bool = True,
) -> AppContext:
    config = load_config(config_path)
    buffer = PreEventBuffer[FramePacket](
        fps=config.camera.fps,
        seconds=config.recording.pre_event_seconds,
    )
    engine = EventEngine(
        recording=config.recording,
        confirm_frames=config.analysis.confirm_frames,
    )
    camera = create_camera_backend(config, input_path=input_path) if include_camera else None
    return AppContext(config=config, pre_event_buffer=buffer, event_engine=engine, camera=camera)


def bootstrap_storage(config: AppConfig) -> Path:
    return ensure_day_directory(config.recording.root, timestamp=_now())


def _now():
    from datetime import datetime

    return datetime.now()
