from __future__ import annotations

from datetime import datetime
import time

from catcam.camera.base import CameraBackend
from catcam.types import FramePacket


class MacCameraBackend(CameraBackend):
    def __init__(self, device: int | str, width: int, height: int, fps: int) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self._capture = None
        self._frame_index = 0

    def start(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for the mac camera backend") from exc

        self._capture = cv2.VideoCapture(self.device, cv2.CAP_AVFOUNDATION)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._capture.set(cv2.CAP_PROP_FPS, self.fps)
        if not self._capture.isOpened():
            raise RuntimeError(f"Unable to open macOS camera device: {self.device}")

    def read(self) -> FramePacket:
        if self._capture is None:
            raise RuntimeError("camera backend has not been started")

        ok, frame = self._capture.read()
        if not ok:
            raise RuntimeError("Failed to read frame from macOS camera")

        packet = FramePacket(
            frame_index=self._frame_index,
            monotonic_seconds=time.monotonic(),
            wall_time=datetime.now(),
            image=frame,
        )
        self._frame_index += 1
        return packet

    def stop(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
