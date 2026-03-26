from pathlib import Path
import json
import tempfile
import unittest

from catcam.app import bootstrap_storage, build_context


class AppTests(unittest.TestCase):
    def test_build_context_without_camera_skips_backend_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config_path = tmp / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "profile": "test-pi",
                        "camera": {
                            "backend": "picamera2",
                            "device": "rpi-camera",
                            "width": 640,
                            "height": 480,
                            "fps": 10,
                        },
                        "analysis": {
                            "width": 320,
                            "height": 240,
                            "fps": 10,
                            "confirm_frames": 2,
                            "warmup_frames": 5,
                            "motion_min_area": 100,
                            "motion_min_score": 0.01,
                        },
                        "recording": {
                            "root": str(tmp / "records"),
                            "pre_event_seconds": 2.0,
                            "post_event_seconds": 5.0,
                            "merge_gap_seconds": 5.0,
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

            context = build_context(config_path, include_camera=False)

            self.assertIsNone(context.camera)
            self.assertEqual(context.config.camera.backend, "picamera2")

    def test_bootstrap_storage_uses_config_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config_path = tmp / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "profile": "test-storage",
                        "camera": {
                            "backend": "mac",
                            "device": "default",
                            "width": 640,
                            "height": 480,
                            "fps": 10,
                        },
                        "analysis": {
                            "width": 320,
                            "height": 240,
                            "fps": 10,
                            "confirm_frames": 2,
                            "warmup_frames": 5,
                            "motion_min_area": 100,
                            "motion_min_score": 0.01,
                        },
                        "recording": {
                            "root": str(tmp / "records"),
                            "pre_event_seconds": 2.0,
                            "post_event_seconds": 5.0,
                            "merge_gap_seconds": 5.0,
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

            context = build_context(config_path, include_camera=False)
            day_dir = bootstrap_storage(context.config)

            self.assertTrue(day_dir.exists())
            self.assertEqual(day_dir.parent.parent.parent, tmp / "records")


if __name__ == "__main__":
    unittest.main()
