from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from catcam.config import AnalysisConfig, AppConfig, BabyResolverConfig, CameraConfig, DetectionConfig, RecordingConfig
from catcam.recording.writer import ClipRecorder, RecordingSession, target_frame_count_for_time
from catcam.types import FramePacket


class _FakeWriter:
    def __init__(self) -> None:
        self.frames = []

    def write(self, image) -> None:
        self.frames.append(image)


class ClipWriterTests(unittest.TestCase):
    def test_target_frame_count_tracks_wall_clock_time(self) -> None:
        start = datetime(2026, 3, 26, 15, 47, 50)

        self.assertEqual(target_frame_count_for_time(start, start, output_fps=10.0), 1)
        self.assertEqual(target_frame_count_for_time(start, start + timedelta(milliseconds=200), output_fps=10.0), 3)
        self.assertEqual(target_frame_count_for_time(start, start + timedelta(milliseconds=950), output_fps=10.0), 10)

    def test_write_frame_repeats_frames_to_cover_elapsed_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ClipRecorder(self._build_config(Path(tmpdir)))
            writer = _FakeWriter()
            start = datetime(2026, 3, 26, 15, 47, 50)
            recorder._session = RecordingSession(
                event_id="evt123",
                label="cat",
                start_time=start,
                clip_path=Path(tmpdir) / "clip.mp4",
                metadata_path=Path(tmpdir) / "clip.json",
                writer=writer,
                output_fps=10.0,
                clip_origin_time=start,
            )

            recorder.write_frame(FramePacket(frame_index=0, monotonic_seconds=0.0, wall_time=start, image="first"))
            recorder.write_frame(
                FramePacket(
                    frame_index=1,
                    monotonic_seconds=0.35,
                    wall_time=start + timedelta(milliseconds=350),
                    image="second",
                )
            )

            self.assertEqual(writer.frames, ["first", "second", "second", "second"])

    def _build_config(self, root: Path) -> AppConfig:
        return AppConfig(
            profile="test",
            camera=CameraConfig(backend="mac", device="test", width=320, height=240, fps=10),
            analysis=AnalysisConfig(
                width=320,
                height=240,
                fps=10,
                confirm_frames=1,
                warmup_frames=3,
                motion_min_area=50,
                motion_min_score=0.001,
                track_max_missing_frames=5,
                track_motion_min_score=0.08,
                cat_motion_min_score_scale=0.5,
                track_min_iou=0.3,
                track_max_centroid_distance=80.0,
            ),
            recording=RecordingConfig(
                root=root / "records",
                pre_event_seconds=3.0,
                post_event_seconds=3.0,
                merge_gap_seconds=3.0,
                container="mp4",
            ),
            detection=DetectionConfig(
                backend="disabled",
                model_path=Path("unused.onnx"),
                person_label="person",
                cat_label="cat",
                confidence_threshold=0.35,
                nms_threshold=0.5,
            ),
            baby_resolver=BabyResolverConfig(mode="disabled", roi=(0.2, 0.2, 0.8, 0.8)),
        )


if __name__ == "__main__":
    unittest.main()
