from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from catcam.config import DetectionConfig
from catcam.types import Detection

COCO_CLASSES = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush",
)


class Detector:
    def detect(self, frame) -> list[Detection]:
        raise NotImplementedError


class NoopDetector(Detector):
    def detect(self, frame) -> list[Detection]:
        return []


class MockCatDetector(Detector):
    def detect(self, frame) -> list[Detection]:
        bright = np.argwhere(frame.max(axis=2) >= 200)
        if bright.size == 0:
            return []
        y0, x0 = bright.min(axis=0)
        y1, x1 = bright.max(axis=0)
        return [
            Detection(
                label="cat",
                original_label="cat",
                confidence=0.99,
                bbox=(float(x0), float(y0), float(x1 + 1), float(y1 + 1)),
            )
        ]


class OpenCVYoloXDetector(Detector):
    def __init__(self, model_path: Path, confidence_threshold: float, nms_threshold: float) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for OpenCV YOLOX detection") from exc

        self._cv2 = cv2
        self.input_size = (640, 640)
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.net = cv2.dnn.readNet(str(model_path))
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self._grids, self._expanded_strides = self._generate_anchors()

    def detect(self, frame) -> list[Detection]:
        cv2 = self._cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        blob, scale = letterbox(rgb, self.input_size)
        input_blob = np.transpose(blob, (2, 0, 1))[np.newaxis, :, :, :]

        self.net.setInput(input_blob)
        outputs = self.net.forward(self.net.getUnconnectedOutLayersNames())[0]
        dets = self._postprocess(outputs)

        results: list[Detection] = []
        for det in dets:
            x0, y0, x1, y1 = (det[:4] / scale).astype(np.float32)
            class_id = int(det[-1])
            label = COCO_CLASSES[class_id]
            if label not in {"cat", "person"}:
                continue
            results.append(
                Detection(
                    label=label,
                    original_label=label,
                    confidence=float(det[-2]),
                    bbox=(float(x0), float(y0), float(x1), float(y1)),
                )
            )
        return results

    def _postprocess(self, outputs) -> np.ndarray:
        cv2 = self._cv2
        dets = outputs[0]
        dets[:, :2] = (dets[:, :2] + self._grids) * self._expanded_strides
        dets[:, 2:4] = np.exp(dets[:, 2:4]) * self._expanded_strides

        boxes = dets[:, :4]
        boxes_xyxy = np.ones_like(boxes)
        boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.0
        boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.0
        boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.0
        boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.0

        scores = dets[:, 4:5] * dets[:, 5:]
        max_scores = np.amax(scores, axis=1)
        max_scores_idx = np.argmax(scores, axis=1)
        keep = cv2.dnn.NMSBoxesBatched(
            boxes_xyxy.tolist(),
            max_scores.tolist(),
            max_scores_idx.tolist(),
            self.confidence_threshold,
            self.nms_threshold,
        )
        if len(keep) == 0:
            return np.array([])
        candidates = np.concatenate(
            [boxes_xyxy, max_scores[:, None], max_scores_idx[:, None]],
            axis=1,
        )
        return candidates[np.array(keep).reshape(-1)]

    def _generate_anchors(self) -> tuple[np.ndarray, np.ndarray]:
        strides = [8, 16, 32]
        grids = []
        expanded_strides = []
        hsizes = [self.input_size[0] // stride for stride in strides]
        wsizes = [self.input_size[1] // stride for stride in strides]

        for hsize, wsize, stride in zip(hsizes, wsizes, strides):
            xv, yv = np.meshgrid(np.arange(hsize), np.arange(wsize))
            grid = np.stack((xv, yv), 2).reshape(1, -1, 2)
            grids.append(grid)
            expanded_strides.append(np.full((*grid.shape[:2], 1), stride))

        return np.concatenate(grids, 1), np.concatenate(expanded_strides, 1)


def create_detector(config: DetectionConfig) -> Detector:
    if config.backend == "disabled":
        return NoopDetector()
    if config.backend == "mock_cat":
        return MockCatDetector()
    if config.backend == "opencv_yolox":
        return OpenCVYoloXDetector(
            model_path=config.model_path,
            confidence_threshold=config.confidence_threshold,
            nms_threshold=config.nms_threshold,
        )
    raise ValueError(f"Unsupported detector backend: {config.backend}")


def smoke_test_detector(config: DetectionConfig) -> dict[str, object]:
    detector = create_detector(config)
    payload = {"backend": config.backend, "model_path": str(config.model_path)}
    if isinstance(detector, OpenCVYoloXDetector):
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        detections = detector.detect(dummy)
        payload["loaded"] = True
        payload["dummy_detections"] = len(detections)
        return payload
    payload["loaded"] = True
    payload["dummy_detections"] = 0
    return payload


def letterbox(srcimg, target_size=(640, 640)):
    import cv2

    padded = np.ones((target_size[0], target_size[1], 3), dtype=np.float32) * 114.0
    ratio = min(target_size[0] / srcimg.shape[0], target_size[1] / srcimg.shape[1])
    resized = cv2.resize(
        srcimg,
        (int(srcimg.shape[1] * ratio), int(srcimg.shape[0] * ratio)),
        interpolation=cv2.INTER_LINEAR,
    ).astype(np.float32)
    padded[: int(srcimg.shape[0] * ratio), : int(srcimg.shape[1] * ratio)] = resized
    return padded, ratio


@dataclass
class TargetDetection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    motion_fraction: float
