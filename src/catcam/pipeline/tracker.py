from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from catcam.types import Detection, TargetCandidate, TrackedTarget


@dataclass
class _TrackState:
    track_id: int
    detection: Detection
    missed_frames: int = 0


class SimpleTracker:
    def __init__(
        self,
        max_missing_frames: int,
        min_iou: float,
        max_centroid_distance: float,
        min_motion_score: float,
        cat_motion_min_score_scale: float = 0.5,
        cat_motion_min_fraction: float = 0.015,
        cat_bbox_motion_min_pixels: float = 4.0,
        cat_bbox_area_change_min_ratio: float = 0.04,
    ) -> None:
        self.max_missing_frames = max_missing_frames
        self.min_iou = min_iou
        self.max_centroid_distance = max_centroid_distance
        self.min_motion_score = min_motion_score
        self.cat_motion_min_score_scale = cat_motion_min_score_scale
        self.cat_motion_min_fraction = cat_motion_min_fraction
        self.cat_bbox_motion_min_pixels = cat_bbox_motion_min_pixels
        self.cat_bbox_area_change_min_ratio = cat_bbox_area_change_min_ratio
        self._tracks: dict[int, _TrackState] = {}
        self._next_track_id = 1

    def update(self, candidates: list[TargetCandidate]) -> list[TrackedTarget]:
        matches, unmatched_tracks, unmatched_candidates = self._match_candidates(candidates)
        tracked_targets: list[TrackedTarget] = []

        for track_id, candidate_index in matches:
            state = self._tracks[track_id]
            candidate = candidates[candidate_index]
            tracked = self._build_tracked_target(state.detection, candidate, track_id)
            state.detection = tracked.detection
            state.missed_frames = 0
            tracked_targets.append(tracked)

        for candidate_index in unmatched_candidates:
            candidate = candidates[candidate_index]
            track_id = self._allocate_track_id()
            detection = Detection(
                label=candidate.resolved_label,
                original_label=candidate.detection.label,
                confidence=candidate.detection.confidence,
                bbox=candidate.detection.bbox,
            )
            self._tracks[track_id] = _TrackState(track_id=track_id, detection=detection)
            motion_score = 0.6 * candidate.motion_fraction
            tracked_targets.append(
                TrackedTarget(
                    track_id=track_id,
                    detection=detection,
                    motion_fraction=candidate.motion_fraction,
                    centroid_distance=0.0,
                    area_change_ratio=0.0,
                    motion_score=motion_score,
                    active_motion=self._is_active_motion(
                        candidate.resolved_label,
                        motion_score,
                        candidate.motion_fraction,
                        centroid_distance=0.0,
                        area_change_ratio=0.0,
                    ),
                )
            )

        for track_id in unmatched_tracks:
            state = self._tracks[track_id]
            state.missed_frames += 1
            if state.missed_frames > self.max_missing_frames:
                del self._tracks[track_id]

        tracked_targets.sort(key=lambda item: item.track_id)
        return tracked_targets

    def _match_candidates(self, candidates: list[TargetCandidate]) -> tuple[list[tuple[int, int]], set[int], set[int]]:
        unmatched_tracks = set(self._tracks.keys())
        unmatched_candidates = set(range(len(candidates)))
        potential_matches: list[tuple[float, float, int, int]] = []

        for track_id, state in self._tracks.items():
            for candidate_index, candidate in enumerate(candidates):
                if state.detection.label != candidate.resolved_label:
                    continue
                iou = bbox_iou(state.detection.bbox, candidate.detection.bbox)
                distance = centroid_distance(state.detection.bbox, candidate.detection.bbox)
                if iou < self.min_iou and distance > self.max_centroid_distance:
                    continue
                potential_matches.append((-iou, distance, track_id, candidate_index))

        potential_matches.sort()
        matches: list[tuple[int, int]] = []
        for _, _, track_id, candidate_index in potential_matches:
            if track_id not in unmatched_tracks or candidate_index not in unmatched_candidates:
                continue
            unmatched_tracks.remove(track_id)
            unmatched_candidates.remove(candidate_index)
            matches.append((track_id, candidate_index))

        return matches, unmatched_tracks, unmatched_candidates

    def _build_tracked_target(
        self,
        previous_detection: Detection,
        candidate: TargetCandidate,
        track_id: int,
    ) -> TrackedTarget:
        distance = centroid_distance(previous_detection.bbox, candidate.detection.bbox)
        prev_area = bbox_area(previous_detection.bbox)
        curr_area = bbox_area(candidate.detection.bbox)
        area_change_ratio = abs(curr_area - prev_area) / max(prev_area, 1.0)
        displacement_score = min(1.0, distance / max(bbox_diagonal(previous_detection.bbox), 1.0))
        size_change_score = min(1.0, area_change_ratio)
        motion_score = (
            0.6 * candidate.motion_fraction
            + 0.3 * displacement_score
            + 0.1 * size_change_score
        )
        detection = Detection(
            label=candidate.resolved_label,
            original_label=candidate.detection.label,
            confidence=candidate.detection.confidence,
            bbox=candidate.detection.bbox,
        )
        return TrackedTarget(
            track_id=track_id,
            detection=detection,
            motion_fraction=candidate.motion_fraction,
            centroid_distance=distance,
            area_change_ratio=area_change_ratio,
            motion_score=motion_score,
            active_motion=self._is_active_motion(
                candidate.resolved_label,
                motion_score,
                candidate.motion_fraction,
                centroid_distance=distance,
                area_change_ratio=area_change_ratio,
            ),
        )

    def _allocate_track_id(self) -> int:
        track_id = self._next_track_id
        self._next_track_id += 1
        return track_id

    def _motion_threshold_for_label(self, label: str) -> float:
        if label == "cat":
            return self.min_motion_score * max(0.0, self.cat_motion_min_score_scale)
        return self.min_motion_score

    def _is_active_motion(
        self,
        label: str,
        motion_score: float,
        motion_fraction: float,
        centroid_distance: float,
        area_change_ratio: float,
    ) -> bool:
        if label == "cat":
            if motion_fraction >= self.cat_motion_min_fraction:
                return True
            if centroid_distance >= self.cat_bbox_motion_min_pixels:
                return True
            if area_change_ratio >= self.cat_bbox_area_change_min_ratio:
                return True
        return motion_score >= self._motion_threshold_for_label(label)


def bbox_iou(lhs: tuple[float, float, float, float], rhs: tuple[float, float, float, float]) -> float:
    left = max(lhs[0], rhs[0])
    top = max(lhs[1], rhs[1])
    right = min(lhs[2], rhs[2])
    bottom = min(lhs[3], rhs[3])
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    union = bbox_area(lhs) + bbox_area(rhs) - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def centroid_distance(lhs: tuple[float, float, float, float], rhs: tuple[float, float, float, float]) -> float:
    lhs_cx = (lhs[0] + lhs[2]) / 2.0
    lhs_cy = (lhs[1] + lhs[3]) / 2.0
    rhs_cx = (rhs[0] + rhs[2]) / 2.0
    rhs_cy = (rhs[1] + rhs[3]) / 2.0
    return hypot(lhs_cx - rhs_cx, lhs_cy - rhs_cy)


def bbox_area(bbox: tuple[float, float, float, float]) -> float:
    width = max(0.0, bbox[2] - bbox[0])
    height = max(0.0, bbox[3] - bbox[1])
    return width * height


def bbox_diagonal(bbox: tuple[float, float, float, float]) -> float:
    width = max(0.0, bbox[2] - bbox[0])
    height = max(0.0, bbox[3] - bbox[1])
    return hypot(width, height)
