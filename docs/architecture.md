# Architecture

## 1. Recommended Stack

### Language Choice

Use Python for the first implementation.

Why Python over Go:

- camera, CV, and edge-ML tooling are much stronger in Python;
- Raspberry Pi camera support is best through `Picamera2`, which is Python-first;
- model export, evaluation, and fallback paths are simpler in Python;
- Go is viable for orchestration, but not the best choice for the CV/ML core.

### Core Libraries

- `opencv-python`: frame processing, motion masks, resizing, morphology, optional webcam capture on macOS.
- `numpy`: frame math and buffering.
- `onnxruntime`: primary offline inference runtime for both macOS and Raspberry Pi OS 64-bit.
- `ultralytics`: model export and training-time tooling only, not required in production runtime.
- `PyYAML` or `pydantic-settings`: config loading.
- `PyAV` or `ffmpeg` subprocess: macOS clip muxing/writing.
- `picamera2`: Raspberry Pi capture and recording backend.
- `systemd`: Raspberry Pi service management.

### Model Choice

Recommended detector strategy:

- `cat`: use a lightweight COCO-class detector.
- `baby`: treat as a staged requirement.

Recommended model path:

1. Start with a small YOLO detector exported to ONNX for `person` and `cat`.
2. For MVP, define a configurable `baby mode`:
- `nursery ROI mode`: if a moving `person` appears inside a configured baby zone, treat it as baby activity.
- `classifier mode`: run a second lightweight baby-vs-adult classifier on person crops.
3. If Raspberry Pi 4 performance is insufficient, export the detector to TFLite/INT8 or NCNN as an optimization phase.

Reasoning:

- `cat` is available in standard label sets.
- `baby` usually is not, so a single off-the-shelf detector will not fully solve your stated requirement.

## 2. System Overview

```text
Camera Backend
  -> Frame Broker
  -> Analysis Pipeline
       -> Motion Gate
       -> Object Detector
       -> Target Tracker
       -> Motion-Within-Target Scorer
       -> Event State Machine
  -> Recorder
       -> Pre-event Ring Buffer
       -> Active Clip Writer
  -> Storage Manager
  -> Metadata + Logs
```

## 3. Component Design

### 3.1 Camera Backend

Interface:

- `start()`
- `read() -> FramePacket`
- `stop()`

Backends:

- `MacCameraBackend`
  - OpenCV `VideoCapture` with macOS AVFoundation backend.
- `PiCameraBackend`
  - `Picamera2` with `libcamera`.

`FramePacket` should contain:

- frame image;
- monotonic timestamp;
- wall-clock timestamp;
- frame index;
- optional encoded packet reference.

### 3.2 Frame Broker

Responsibilities:

- decouple capture from analysis;
- resize/copy frames for low-resolution inference;
- maintain a small bounded queue;
- drop stale analysis frames if the detector falls behind.

This prevents camera capture from blocking on ML.

### 3.3 Motion Gate

Purpose:

- filter out most frames before running the detector.

Method:

- OpenCV `BackgroundSubtractorMOG2` or frame differencing;
- morphological cleanup;
- contour area filtering;
- debounce over several frames.

Output:

- `motion_present`;
- motion regions;
- motion score.

### 3.4 Object Detector

Purpose:

- identify `cat` and `person` candidates in motion frames.

Production shape:

- detector runs only when motion is present, or every Nth frame while an event is active;
- inference resolution should be lower than recording resolution.

Recommended first detector:

- lightweight YOLO nano/small variant exported to ONNX.

### 3.5 Target Tracker

Purpose:

- assign stable IDs to cat/person detections across frames;
- reduce duplicate event starts.

Recommendation:

- MVP: simple centroid/IoU tracker implemented in-project;
- upgrade path: ByteTrack if occlusion handling becomes a real problem.

### 3.6 Motion-Within-Target Scorer

This is the rule that enforces your core requirement.

Triggering on object presence alone is incorrect. The system should record only when the target itself moves.

Per target track, compute motion from:

- bounding-box center displacement over time;
- change in box size;
- optional optical-flow or foreground-mask energy inside the box.

An event is eligible only if:

- class is `cat`, or class resolves to `baby`;
- target motion score exceeds threshold for a minimum confirmation window.

This rejects:

- moving curtains with a sleeping cat in frame;
- adult movement when baby mode is strict;
- general room motion with no target.

### 3.7 Baby Resolver

Because `baby` is not a reliable standard detector class, add a dedicated resolver:

- Input: tracked `person` detection plus ROI/context.
- Output: `adult`, `baby`, or `unknown`.

Resolver modes:

- `roi_person_is_baby`
  - best for crib/nursery cameras;
  - low complexity, room-specific.
- `crop_classifier`
  - a small binary classifier on person crops;
  - needs curated data and validation.
