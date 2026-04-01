from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
import logging
from pathlib import Path

from catcam.app import bootstrap_storage, build_context
from catcam.benchmark import BenchmarkOptions, benchmark_pipeline
from catcam.config import load_config
from catcam.deploy import render_systemd_unit
from catcam.logging_utils import configure_logging
from catcam.pipeline.detector import smoke_test_detector
from catcam.runtime import CatCamRuntime, RunOptions
from catcam.storage.paths import build_clip_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="catcam")
    parser.add_argument(
        "--config",
        default="configs/macos-dev.json",
        help="Path to the runtime JSON config profile.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("show-config", help="Print the resolved runtime config as JSON.")
    subparsers.add_parser("bootstrap-storage", help="Create today's recording directory.")
    subparsers.add_parser("sample-clip-path", help="Print a sample clip and metadata path.")
    run_parser = subparsers.add_parser("run", help="Run the capture pipeline.")
    run_parser.add_argument("--input", help="Optional path to a video file for replay testing.")
    run_parser.add_argument("--max-frames", type=int, help="Stop after N frames.")
    run_parser.add_argument("--display", action="store_true", help="Show a preview window.")
    verify_camera = subparsers.add_parser("verify-camera", help="Start the camera backend and sample frames.")
    verify_camera.add_argument("--frames", type=int, default=30, help="Number of frames to sample.")
    benchmark = subparsers.add_parser("benchmark", help="Benchmark motion and detector throughput.")
    benchmark.add_argument("--input", help="Optional replay file path for repeatable benchmarking.")
    benchmark.add_argument("--frames", type=int, default=180, help="Number of frames to benchmark.")
    benchmark.add_argument(
        "--detector-mode",
        choices=("motion-gated", "always"),
        default="motion-gated",
        help="Run detector only on motion frames or on every frame.",
    )
    verify_model = subparsers.add_parser("verify-model", help="Verify that the detector model file exists.")
    verify_model.add_argument("--model", help="Override model path for verification.")
    print_systemd_unit = subparsers.add_parser(
        "print-systemd-unit",
        help="Render a systemd unit for the current checkout.",
    )
    print_systemd_unit.add_argument(
        "--project-root",
        default=".",
        help="Path to the CatCam checkout used for WorkingDirectory and ExecStart.",
    )
    print_systemd_unit.add_argument(
        "--service-user",
        required=True,
        help="Linux user that will own the service process.",
    )
    print_systemd_unit.add_argument(
        "--config",
        help="Absolute or relative config path to use in ExecStart.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging()
    logger = logging.getLogger("catcam.cli")

    if args.command == "show-config":
        config = load_runtime_config(args.config, logger)
        print(json.dumps(asdict(config), indent=2, default=str))
        return 0

    if args.command == "bootstrap-storage":
        config = load_runtime_config(args.config, logger)
        print(bootstrap_storage(config))
        return 0

    if args.command == "sample-clip-path":
        config = load_runtime_config(args.config, logger)
        clip_path, meta_path = build_clip_paths(
            root=config.recording.root,
            timestamp=datetime.now(),
            label="cat",
            event_id="example123",
            container=config.recording.container,
        )
        print(json.dumps({"clip_path": str(clip_path), "metadata_path": str(meta_path)}, indent=2))
        return 0

    if args.command == "verify-camera":
        context = build_context(args.config, include_camera=True)
        result = inspect_camera(context, frames=args.frames)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "benchmark":
        result = benchmark_pipeline(
            BenchmarkOptions(
                config_path=args.config,
                input_path=args.input,
                frames=args.frames,
                detector_mode=args.detector_mode,
            )
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "verify-model":
        config = load_runtime_config(args.config, logger)
        model_path = Path(args.model) if args.model else config.detection.model_path
        detection_config = config.detection
        if args.model:
            detection_config.model_path = model_path
        result = {
            "model_path": str(model_path),
            "exists": model_path.exists(),
        }
        if model_path.exists():
            result.update(smoke_test_detector(detection_config))
        print(json.dumps(result, indent=2))
        return 0 if model_path.exists() else 1

    if args.command == "print-systemd-unit":
        print(
            render_systemd_unit(
                project_root=args.project_root,
                service_user=args.service_user,
                config_path=args.config,
            ),
            end="",
        )
        return 0

    if args.command == "run":
        runtime = CatCamRuntime(
            RunOptions(
                config_path=args.config,
                input_path=args.input,
                max_frames=args.max_frames,
                display=args.display,
            )
        )
        return runtime.run()

    parser.error(f"unknown command: {args.command}")
    return 2


def load_runtime_config(config_path: str, logger: logging.Logger):
    config = load_config(config_path)
    logger.info("Loaded profile %s", config.profile)
    return config


def inspect_camera(context, frames: int) -> dict[str, object]:
    if context.camera is None:
        raise RuntimeError("camera backend is not configured")
    if frames <= 0:
        raise ValueError("frames must be positive")

    camera = context.camera
    sampled = []
    camera.start()
    try:
        for _ in range(frames):
            sampled.append(camera.read())
    finally:
        camera.stop()

    first = sampled[0]
    last = sampled[-1]
    elapsed = max(0.0, last.monotonic_seconds - first.monotonic_seconds)
    observed_fps = ((len(sampled) - 1) / elapsed) if elapsed > 0 else None
    shape = tuple(int(value) for value in first.image.shape)
    return {
        "backend": context.config.camera.backend,
        "device": context.config.camera.device,
        "requested_fps": context.config.camera.fps,
        "sampled_frames": len(sampled),
        "observed_fps": observed_fps,
        "frame_shape": shape,
    }


if __name__ == "__main__":
    raise SystemExit(main())
