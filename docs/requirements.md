# Requirements

## 1. Goal

Build an offline video event-capture system that:

- reads a live camera feed from a MacBook camera now;
- later runs on Raspberry Pi 4 with a Raspberry Pi camera;
- saves clips only when motion is caused by a cat or a baby;
- ignores all other motion and no-motion periods;
- includes video from 3 seconds before the event starts.

## 2. Functional Requirements

### 2.1 Camera Input

- The system must support a built-in MacBook camera for the initial development target.
- The system must support Raspberry Pi camera input for the migration target.
- Camera capture must be abstracted behind a backend interface so the detection pipeline does not depend on a specific device API.

### 2.2 Event Detection

- The system must continuously inspect the live stream for motion.
- The system must only trigger a recording when both of the following are true:
- motion is present;
- the moving object is classified as `cat` or `baby`.
- Motion caused by other classes, background changes, or camera noise must not create a saved clip.
- Presence without motion must not create a saved clip.
- An event start timestamp must be based on the first confirmed frame where target-class motion is detected.

### 2.3 Recording

- The system must keep a rolling pre-event buffer of at least 3 seconds.
- A saved clip must begin at least 3 seconds before the confirmed event start timestamp.
- A saved clip must continue until target motion ends plus a configurable post-roll.
- Multiple detections close in time should be merged into a single clip when the gap is below a configurable threshold.
- Output clips should default to MP4/H.264 for broad compatibility.

### 2.4 Storage

- Clips must be stored in a year/month/day directory structure.
- Example path: `records/2026/03/26/20260326T214455_cat.mp4`
- Filenames should include timestamp and event label.
- The system should also store event metadata in JSON alongside each clip.

### 2.5 Configuration

- Thresholds, model paths, clip lengths, frame rate, resolutions, and storage root must be configurable without code changes.
- The system should support separate profiles for `macos-dev` and `rpi4-prod`.
- Regions of interest must be configurable for rooms where only part of the frame matters.

### 2.6 Operations

- The system must run fully offline after installation.
- The system must restart cleanly after failure.
- The system should run headless.
- The system should emit structured logs for debugging.

## 3. Quality Requirements

### 3.1 Performance

- On macOS, the system should support a development mode at 10-15 FPS analysis resolution.
- On Raspberry Pi 4, the baseline target should be 5-10 FPS analysis resolution with motion-gated inference.
- CPU use should remain bounded by using a low-resolution analysis stream and running ML only when motion is likely.

### 3.2 Accuracy

- False positives from lighting changes, monitor flicker, and foliage should be reduced with motion filtering and temporal confirmation.
- Cat detection should rely on a standard object detector class.
- Baby detection is treated as a staged requirement because common general-purpose detector label sets usually include `person` but not `baby`.

### 3.3 Reliability

- A recording failure must not crash the capture loop.
- Corrupt or partial clips should be minimized with atomic file finalization.
- When disk space falls below a configured watermark, the system should log and optionally prune old clips by retention policy.

### 3.4 Portability

- Business logic must be shared between macOS and Raspberry Pi.
- Platform-specific code should be isolated to camera and encoder backends.
- The preferred Raspberry Pi target is 64-bit Raspberry Pi OS to simplify Python package availability.

## 4. Explicit Non-Goals For MVP

- Cloud upload.
- Real-time mobile notifications.
- Multi-camera support.
- Training a fully custom detector from day one.
- Perfect baby/adult discrimination without environment-specific data.

## 5. Acceptance Criteria For MVP

- From a MacBook camera, the system runs locally and writes clips only for target motion.
- Saved clips start at least 3 seconds before the first confirmed target-motion frame.
- Clips are written under `records/YYYY/MM/DD`.
- Cat events are detected with stable precision in the target room.
- Baby events work in one of these MVP modes:
- nursery-specific `person-in-ROI` mode with clear documented limits;
- or a custom baby classifier that passes local test footage.
- The codebase structure allows swapping the camera backend from macOS to Picamera2 without touching event logic.
