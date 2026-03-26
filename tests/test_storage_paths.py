from datetime import datetime
from pathlib import Path
import unittest

from catcam.storage.paths import build_clip_paths, day_directory


class StoragePathTests(unittest.TestCase):
    def test_day_directory_uses_year_month_day_layout(self) -> None:
        timestamp = datetime(2026, 3, 26, 21, 44, 55)
        self.assertEqual(day_directory("records", timestamp), Path("records/2026/03/26"))

    def test_build_clip_paths_uses_timestamp_label_and_event_id(self) -> None:
        timestamp = datetime(2026, 3, 26, 21, 44, 55)
        clip_path, metadata_path = build_clip_paths(
            root="records",
            timestamp=timestamp,
            label="Cat",
            event_id="abc123",
        )

        self.assertEqual(clip_path, Path("records/2026/03/26/20260326T214455_cat_abc123.mp4"))
        self.assertEqual(metadata_path, Path("records/2026/03/26/20260326T214455_cat_abc123.json"))


if __name__ == "__main__":
    unittest.main()
