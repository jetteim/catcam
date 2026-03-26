from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FramePacket:
    frame_index: int
    monotonic_seconds: float
    wall_time: datetime
    image: Any = None


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    original_label: str | None = None


@dataclass
class TrackMotionObservation:
    timestamp: datetime
    target_motion: bool
    labels: list[str] = field(default_factory=list)
    motion_score: float = 0.0

    @property
    def primary_label(self) -> str:
        return self.labels[0] if self.labels else "unknown"


@dataclass
class EventRecord:
    event_id: str
    label: str
    start_time: datetime
    end_time: datetime
    pre_event_seconds: float
    source_camera: str
    profile: str
    clip_path: Path
    metadata_path: Path
    confidence_summary: dict[str, float] = field(default_factory=dict)


@dataclass
class EventDecision:
    action: str
    event_id: str | None = None
    label: str | None = None
    event_start: datetime | None = None
    event_end: datetime | None = None
    reason: str | None = None


@dataclass
class MotionAnalysis:
    present: bool
    score: float
    area: int
    mask: Any = None
