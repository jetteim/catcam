from __future__ import annotations

from dataclasses import dataclass
import time

import cv2

from catcam.app import build_context
from catcam.pipeline.detector import create_detector
from catcam.pipeline.motion import BackgroundMotionDetector


@dataclass
class BenchmarkOptions:
    config_path: str
    input_path: str | None = None
    frames: int = 180
    detector_mode: str = "motion-gated"


def benchmark_pipeline(options: BenchmarkOptions) -> dict[str, object]:
    if options.frames <= 0:
        raise ValueError("frames must be positive")
    if options.detector_mode not in {"motion-gated", "always"}:
        raise ValueError("detector_mode must be 'motion-gated' or 'always'")

    context = build_context(options.config_path, input_path=options.input_path, include_camera=True)
    if context.camera is None:
        raise RuntimeError("benchmark requires a camera backend")

    camera = context.camera
    motion = BackgroundMotionDetector(
        min_area=context.config.analysis.motion_min_area,
        min_score=context.config.analysis.motion_min_score,
    )
    detector = create_detector(context.config.detection)

    sampled_frames = 0
    detector_frames = 0
    detector_time = 0.0
    motion_time = 0.0
    total_start = time.perf_counter()

    camera.start()
    try:
        while sampled_frames < options.frames:
            try:
                packet = camera.read()
            except EOFError:
                break

            analysis_frame = cv2.resize(
                packet.image,
                (context.config.analysis.width, context.config.analysis.height),
            )
            motion_start = time.perf_counter()
            motion_result = motion.analyze(analysis_frame)
            motion_time += time.perf_counter() - motion_start

            should_detect = options.detector_mode == "always" or motion_result.present
            if should_detect:
                detect_start = time.perf_counter()
                detector.detect(analysis_frame)
                detector_time += time.perf_counter() - detect_start
                detector_frames += 1
            sampled_frames += 1
    finally:
        camera.stop()

    elapsed = time.perf_counter() - total_start
    return {
        "profile": context.config.profile,
        "camera_backend": context.config.camera.backend,
        "input_path": options.input_path,
        "frames": sampled_frames,
        "elapsed_seconds": elapsed,
        "pipeline_fps": (sampled_frames / elapsed) if elapsed > 0 else None,
        "detector_mode": options.detector_mode,
        "detector_invocations": detector_frames,
        "motion_avg_ms": ((motion_time / sampled_frames) * 1000.0) if sampled_frames else 0.0,
        "detector_avg_ms": ((detector_time / detector_frames) * 1000.0) if detector_frames else 0.0,
        "detector_share": (detector_frames / sampled_frames) if sampled_frames else 0.0,
        "analysis_size": [context.config.analysis.width, context.config.analysis.height],
    }
