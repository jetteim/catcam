from __future__ import annotations

from pathlib import Path
import unittest


class ScriptTests(unittest.TestCase):
    def test_pi_setup_venv_includes_system_site_packages(self) -> None:
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "pi_setup.sh"
        script_text = script_path.read_text(encoding="utf-8")

        self.assertIn("python3 -m venv --clear --system-site-packages .venv", script_text)

    def test_pi_setup_fetches_model_assets(self) -> None:
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "pi_setup.sh"
        fetch_script_path = Path(__file__).resolve().parents[1] / "scripts" / "fetch_model_assets.sh"

        script_text = script_path.read_text(encoding="utf-8")
        fetch_script_text = fetch_script_path.read_text(encoding="utf-8")

        self.assertIn('"$ROOT/scripts/fetch_model_assets.sh"', script_text)
        self.assertIn("object_detection_yolox_2022nov.onnx", fetch_script_text)
        self.assertIn("https://huggingface.co/opencv/object_detection_yolox/resolve/main/object_detection_yolox_2022nov.onnx", fetch_script_text)


if __name__ == "__main__":
    unittest.main()
