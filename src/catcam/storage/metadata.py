from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from catcam.types import EventRecord


def write_event_metadata(record: EventRecord) -> None:
    payload = asdict(record)
    payload["clip_path"] = str(record.clip_path)
    payload["metadata_path"] = str(record.metadata_path)
    payload["start_time"] = record.start_time.isoformat()
    payload["end_time"] = record.end_time.isoformat()

    record.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    record.metadata_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
