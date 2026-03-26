from __future__ import annotations

from abc import ABC, abstractmethod

from catcam.types import FramePacket


class CameraBackend(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self) -> FramePacket:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    def native_camera(self):
        return None