- `disabled`
  - cat-only operation.

Recommendation:

- Start with `roi_person_is_baby` if the camera is room-specific.
- Promote to `crop_classifier` once you have sample footage.

### 3.8 Event State Machine

States:

- `idle`
- `candidate`
- `recording`
- `cooldown`

Rules:

- `idle -> candidate` when target motion is first detected.
- `candidate -> recording` after temporal confirmation across several frames.
- `recording` continues while target motion persists.
- Merge events when gaps are shorter than `merge_gap_seconds`.
- `recording -> cooldown -> idle` after post-roll completes.

The event start time is the first confirmed target-motion timestamp, not the time the file begins to flush.

### 3.9 Recorder

Two-layer design:

- `PreEventBuffer`
  - always-on circular buffer containing the last 2-5 seconds.
- `ClipWriter`
  - writes the selected pre-roll plus active frames to final storage.

macOS MVP:

- keep a circular buffer of recent full-res frames or encoded packets;
- write clips with PyAV or FFmpeg once an event is confirmed.

Raspberry Pi optimized path:

- use `Picamera2` video recording with `CircularOutput` for H.264 pre-roll;
- run analysis on a low-resolution stream in parallel.

### 3.10 Storage Manager

Directory layout:

```text
records/
  YYYY/
    MM/
      DD/
        20260326T214455_cat.mp4
        20260326T214455_cat.json
```

Metadata JSON should include:

- event id;
- start/end timestamps;
- pre-roll seconds;
- detected labels;
- confidence summary;
- runtime profile;
- source camera;
- clip path.

## 4. Data Flow

1. Camera backend captures frames continuously.
2. Recorder keeps a circular pre-event buffer.
3. Analysis pipeline receives resized frames.
4. Motion gate marks candidate frames.
5. Detector runs on candidates.
6. Tracker links detections across frames.
7. Motion scorer confirms that a target object itself is moving.
8. Event state machine opens or extends a clip.
9. Recorder flushes 2 seconds of buffered video before the event and appends post-event footage.
10. Storage manager writes MP4 + JSON under `records/YYYY/MM/DD`.

## 5. Platform Migration Strategy

### Shared Code

- config loading;
- motion gate;
- detection and tracking;
- event rules;
- storage paths;
- metadata and logging;
- tests.

### macOS-Specific

- webcam capture via OpenCV AVFoundation;
- frame-based clip writing if hardware-friendly circular encoding is unavailable.

### Raspberry Pi-Specific

- `Picamera2` capture;
- H.264 encoder plus `CircularOutput`;
- `systemd` service;
- Raspberry Pi OS tuning.

### Migration Rule

The only code that should change during migration is:

- `camera_backend/*`
- `recorder_backend/*`
- deployment scripts and service files

Everything else should remain identical.

## 6. Suggested Project Layout

```text
src/catcam/
  app.py
  config.py
  models/
  camera/
    base.py
    mac_camera.py
    pi_camera.py
  pipeline/
    motion.py
    detector.py
    tracker.py
    baby_resolver.py
    event_engine.py
  recording/
    buffer.py
    writer.py
    mac_writer.py
    pi_writer.py
  storage/
    paths.py
    metadata.py
    retention.py
  service/
    health.py
tests/
configs/
models/
records/
```

## 7. Key Risks

### Risk 1: Baby detection quality

This is the highest-risk requirement.

Mitigation:

- begin with ROI-based baby semantics if the deployment scene allows it;
- collect local footage;
- train or fine-tune a lightweight baby/adult classifier;
- validate on your own camera angle before trusting it.

### Risk 2: Raspberry Pi 4 throughput

Mitigation:

- use motion-gated inference;
- keep analysis resolution low;
- prefer ONNX first for dev simplicity;
- add TFLite/INT8 or NCNN if needed.

### Risk 3: False positives from scene noise

Mitigation:

- combine motion gate with target classification and target-local motion scoring;
- require multi-frame confirmation;
- add configurable ROIs and ignore zones.

## 8. Recommended Implementation Order

1. Mac camera capture + circular buffer + raw clip writing.
2. Motion gate.
3. Cat detection only.
4. Track-based motion confirmation.
5. Event state machine + storage layout.
6. Baby MVP mode.
7. Pi camera backend.
8. Pi encoder optimization.
9. Baby classifier training and validation.

## 9. Reference Notes

The design aligns with current upstream docs showing:

- Raspberry Pi camera support is centered on `Picamera2` over `libcamera`.
- `Picamera2` supports `CircularOutput`, which directly fits the 2-second pre-event requirement.
- OpenCV exposes AVFoundation on macOS and provides standard video I/O and background subtraction primitives.
- Ultralytics supports export to ONNX, TFLite, and NCNN.
- ONNX Runtime provides a CPU Python package for Arm-based CPUs and macOS.
