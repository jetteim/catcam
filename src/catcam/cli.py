from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
import logging

from catcam.app import bootstrap_storage, build_context
from catcam.logging_utils import configure_logging
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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging()
    context = build_context(args.config)
    logger = logging.getLogger("catcam.cli")
    logger.info("Loaded profile %s", context.config.profile)

    if args.command == "show-config":
        print(json.dumps(asdict(context.config), indent=2, default=str))
        return 0

    if args.command == "bootstrap-storage":
        print(bootstrap_storage(context))
        return 0

    if args.command == "sample-clip-path":
        clip_path, meta_path = build_clip_paths(
            root=context.config.recording.root,
            timestamp=datetime.now(),
            label="cat",
            event_id="example123",
            container=context.config.recording.container,
        )
        print(json.dumps({"clip_path": str(clip_path), "metadata_path": str(meta_path)}, indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
