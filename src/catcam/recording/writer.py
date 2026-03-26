from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from catcam.config import AppConfig
from catcam.recording.base import RecorderBackend
from catcam.storage.metadata import write_event_metadata
from catcam.storage.paths import build_clip_paths, ensure_day_directory
from catcam.types import Detection, EventDecision, EventRecord, FramePacket


@dataclass
class RecordingSession:
    event_id: str
    label: str
    start_time: datetime
    clip_path: Path
    metadata_path: Path
    writer: object
    labels: Counter[str] = field(default_factory=Counter)
    confidences: dict[str, float] = field(default_factory=dict)
    last_written_time: datetime | None = None
    written_frames: set[int] = field(default_factory=set)


class ClipRecorder(RecorderBackend):
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._session: RecordingSession | None = None

    @property
    def active(self) -> bool:
        return self._session is not None

    def start(self, decision: EventDecision, pre_event_frames: list[FramePacket]) -> RecordingSession:
        if self._session is not None:
            return self._session
        if not pre_event_frames:
            raise ValueError("pre_event_frames must include at least the trigger frame")
        if decision.event_id is None or decision.label is None or decision.event_start is None:
            raise ValueError("event decision is missing required start fields")

        import cv2

        clip_path, metadata_path = build_clip_paths(
            root=self.config.recording.root,
            timestamp=decision.event_start,
            label=decision.label,
            event_id=decision.event_id,
            container=self.config.recording.container,
        )
        ensure_day_directory(self.config.recording.root, decision.event_start)

        frame = pre_event_frames[0].image
        height, width = frame.shape[:2]
        output_fps = estimate_output_fps(pre_event_frames, fallback_fps=float(self.config.camera.fps))
        writer = cv2.VideoWriter(
            str(clip_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            output_fps,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Unable to open clip writer: {clip_path}")

        session = RecordingSession(
            event_id=decision.event_id,
            label=decision.label,
            start_time=decision.event_start,
            clip_path=clip_path,
            metadata_path=metadata_path,
            writer=writer,
        )
        self._session = session
        for packet in pre_event_frames:
            self.write_frame(packet)
        return session

    def write_frame(self, packet: FramePacket, detections: list[Detection] | None = None) -> None:
        session = self._require_session()
        if packet.frame_index in session.written_frames:
            return
        session.writer.write(packet.image)
        session.written_frames.add(packet.frame_index)
        session.last_written_time = packet.wall_time
        if detections:
            for detection in detections:
                session.labels.update([detection.label])
                previous = session.confidences.get(detection.label, 0.0)
                session.confidences[detection.label] = max(previous, detection.confidence)

    def finalize(self, decision: EventDecision) -> EventRecord:
        session = self._require_session()
        event_end = decision.event_end or session.last_written_time or session.start_time
        session.writer.release()
        record = EventRecord(
            event_id=session.event_id,
            label=session.label,
            start_time=session.start_time,
            end_time=event_end,
            pre_event_seconds=self.config.recording.pre_event_seconds,
            source_camera=self.config.camera.device,
            profile=self.config.profile,
            clip_path=session.clip_path,
            metadata_path=session.metadata_path,
            confidence_summary=session.confidences,
        )
        write_event_metadata(record)
        self._session = None
        return record

    def _require_session(self) -> RecordingSession:
        if self._session is None:
            raise RuntimeError("recording session is not active")
        return self._session


def estimate_output_fps(pre_event_frames: list[FramePacket], fallback_fps: float) -> float:
    if len(pre_event_frames) < 2:
        return fallback_fps
    elapsed = pre_event_frames[-1].monotonic_seconds - pre_event_frames[0].monotonic_seconds
    if elapsed <= 0:
        return fallback_fps
    observed_fps = (len(pre_event_frames) - 1) / elapsed
    if observed_fps < 1.0 or observed_fps > 120.0:
        return fallback_fps
    return observed_fps
