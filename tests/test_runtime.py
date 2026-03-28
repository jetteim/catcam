import unittest

from catcam.runtime import should_run_detection


class RuntimeDetectionPollingTests(unittest.TestCase):
    def test_runs_detector_when_motion_is_present(self) -> None:
        self.assertTrue(
            should_run_detection(
                processed=3,
                motion_present=True,
                recorder_active=False,
                idle_interval_frames=7,
            )
        )

    def test_runs_detector_while_recording(self) -> None:
        self.assertTrue(
            should_run_detection(
                processed=3,
                motion_present=False,
                recorder_active=True,
                idle_interval_frames=7,
            )
        )

    def test_polls_detector_periodically_while_idle(self) -> None:
        self.assertTrue(
            should_run_detection(
                processed=14,
                motion_present=False,
                recorder_active=False,
                idle_interval_frames=7,
            )
        )
        self.assertFalse(
            should_run_detection(
                processed=15,
                motion_present=False,
                recorder_active=False,
                idle_interval_frames=7,
            )
        )


if __name__ == "__main__":
    unittest.main()
