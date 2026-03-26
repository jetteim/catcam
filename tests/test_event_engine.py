from datetime import datetime, timedelta
import unittest

from catcam.config import RecordingConfig
from catcam.pipeline.event_engine import EventEngine
from catcam.types import TrackMotionObservation


class EventEngineTests(unittest.TestCase):
    def test_uses_first_confirmed_timestamp_for_event_start(self) -> None:
        engine = EventEngine(
            recording=RecordingConfig(
                root="records",
                pre_event_seconds=2.0,
                post_event_seconds=3.0,
                merge_gap_seconds=6.0,
                container="mp4",
            ),
            confirm_frames=2,
        )
        start = datetime(2026, 3, 26, 21, 44, 55)

        first = engine.process(TrackMotionObservation(timestamp=start, target_motion=True, labels=["cat"]))
        second = engine.process(
            TrackMotionObservation(timestamp=start + timedelta(milliseconds=100), target_motion=True, labels=["cat"])
        )

        self.assertEqual(first.action, "candidate")
        self.assertEqual(second.action, "start_recording")
        self.assertEqual(second.event_start, start)
        self.assertEqual(second.label, "cat")

    def test_finalizes_after_hold_open_window(self) -> None:
        engine = EventEngine(
            recording=RecordingConfig(
                root="records",
                pre_event_seconds=2.0,
                post_event_seconds=3.0,
                merge_gap_seconds=6.0,
                container="mp4",
            ),
            confirm_frames=1,
        )
        start = datetime(2026, 3, 26, 21, 44, 55)

        started = engine.process(TrackMotionObservation(timestamp=start, target_motion=True, labels=["cat"]))
        held = engine.process(
            TrackMotionObservation(timestamp=start + timedelta(seconds=5), target_motion=False, labels=[])
        )
        finalized = engine.process(
            TrackMotionObservation(timestamp=start + timedelta(seconds=7), target_motion=False, labels=[])
        )

        self.assertEqual(started.action, "start_recording")
        self.assertEqual(held.action, "continue_recording")
        self.assertEqual(finalized.action, "finalize_recording")
        self.assertEqual(finalized.event_end, start)


if __name__ == "__main__":
    unittest.main()
