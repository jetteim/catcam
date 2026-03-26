from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class CameraConfig:
    backend: str
    device: str
    width: int
    height: int
    fps: int


@dataclass
class AnalysisConfig:
    width: int
    height: int
    fps: int
    confirm_frames: int
    warmup_frames: int
    motion_min_area: int
    motion_min_score: float
    track_max_missing_frames: int = 5
    track_motion_min_score: float = 0.08
    track_min_iou: float = 0.3
    track_max_centroid_distance: float = 80.0


@dataclass
class RecordingConfig:
    root: Path
    pre_event_seconds: float
    post_event_seconds: float
    merge_gap_seconds: float
    container: str


@dataclass
class DetectionConfig:
    backend: str
    model_path: Path
    person_label: str
    cat_label: str
    confidence_threshold: float
    nms_threshold: float


@dataclass
class BabyResolverConfig:
    mode: str
    roi: tuple[float, float, float, float]


@dataclass
class AppConfig:
    profile: str
    camera: CameraConfig
    analysis: AnalysisConfig
    recording: RecordingConfig
    detection: DetectionConfig
    baby_resolver: BabyResolverConfig


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))

    return AppConfig(
        profile=data["profile"],
        camera=CameraConfig(**data["camera"]),
        analysis=AnalysisConfig(**data["analysis"]),
        recording=RecordingConfig(
            root=Path(data["recording"]["root"]),
            pre_event_seconds=float(data["recording"]["pre_event_seconds"]),
            post_event_seconds=float(data["recording"]["post_event_seconds"]),
            merge_gap_seconds=float(data["recording"]["merge_gap_seconds"]),
            container=data["recording"]["container"],
        ),
        detection=DetectionConfig(
            backend=data["detection"]["backend"],
            model_path=Path(data["detection"]["model_path"]),
            person_label=data["detection"]["person_label"],
            cat_label=data["detection"]["cat_label"],
            confidence_threshold=float(data["detection"]["confidence_threshold"]),
            nms_threshold=float(data["detection"]["nms_threshold"]),
        ),
        baby_resolver=BabyResolverConfig(
            mode=data["baby_resolver"]["mode"],
            roi=tuple(float(value) for value in data["baby_resolver"]["roi"]),
        ),
    )
