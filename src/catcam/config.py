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
    motion_min_area: int
    motion_min_score: float


@dataclass
class RecordingConfig:
    root: Path
    pre_event_seconds: float
    post_event_seconds: float
    merge_gap_seconds: float
    container: str


@dataclass
class DetectionConfig:
    runtime: str
    model_path: Path
    person_label: str
    cat_label: str


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
            runtime=data["detection"]["runtime"],
            model_path=Path(data["detection"]["model_path"]),
            person_label=data["detection"]["person_label"],
            cat_label=data["detection"]["cat_label"],
        ),
        baby_resolver=BabyResolverConfig(
            mode=data["baby_resolver"]["mode"],
            roi=tuple(float(value) for value in data["baby_resolver"]["roi"]),
        ),
    )
