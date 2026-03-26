from datetime import datetime, timedelta
import unittest

from catcam.recording.writer import estimate_output_fps
from catcam.types import FramePacket


class ClipWriterTests(unittest.TestCase):
    def test_estimate_output_fps_uses_observed_frame_timing(self) -> None:
        start = datetime(2026, 3, 26, 15, 47, 50)
        frames = [
            FramePacket(frame_index=index, monotonic_seconds=index / 9.0, wall_time=start + timedelta(seconds=index / 9.0))
            for index in range(18)
        ]

        fps = estimate_output_fps(frames, fallback_fps=15.0)

        self.assertAlmostEqual(fps, 9.0, places=1)

    def test_estimate_output_fps_falls_back_without_timing_span(self) -> None:
        now = datetime(2026, 3, 26, 15, 47, 50)
        frames = [
            FramePacket(frame_index=0, monotonic_seconds=10.0, wall_time=now),
            FramePacket(frame_index=1, monotonic_seconds=10.0, wall_time=now),
        ]

        fps = estimate_output_fps(frames, fallback_fps=15.0)

        self.assertEqual(fps, 15.0)


if __name__ == "__main__":
    unittest.main()
