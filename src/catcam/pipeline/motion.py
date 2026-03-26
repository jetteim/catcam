from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MotionSignal:
    present: bool
    score: float
    area: int


class MotionGate:
    def __init__(self, min_area: int, min_score: float) -> None:
        self.min_area = min_area
        self.min_score = min_score

    def classify(self, foreground_area: int, motion_score: float) -> MotionSignal:
        present = foreground_area >= self.min_area and motion_score >= self.min_score
        return MotionSignal(present=present, score=motion_score, area=foreground_area)
