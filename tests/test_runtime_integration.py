from pathlib import Path
import json
import tempfile
import unittest

import cv2
import numpy as np

from catcam.runtime import CatCamRuntime, RunOptions


class RuntimeIntegrationTests(unittest.TestCase):
    def test_replay_pipeline_writes_clip_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            video_path = tmp / "input.mp4"
            records_root = tmp / "records"
            config_path = tmp / "config.json"
            self._write_test_video(video_path)
            self._write_config(config_path, records_root, detection_backend="mock_cat")

            runtime = CatCamRuntime(RunOptions(config_path=str(config_path), input_path=str(video_path), max_frames=20))
            exit_code = runtime.run()

            self.assertEqual(exit_code, 0)
            clips = list(records_root.rglob("*.mp4"))
            metadata_files = list(records_root.rglob("*.json"))
            self.assertEqual(len(clips), 1)
            self.assertEqual(len(metadata_files), 1)
            self.assertGreater(clips[0].stat().st_size, 0)

    def test_replay_pipeline_skips_clip_for_non_target_motion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            video_path = tmp / "input.mp4"
            records_root = tmp / "records"
            config_path = tmp / "config.json"
            self._write_test_video(video_path)
            self._write_config(config_path, records_root, detection_backend="disabled")

            runtime = CatCamRuntime(RunOptions(config_path=str(config_path), input_path=str(video_path), max_frames=20))
            exit_code = runtime.run()

            self.assertEqual(exit_code, 0)
            self.assertEqual(list(records_root.rglob("*.mp4")), [])
            self.assertEqual(list(records_root.rglob("*.json")), [])

    def _write_test_video(self, path: Path) -> None:
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
        self.assertTrue(writer.isOpened())
        for index in range(20):
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            if 5 <= index <= 12:
                x0 = 20 + (index - 5) * 18
                cv2.rectangle(frame, (x0, 80), (x0 + 60, 150), (255, 255, 255), -1)
            writer.write(frame)
        writer.release()

    def _write_config(self, path: Path, records_root: Path, detection_backend: str) -> None:
        path.write_text(
            json.dumps(
                {
                    "profile": "test",
                    "camera": {
                        "backend": "mac",
                        "device": "test",
                        "width": 320,
                        "height": 240,
                        "fps": 10,
                    },
                    "analysis": {
                        "width": 320,
                        "height": 240,
                        "fps": 10,
                        "confirm_frames": 1,
                        "warmup_frames": 3,
                        "motion_min_area": 50,
                        "motion_min_score": 0.001,
                    },
                    "recording": {
                        "root": str(records_root),
                        "pre_event_seconds": 2.0,
                        "post_event_seconds": 0.2,
                        "merge_gap_seconds": 0.2,
                        "container": "mp4",
                    },
                    "detection": {
                        "backend": detection_backend,
                        "model_path": "unused.onnx",
                        "person_label": "person",
                        "cat_label": "cat",
                        "confidence_threshold": 0.35,
                        "nms_threshold": 0.5,
                    },
                    "baby_resolver": {
                        "mode": "roi_person_is_baby",
                        "roi": [0.2, 0.2, 0.8, 0.8],
                    },
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
