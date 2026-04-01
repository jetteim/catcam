#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODEL_DIR="$ROOT/models/opencv_yolox"
mkdir -p "$MODEL_DIR"

curl -fsSL "https://huggingface.co/opencv/object_detection_yolox/resolve/main/demo.py" \
  -o "$MODEL_DIR/opencv_demo.py"
curl -fsSL "https://huggingface.co/opencv/object_detection_yolox/resolve/main/yolox.py" \
  -o "$MODEL_DIR/opencv_yolox_ref.py"
curl -fsSL "https://huggingface.co/opencv/object_detection_yolox/resolve/main/object_detection_yolox_2022nov.onnx" \
  -o "$MODEL_DIR/object_detection_yolox_2022nov.onnx"

echo "Model assets synced to $MODEL_DIR"
