from __future__ import annotations

from abc import ABC, abstractmethod

from catcam.types import Detection, EventDecision, EventRecord, FramePacket


class RecorderBackend(ABC):
    @property
    @abstractmethod
    def active(self) -> bool:
        raise NotImplementedError

    def open(self) -> None:
        return None

    @abstractmethod
    def start(self, decision: EventDecision, pre_event_frames: list[FramePacket]):
        raise NotImplementedError

    @abstractmethod
    def write_frame(self, packet: FramePacket, detections: list[Detection] | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def finalize(self, decision: EventDecision) -> EventRecord:
        raise NotImplementedError

    def close(self) -> None:
        return None
