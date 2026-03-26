from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import uuid4

from catcam.config import RecordingConfig
from catcam.types import EventDecision, TrackMotionObservation


@dataclass
class EventEngine:
    recording: RecordingConfig
    confirm_frames: int
    _state: str = "idle"
    _candidate_start: datetime | None = None
    _candidate_labels: list[str] = field(default_factory=list)
    _candidate_count: int = 0
    _event_id: str | None = None
    _event_start: datetime | None = None
    _event_label_counts: Counter[str] = field(default_factory=Counter)
    _last_motion_at: datetime | None = None

    def process(self, observation: TrackMotionObservation) -> EventDecision:
        if observation.target_motion:
            return self._on_target_motion(observation)
        return self._on_no_target_motion(observation.timestamp)

    def _on_target_motion(self, observation: TrackMotionObservation) -> EventDecision:
        timestamp = observation.timestamp
        label = observation.primary_label

        if self._state in {"idle", "candidate"}:
            if self._candidate_start is None:
                self._candidate_start = timestamp
            self._candidate_count += 1
            self._candidate_labels.extend(observation.labels or [label])
            self._state = "candidate"

            if self._candidate_count >= self.confirm_frames:
                self._state = "recording"
                self._event_id = uuid4().hex[:12]
                self._event_start = self._candidate_start
                self._event_label_counts = Counter(self._candidate_labels)
                self._last_motion_at = timestamp
                return EventDecision(
                    action="start_recording",
                    event_id=self._event_id,
                    label=self._dominant_label(),
                    event_start=self._event_start,
                    reason="target-motion-confirmed",
                )

            return EventDecision(action="candidate", label=label, reason="awaiting-confirmation")

        self._last_motion_at = timestamp
        self._event_label_counts.update(observation.labels or [label])
        self._state = "recording"
        return EventDecision(
            action="continue_recording",
            event_id=self._event_id,
            label=self._dominant_label(),
            event_start=self._event_start,
            reason="target-motion-active",
        )

    def _on_no_target_motion(self, timestamp: datetime) -> EventDecision:
        if self._state == "candidate":
            self._reset_candidate()
            self._state = "idle"
            return EventDecision(action="idle", reason="candidate-reset")

        if self._state not in {"recording", "cooldown"}:
            return EventDecision(action="idle", reason="no-target-motion")

        assert self._last_motion_at is not None
        gap = timestamp - self._last_motion_at
        hold_open = max(self.recording.post_event_seconds, self.recording.merge_gap_seconds)

        if gap <= timedelta(seconds=hold_open):
            self._state = "cooldown"
            return EventDecision(
                action="continue_recording",
                event_id=self._event_id,
                label=self._dominant_label(),
                event_start=self._event_start,
                reason="post-roll-or-merge-gap",
            )

        decision = EventDecision(
            action="finalize_recording",
            event_id=self._event_id,
            label=self._dominant_label(),
            event_start=self._event_start,
            event_end=self._last_motion_at,
            reason="target-motion-ended",
        )
        self._reset_all()
        return decision

    def _dominant_label(self) -> str:
        if not self._event_label_counts:
            return "unknown"
        return self._event_label_counts.most_common(1)[0][0]

    def _reset_candidate(self) -> None:
        self._candidate_start = None
        self._candidate_labels.clear()
        self._candidate_count = 0

    def _reset_all(self) -> None:
        self._reset_candidate()
        self._state = "idle"
        self._event_id = None
        self._event_start = None
        self._event_label_counts.clear()
        self._last_motion_at = None
