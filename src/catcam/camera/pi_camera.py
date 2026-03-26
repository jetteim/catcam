from __future__ import annotations

from datetime import datetime
import time

from catcam.camera.base import CameraBackend
from catcam.types import FramePacket


class PiCameraBackend(CameraBackend):
    def __init__(self, width: int, height: int, fps: int) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self._camera = None
        self._frame_index = 0

    def start(self) -> None:
        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise RuntimeError("picamera2 is required for the Raspberry Pi camera backend") from exc

        self._camera = Picamera2()
        config = self._camera.create_video_configuration(
            main={"size": (self.width, self.height)},
            controls={"FrameRate": self.fps},
        )
        self._camera.configure(config)
        self._camera.start()

    def read(self) -> FramePacket:
        if self._camera is None:
            raise RuntimeError("camera backend has not been started")

        frame = self._camera.capture_array()
        packet = FramePacket(
            frame_index=self._frame_index,
            monotonic_seconds=time.monotonic(),
            wall_time=datetime.now(),
            image=frame,
        )
        self._frame_index += 1
        return packet

    def stop(self) -> None:
        if self._camera is not None:
            self._camera.stop()
            self._camera.close()
            self._camera = None

    def native_camera(self):
        return self._camera
