from __future__ import annotations

from pathlib import Path
import unittest

from catcam.deploy import render_systemd_unit


class DeployTests(unittest.TestCase):
    def test_render_systemd_unit_uses_checkout_paths(self) -> None:
        project_root = Path("/home/pi/catcam")

        unit = render_systemd_unit(project_root=project_root, service_user="camera")

        self.assertIn("User=camera", unit)
        self.assertIn("WorkingDirectory=/home/pi/catcam", unit)
        self.assertIn(
            "ExecStart=/home/pi/catcam/.venv/bin/python -m catcam.cli --config /home/pi/catcam/configs/rpi4-prod.json run",
            unit,
        )
        self.assertNotIn("/opt/catcam", unit)

    def test_render_systemd_unit_accepts_explicit_config_path(self) -> None:
        project_root = Path("/srv/catcam")
        config_path = project_root / "configs/custom.json"

        unit = render_systemd_unit(
            project_root=project_root,
            service_user="pi",
            config_path=config_path,
        )

        self.assertIn("ExecStart=/srv/catcam/.venv/bin/python -m catcam.cli --config /srv/catcam/configs/custom.json run", unit)


if __name__ == "__main__":
    unittest.main()
