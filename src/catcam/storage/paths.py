from __future__ import annotations

from datetime import datetime
from pathlib import Path


def day_directory(root: str | Path, timestamp: datetime) -> Path:
    root_path = Path(root)
    return root_path / f"{timestamp:%Y}" / f"{timestamp:%m}" / f"{timestamp:%d}"


def clip_stem(timestamp: datetime, label: str, event_id: str) -> str:
    normalized = label.lower().replace(" ", "_")
    return f"{timestamp:%Y%m%dT%H%M%S}_{normalized}_{event_id}"


def build_clip_paths(
    root: str | Path,
    timestamp: datetime,
    label: str,
    event_id: str,
    container: str = "mp4",
) -> tuple[Path, Path]:
    day_dir = day_directory(root, timestamp)
    stem = clip_stem(timestamp, label, event_id)
    return day_dir / f"{stem}.{container}", day_dir / f"{stem}.json"


def ensure_day_directory(root: str | Path, timestamp: datetime) -> Path:
    target = day_directory(root, timestamp)
    target.mkdir(parents=True, exist_ok=True)
    return target
