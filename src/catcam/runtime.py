from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

import cv2

from catcam.app import build_context
from catcam.camera.factory import create_camera_backend
from catcam.pipeline.baby_resolver import BabyResolver
from catcam.pipeline.detector import create_detector
from catcam.pipeline.motion import BackgroundMotionDetector
from catcam.pipeline.targeting import select_target_detections
from catcam.recording.writer import ClipRecorder
from catcam.types import Detection, TrackMotionObservation


@dataclass
class RunOptions:
    config_path: str
    input_path: str | None = None
    max_frames: int | None = None
    display: bool = False


class CatCamRuntime:
    def __init__(self, options: RunOptions) -> None:
        self.logger = logging.getLogger("catcam.runtime")
        self.context = build_context(options.config_path, input_path=options.input_path)
        self.options = options
        self.camera = self.context.camera
        self.motion = BackgroundMotionDetector(
            min_area=self.context.config.analysis.motion_min_area,
            min_score=self.context.config.analysis.motion_min_score,
        )
        self.detector = create_detector(self.context.config.detection)
        self.baby_resolver = BabyResolver(self.context.config.baby_resolver)
        self.recorder = ClipRecorder(self.context.config)

    def run(self) -> int:
        processed = 0
        self.camera.start()
        last_packet = None
        try:
            while True:
                if self.options.max_frames is not None and processed >= self.options.max_frames:
                    break
                try:
                    packet = self.camera.read()
                except EOFError:
                    break
                last_packet = packet

                frame = packet.image
                analysis_frame = cv2.resize(
                    frame,
                    (self.context.config.analysis.width, self.context.config.analysis.height),
                )
                motion = self.motion.analyze(analysis_frame)
                if processed < self.context.config.analysis.warmup_frames:
                    self.context.pre_event_buffer.append(packet)
                    processed += 1
                    continue
                detections: list[Detection] = []
                if motion.present or self.recorder.active:
                    detections = self.detector.detect(analysis_frame)
                scaled_detections = [
                    scale_detection(
                        detection,
                        src_shape=analysis_frame.shape,
                        dst_shape=frame.shape,
                    )
                    for detection in detections
                ]
                target_detections = select_target_detections(
                    scaled_detections,
                    scale_motion_mask(motion, frame.shape),
                    frame_shape=frame.shape,
                    baby_resolver=self.baby_resolver,
                )

                observation = TrackMotionObservation(
                    timestamp=packet.wall_time,
                    target_motion=bool(target_detections),
                    labels=[det.label for det in target_detections],
                    motion_score=motion.score,
                )
                decision = self.context.event_engine.process(observation)
                pre_event_frames = self.context.pre_event_buffer.snapshot() + [packet]

                if decision.action == "start_recording":
                    self.recorder.start(decision, pre_event_frames)
                    self.recorder.write_frame(packet, target_detections)
                    self.logger.info("Started recording %s (%s)", decision.event_id, decision.label)
                elif self.recorder.active:
                    self.recorder.write_frame(packet, target_detections)
                    if decision.action == "finalize_recording":
                        record = self.recorder.finalize(decision)
                        self.logger.info("Finalized clip %s", record.clip_path)

                self.context.pre_event_buffer.append(packet)

                if self.options.display:
                    preview = draw_preview(frame, target_detections, motion.present)
                    cv2.imshow("catcam", preview)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                processed += 1
        finally:
            if self.recorder.active and last_packet is not None:
                decision = self.context.event_engine.process(
                    TrackMotionObservation(
                        timestamp=last_packet.wall_time,
                        target_motion=False,
                        labels=[],
                    )
                )
                if decision.action != "finalize_recording":
                    decision.action = "finalize_recording"
                    decision.event_end = last_packet.wall_time
                record = self.recorder.finalize(decision)
                self.logger.info("Finalized clip at shutdown %s", record.clip_path)
            self.camera.stop()
            if self.options.display:
                cv2.destroyAllWindows()
        return 0


def scale_detection(detection: Detection, src_shape: tuple[int, int, int], dst_shape: tuple[int, int, int]) -> Detection:
    src_h, src_w = src_shape[:2]
    dst_h, dst_w = dst_shape[:2]
    x_scale = dst_w / src_w
    y_scale = dst_h / src_h
    x0, y0, x1, y1 = detection.bbox
    return Detection(
        label=detection.label,
        original_label=detection.original_label,
        confidence=detection.confidence,
        bbox=(x0 * x_scale, y0 * y_scale, x1 * x_scale, y1 * y_scale),
    )


def scale_motion_mask(motion, dst_shape: tuple[int, int, int]):
    mask = cv2.resize(motion.mask, (dst_shape[1], dst_shape[0]), interpolation=cv2.INTER_NEAREST)
    motion.mask = mask
    return motion


def draw_preview(frame, detections: list[Detection], motion_present: bool):
    preview = frame.copy()
    color = (0, 255, 0) if motion_present else (100, 100, 100)
    cv2.putText(preview, f"motion={motion_present}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    for detection in detections:
        x0, y0, x1, y1 = [int(value) for value in detection.bbox]
        cv2.rectangle(preview, (x0, y0), (x1, y1), (0, 255, 0), 2)
        cv2.putText(
            preview,
            f"{detection.label}:{detection.confidence:.2f}",
            (x0, max(20, y0 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
    return preview
