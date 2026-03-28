import unittest

import numpy as np

from catcam.config import BabyResolverConfig
from catcam.pipeline.baby_resolver import BabyResolver
from catcam.pipeline.targeting import select_target_candidates
from catcam.types import Detection, MotionAnalysis


class TargetingTests(unittest.TestCase):
    def test_uses_configurable_min_confidence(self) -> None:
        detections = [Detection(label="cat", original_label="cat", confidence=0.3, bbox=(10, 10, 40, 40))]
        motion = MotionAnalysis(
            present=True,
            score=0.02,
            area=1200,
            mask=np.full((80, 80), 255, dtype=np.uint8),
        )
        resolver = BabyResolver(BabyResolverConfig(mode="disabled", roi=(0.2, 0.2, 0.8, 0.8)))

        filtered = select_target_candidates(
            detections,
            motion,
            frame_shape=(80, 80, 3),
            baby_resolver=resolver,
            min_confidence=0.35,
        )
        accepted = select_target_candidates(
            detections,
            motion,
            frame_shape=(80, 80, 3),
            baby_resolver=resolver,
            min_confidence=0.25,
        )

        self.assertEqual(filtered, [])
        self.assertEqual(len(accepted), 1)


if __name__ == "__main__":
    unittest.main()
