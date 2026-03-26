from __future__ import annotations

from catcam.pipeline.baby_resolver import BabyResolver
from catcam.types import Detection, MotionAnalysis


def select_target_detections(
    detections: list[Detection],
    motion: MotionAnalysis,
    frame_shape: tuple[int, int, int],
    baby_resolver: BabyResolver,
    min_motion_fraction: float = 0.05,
) -> list[Detection]:
    if motion.mask is None:
        return []

    results: list[Detection] = []
    for detection in detections:
        resolved = baby_resolver.resolve(detection, frame_shape)
        if not resolved:
            continue
        motion_fraction = foreground_fraction(motion.mask, detection.bbox)
        if motion_fraction < min_motion_fraction:
            continue
        results.append(
            Detection(
                label=resolved,
                original_label=detection.label,
                confidence=detection.confidence,
                bbox=detection.bbox,
            )
        )
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
