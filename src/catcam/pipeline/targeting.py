from __future__ import annotations

from catcam.pipeline.baby_resolver import BabyResolver
from catcam.types import Detection, MotionAnalysis, TargetCandidate


def select_target_candidates(
    detections: list[Detection],
    motion: MotionAnalysis,
    frame_shape: tuple[int, int, int],
    baby_resolver: BabyResolver,
    min_confidence: float = 0.35,
) -> list[TargetCandidate]:
    if motion.mask is None:
        return []

    results: list[TargetCandidate] = []
    for detection in detections:
        if detection.confidence < min_confidence:
            continue
        resolved = baby_resolver.resolve(detection, frame_shape)
        if not resolved:
            continue
        motion_fraction = foreground_fraction(motion.mask, detection.bbox)
        results.append(TargetCandidate(detection=detection, resolved_label=resolved, motion_fraction=motion_fraction))
    return results


def foreground_fraction(mask, bbox: tuple[float, float, float, float]) -> float:
    x0, y0, x1, y1 = [int(value) for value in bbox]
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(mask.shape[1], max(x0 + 1, x1))
    y1 = min(mask.shape[0], max(y0 + 1, y1))
    roi = mask[y0:y1, x0:x1]
    if roi.size == 0:
        return 0.0
    return float((roi > 0).sum()) / float(roi.size)
