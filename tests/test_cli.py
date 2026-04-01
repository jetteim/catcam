from __future__ import annotations

from io import StringIO
from pathlib import Path
import json
import tempfile
from unittest.mock import patch
import contextlib
import unittest

from catcam import cli


class CliTests(unittest.TestCase):
    def test_print_systemd_unit_does_not_require_runtime_config(self) -> None:
        stdout = StringIO()

        with patch("sys.argv", ["catcam", "print-systemd-unit", "--service-user", "pi"]), patch(
            "catcam.cli.load_config",
            side_effect=AssertionError("load_config should not be called for print-systemd-unit"),
        ), contextlib.redirect_stdout(stdout):
            exit_code = cli.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("User=pi", stdout.getvalue())

    def test_verify_model_returns_nonzero_when_model_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            config_path = tmp / "config.json"
            config_path.write_text(
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
                            "root": str(tmp / "records"),
                            "pre_event_seconds": 2.0,
                            "post_event_seconds": 0.2,
                            "merge_gap_seconds": 0.2,
                            "container": "mp4",
                        },
                        "detection": {
                            "backend": "opencv_yolox",
                            "model_path": str(tmp / "missing.onnx"),
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
            stdout = StringIO()

            with patch("sys.argv", ["catcam", "--config", str(config_path), "verify-model"]), contextlib.redirect_stdout(stdout):
                exit_code = cli.main()

            self.assertEqual(exit_code, 1)
            self.assertIn('"exists": false', stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
