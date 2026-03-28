import unittest

from catcam.pipeline.tracker import SimpleTracker
from catcam.types import Detection, TargetCandidate


class SimpleTrackerTests(unittest.TestCase):
    def test_reuses_track_id_for_same_label_with_overlap(self) -> None:
        tracker = SimpleTracker(
            max_missing_frames=2,
            min_iou=0.3,
            max_centroid_distance=80.0,
            min_motion_score=0.03,
        )
        first = tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(10, 10, 50, 50)),
                    resolved_label="cat",
                    motion_fraction=0.10,
                )
            ]
        )
        second = tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(14, 12, 54, 52)),
                    resolved_label="cat",
                    motion_fraction=0.12,
                )
            ]
        )

        self.assertEqual(first[0].track_id, second[0].track_id)

    def test_motion_score_stays_below_threshold_for_static_box_with_weak_foreground(self) -> None:
        tracker = SimpleTracker(
            max_missing_frames=2,
            min_iou=0.3,
            max_centroid_distance=80.0,
            min_motion_score=0.08,
        )
        tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="baby", original_label="person", confidence=0.9, bbox=(20, 20, 80, 100)),
                    resolved_label="baby",
                    motion_fraction=0.03,
                )
            ]
        )
        tracked = tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="baby", original_label="person", confidence=0.9, bbox=(20, 20, 80, 100)),
                    resolved_label="baby",
                    motion_fraction=0.03,
                )
            ]
        )

        self.assertFalse(tracked[0].active_motion)
        self.assertLess(tracked[0].motion_score, 0.08)

    def test_motion_score_crosses_threshold_when_box_moves(self) -> None:
        tracker = SimpleTracker(
            max_missing_frames=2,
            min_iou=0.3,
            max_centroid_distance=80.0,
            min_motion_score=0.08,
        )
        tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(10, 10, 50, 50)),
                    resolved_label="cat",
                    motion_fraction=0.04,
                )
            ]
        )
        tracked = tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(22, 10, 62, 50)),
                    resolved_label="cat",
                    motion_fraction=0.04,
                )
            ]
        )

        self.assertTrue(tracked[0].active_motion)
        self.assertGreaterEqual(tracked[0].motion_score, 0.08)

    def test_cat_uses_lower_motion_threshold_after_detection(self) -> None:
        tracker = SimpleTracker(
            max_missing_frames=2,
            min_iou=0.3,
            max_centroid_distance=80.0,
            min_motion_score=0.08,
            cat_motion_min_score_scale=0.5,
        )
        tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(10, 10, 50, 50)),
                    resolved_label="cat",
                    motion_fraction=0.03,
                )
            ]
        )
        tracked = tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(16, 10, 56, 50)),
                    resolved_label="cat",
                    motion_fraction=0.03,
                )
            ]
        )

        self.assertTrue(tracked[0].active_motion)
        self.assertLess(tracked[0].motion_score, 0.08)
        self.assertGreaterEqual(tracked[0].motion_score, 0.04)

    def test_cat_small_local_motion_counts_as_active(self) -> None:
        tracker = SimpleTracker(
            max_missing_frames=2,
            min_iou=0.3,
            max_centroid_distance=80.0,
            min_motion_score=0.08,
            cat_motion_min_score_scale=0.35,
            cat_motion_min_fraction=0.015,
        )
        tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(10, 10, 50, 50)),
                    resolved_label="cat",
                    motion_fraction=0.01,
                )
            ]
        )
        tracked = tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(10, 10, 50, 50)),
                    resolved_label="cat",
                    motion_fraction=0.02,
                )
            ]
        )

        self.assertTrue(tracked[0].active_motion)
        self.assertLess(tracked[0].motion_score, 0.028)

    def test_cat_box_shift_counts_as_active_even_with_low_mask_motion(self) -> None:
        tracker = SimpleTracker(
            max_missing_frames=2,
            min_iou=0.3,
            max_centroid_distance=80.0,
            min_motion_score=0.08,
            cat_motion_min_score_scale=0.2,
            cat_motion_min_fraction=0.01,
            cat_bbox_motion_min_pixels=4.0,
            cat_bbox_area_change_min_ratio=0.04,
        )
        tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(10, 10, 50, 50)),
                    resolved_label="cat",
                    motion_fraction=0.002,
                )
            ]
        )
        tracked = tracker.update(
            [
                TargetCandidate(
                    detection=Detection(label="cat", original_label="cat", confidence=0.9, bbox=(15, 10, 55, 50)),
                    resolved_label="cat",
                    motion_fraction=0.002,
                )
            ]
        )

        self.assertTrue(tracked[0].active_motion)
        self.assertLess(tracked[0].motion_score, 0.03)


if __name__ == "__main__":
    unittest.main()
