from __future__ import annotations

from io import StringIO
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


if __name__ == "__main__":
    unittest.main()
