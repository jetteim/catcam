from pathlib import Path
import json
import tempfile
import unittest

import cv2
import numpy as np

from catcam.benchmark import BenchmarkOptions, benchmark_pipeline


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_pipeline_reports_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            video_path = tmp / "input.mp4"
            config_path = tmp / "config.json"
            self._write_test_video(video_path)
            config_path.write_text(
                json.dumps(
                    {
                        "profile": "bench",
                        "camera": {
                            "backend": "mac",
                            "device": "default",
                            "width": 320,
                            "height": 240,
                            "fps": 10,
                        },
                        "analysis": {
                            "width": 320,
                            "height": 240,
                            "fps": 10,
                            "confirm_frames": 1,
                            "warmup_frames": 0,
                            "motion_min_area": 50,
                            "motion_min_score": 0.001,
                        },
                        "recording": {
                            "root": str(tmp / "records"),
                            "pre_event_seconds": 3.0,
                            "post_event_seconds": 3.0,
                            "merge_gap_seconds": 3.0,
                            "container": "mp4",
                        },
                        "detection": {
                            "backend": "disabled",
                            "model_path": "unused.onnx",
                            "person_label": "person",
                            "cat_label": "cat",
                            "confidence_threshold": 0.35,
                            "nms_threshold": 0.5,
                        },
                        "baby_resolver": {
                            "mode": "disabled",
                            "roi": [0.2, 0.2, 0.8, 0.8],
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = benchmark_pipeline(
                BenchmarkOptions(
                    config_path=str(config_path),
                    input_path=str(video_path),
                    frames=8,
                    detector_mode="always",
                )
            )

            self.assertEqual(result["frames"], 8)
            self.assertEqual(result["detector_invocations"], 8)
            self.assertEqual(result["analysis_size"], [320, 240])
            self.assertGreater(result["pipeline_fps"], 0.0)

    def _write_test_video(self, path: Path) -> None:
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
        self.assertTrue(writer.isOpened())
        for index in range(12):
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            if 3 <= index <= 8:
                cv2.rectangle(frame, (40 + index * 5, 80), (90 + index * 5, 140), (255, 255, 255), -1)
            writer.write(frame)
        writer.release()


if __name__ == "__main__":
    unittest.main()
