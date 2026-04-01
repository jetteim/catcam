from __future__ import annotations

from pathlib import Path
import unittest


class ScriptTests(unittest.TestCase):
    def test_pi_setup_venv_includes_system_site_packages(self) -> None:
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "pi_setup.sh"
        script_text = script_path.read_text(encoding="utf-8")

        self.assertIn("python3 -m venv --clear --system-site-packages .venv", script_text)


if __name__ == "__main__":
    unittest.main()
