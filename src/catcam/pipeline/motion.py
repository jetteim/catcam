from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from catcam.types import MotionAnalysis

@dataclass
class MotionSignal:
    present: bool
    score: float
    area: int
    mask: Any = None


class MotionGate:
    def __init__(self, min_area: int, min_score: float) -> None:
        self.min_area = min_area
        self.min_score = min_score

    def classify(self, foreground_area: int, motion_score: float) -> MotionSignal:
        present = foreground_area >= self.min_area and motion_score >= self.min_score
        return MotionSignal(present=present, score=motion_score, area=foreground_area)


class BackgroundMotionDetector:
    def __init__(self, min_area: int, min_score: float) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for motion detection") from exc

        self._cv2 = cv2
        self._gate = MotionGate(min_area=min_area, min_score=min_score)
        self._subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300,
            varThreshold=24,
            detectShadows=False,
        )
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    def analyze(self, frame) -> MotionAnalysis:
        cv2 = self._cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = self._subtractor.apply(gray)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._kernel)
        mask = cv2.dilate(mask, self._kernel, iterations=2)

        area = int(cv2.countNonZero(mask))
        motion_score = float(area) / float(mask.shape[0] * mask.shape[1])
        signal = self._gate.classify(area, motion_score)
        return MotionAnalysis(
            present=signal.present,
            score=signal.score,
            area=signal.area,
            mask=mask,
        )
