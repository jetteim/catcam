from datetime import datetime
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from catcam.config import AnalysisConfig, AppConfig, BabyResolverConfig, CameraConfig, DetectionConfig, RecordingConfig
from catcam.recording.pi_native import PiNativeRecorder
from catcam.types import Detection, EventDecision, FramePacket


class _FakeEncoder:
    def __init__(self) -> None:
        self.output = None


class _FakeCircularOutput:
    instances = []

    def __init__(self, buffersize: int, outputtofile: bool) -> None:
        self.buffersize = buffersize
        self.outputtofile = outputtofile
        self.fileoutput = None
        self.started = False
        _FakeCircularOutput.instances.append(self)

    def start(self) -> None:
        self.started = True
        Path(self.fileoutput).write_bytes(b"fake-h264")

    def stop(self) -> None:
        self.started = False


class _FakeNativeCamera:
    def __init__(self) -> None:
        self.started_with = None
        self.stopped = False

    def start_encoder(self, encoder) -> None:
        self.started_with = encoder

    def stop_encoder(self) -> None:
        self.stopped = True


class _FakeCameraBackend:
    def __init__(self, native_camera) -> None:
        self._native_camera = native_camera

    def native_camera(self):
        return self._native_camera


class PiNativeRecorderTests(unittest.TestCase):
    def test_open_starts_circular_encoder_and_finalize_remuxes_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config = self._build_config(tmp, container="mp4")
            native_camera = _FakeNativeCamera()
            recorder = PiNativeRecorder(config, camera_backend=_FakeCameraBackend(native_camera))

            fake_encoders = types.SimpleNamespace(H264Encoder=_FakeEncoder)
            fake_outputs = types.SimpleNamespace(CircularOutput=_FakeCircularOutput, FileOutput=None)

            def fake_ffmpeg_run(command, check):
                Path(command[-1]).write_bytes(b"mp4")

            with patch.dict("sys.modules", {"picamera2.encoders": fake_encoders, "picamera2.outputs": fake_outputs}):
                with patch("catcam.recording.pi_native.shutil.which", return_value="/usr/bin/ffmpeg"):
                    with patch("catcam.recording.pi_native.subprocess.run", side_effect=fake_ffmpeg_run):
                        recorder.open()
                        decision = EventDecision(
                            action="start_recording",
                            event_id="abc123",
                            label="cat",
                            event_start=datetime(2026, 3, 26, 12, 0, 0),
                        )
                        recorder.start(decision, [])
                        recorder.write_frame(
                            FramePacket(
                                frame_index=1,
                                monotonic_seconds=1.0,
                                wall_time=datetime(2026, 3, 26, 12, 0, 1),
                            ),
                            [Detection(label="cat", original_label="cat", confidence=0.9, bbox=(0, 0, 10, 10))],
                        )
                        record = recorder.finalize(
                            EventDecision(
                                action="finalize_recording",
                                event_id="abc123",
                                label="cat",
                                event_start=decision.event_start,
                                event_end=datetime(2026, 3, 26, 12, 0, 1),
                            )
                        )
                        recorder.close()

            self.assertEqual(_FakeCircularOutput.instances[-1].buffersize, 45)
            self.assertIs(native_camera.started_with.output, _FakeCircularOutput.instances[-1])
            self.assertTrue(record.clip_path.exists())
            self.assertTrue(record.metadata_path.exists())
            self.assertTrue(native_camera.stopped)

    def test_finalize_moves_h264_when_container_is_raw(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config = self._build_config(tmp, container="h264")
            native_camera = _FakeNativeCamera()
            recorder = PiNativeRecorder(config, camera_backend=_FakeCameraBackend(native_camera))

            fake_encoders = types.SimpleNamespace(H264Encoder=_FakeEncoder)
            fake_outputs = types.SimpleNamespace(CircularOutput=_FakeCircularOutput, FileOutput=None)

            with patch.dict("sys.modules", {"picamera2.encoders": fake_encoders, "picamera2.outputs": fake_outputs}):
                recorder.open()
                decision = EventDecision(
                    action="start_recording",
                    event_id="raw123",
                    label="cat",
                    event_start=datetime(2026, 3, 26, 12, 0, 0),
                )
                recorder.start(decision, [])
                record = recorder.finalize(
                    EventDecision(
                        action="finalize_recording",
                        event_id="raw123",
                        label="cat",
                        event_start=decision.event_start,
                        event_end=datetime(2026, 3, 26, 12, 0, 0),
                    )
                )

            self.assertEqual(record.clip_path.suffix, ".h264")
            self.assertTrue(record.clip_path.exists())

    def _build_config(self, root: Path, container: str) -> AppConfig:
        return AppConfig(
            profile="rpi4-prod",
            camera=CameraConfig(backend="picamera2", device="rpi-camera", width=1280, height=720, fps=15),
            analysis=AnalysisConfig(
                width=512,
                height=288,
                fps=8,
                confirm_frames=2,
                warmup_frames=15,
                motion_min_area=700,
                motion_min_score=0.08,
                track_max_missing_frames=5,
                track_motion_min_score=0.08,
                track_min_iou=0.3,
                track_max_centroid_distance=80.0,
            ),
            recording=RecordingConfig(
                root=root / "records",
                pre_event_seconds=3.0,
                post_event_seconds=3.0,
                merge_gap_seconds=3.0,
                container=container,
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
