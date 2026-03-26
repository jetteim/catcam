from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import time

from catcam.camera.base import CameraBackend
from catcam.types import FramePacket


class ReplayCameraBackend(CameraBackend):
    def __init__(self, path: str, width: int, height: int) -> None:
        self.path = Path(path)
        self.width = width
        self.height = height
        self._capture = None
        self._frame_index = 0
        self._fps = 0.0
        self._start_wall_time = datetime.now()

    def start(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for replay input") from exc

        self._capture = cv2.VideoCapture(str(self.path))
        if not self._capture.isOpened():
            raise RuntimeError(f"Unable to open replay input: {self.path}")
        self._fps = float(self._capture.get(cv2.CAP_PROP_FPS) or 0.0) or 15.0
        self._start_wall_time = datetime.now()

    def read(self) -> FramePacket:
        if self._capture is None:
            raise RuntimeError("camera backend has not been started")

        ok, frame = self._capture.read()
        if not ok:
            raise EOFError("Replay input exhausted")

        wall_time = self._start_wall_time + timedelta(seconds=self._frame_index / self._fps)
        packet = FramePacket(
            frame_index=self._frame_index,
            monotonic_seconds=time.monotonic(),
            wall_time=wall_time,
            image=frame,
        )
        self._frame_index += 1
        return packet

    def stop(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
