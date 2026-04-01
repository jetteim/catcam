from __future__ import annotations

from pathlib import Path
import unittest


class PackagingTests(unittest.TestCase):
    def test_ml_extra_is_a_compatibility_shim(self) -> None:
        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        pyproject_text = pyproject_path.read_text(encoding="utf-8")

        self.assertIn("ml = []", pyproject_text)
        self.assertNotIn("onnxruntime", pyproject_text)


if __name__ == "__main__":
    unittest.main()
