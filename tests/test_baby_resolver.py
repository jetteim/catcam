import unittest

from catcam.config import BabyResolverConfig
from catcam.pipeline.baby_resolver import BabyResolver
from catcam.types import Detection


class BabyResolverTests(unittest.TestCase):
    def test_cat_passthrough(self) -> None:
        resolver = BabyResolver(BabyResolverConfig(mode="roi_person_is_baby", roi=(0.2, 0.2, 0.8, 0.8)))
        resolved = resolver.resolve(
            Detection(label="cat", original_label="cat", confidence=0.9, bbox=(10, 10, 50, 50)),
            (100, 100, 3),
        )
        self.assertEqual(resolved, "cat")

    def test_person_in_roi_resolves_to_baby(self) -> None:
        resolver = BabyResolver(BabyResolverConfig(mode="roi_person_is_baby", roi=(0.2, 0.2, 0.8, 0.8)))
        resolved = resolver.resolve(
            Detection(label="person", original_label="person", confidence=0.9, bbox=(30, 30, 50, 60)),
            (100, 100, 3),
        )
        self.assertEqual(resolved, "baby")


if __name__ == "__main__":
    unittest.main()
