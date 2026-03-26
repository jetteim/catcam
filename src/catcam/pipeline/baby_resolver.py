from __future__ import annotations

from catcam.config import BabyResolverConfig
from catcam.types import Detection


class BabyResolver:
    def __init__(self, config: BabyResolverConfig) -> None:
        self.config = config

    def resolve(self, detection: Detection, frame_shape: tuple[int, int, int]) -> str | None:
        if detection.label == "cat":
            return "cat"
        if detection.label != "person":
            return None
        if self.config.mode == "disabled":
            return None
        if self.config.mode == "roi_person_is_baby":
            if _bbox_center_in_roi(detection.bbox, frame_shape, self.config.roi):
                return "baby"
        return None


def _bbox_center_in_roi(
    bbox: tuple[float, float, float, float],
    frame_shape: tuple[int, int, int],
    roi: tuple[float, float, float, float],
) -> bool:
    height, width = frame_shape[:2]
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    left = roi[0] * width
    top = roi[1] * height
    right = roi[2] * width
    bottom = roi[3] * height
    return left <= cx <= right and top <= cy <= bottom
