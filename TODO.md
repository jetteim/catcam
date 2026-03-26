# TODO

## Phase 0: Decision Lock

- [x] Confirm Python as the implementation language.
- [x] Confirm Raspberry Pi OS 64-bit as the migration target.
- [ ] Decide the initial camera scene type:
- nursery/crib camera;
- general room camera.
- [ ] Decide whether MVP baby detection may use room-specific ROI rules.

## Phase 1: Repository Bootstrap

- [x] Initialize a git repository.
- [x] Create Python project skeleton under `src/catcam`.
- [x] Add `pyproject.toml`.
- [x] Add config files for `macos-dev` and `rpi4-prod`.
- [x] Add model and records directories.
- [x] Add basic CLI entrypoint.
- [x] Add logging.

## Phase 2: Camera + Recording Foundation

- [x] Implement `CameraBackend` interface.
- [x] Implement macOS camera backend with OpenCV.
- [x] Implement circular pre-event buffer.
- [x] Implement MP4 clip writer.
- [x] Implement storage path builder for `records/YYYY/MM/DD`.
- [x] Save metadata JSON next to clips.
- [x] Add a synthetic replay mode from video file for repeatable tests.

## Phase 3: Event Logic MVP

- [x] Implement motion gate with MOG2.
- [x] Add contour filtering and debounce.
- [x] Implement detector runtime wrapper.
- [ ] Export a lightweight detector to ONNX.
- [x] Implement cat/person label mapping.
- [ ] Implement simple IoU or centroid tracker.
- [ ] Implement per-track motion scoring.
- [x] Implement event state machine with pre-roll and post-roll.
- [ ] Verify that non-target motion does not save clips.

## Phase 4: Cat-Only Validation

- [ ] Collect short cat and non-cat sample videos.
- [ ] Build an offline evaluation set.
- [ ] Tune thresholds for target room lighting.
- [ ] Measure false positives and missed events.
- [ ] Lock cat-only acceptance thresholds.

## Phase 5: Baby Detection Strategy

- [ ] Implement `baby_resolver` abstraction.
- [ ] MVP option A: add ROI-based baby mode.
- [ ] MVP option B: add person-crop dataset tooling.
- [ ] Gather local baby/adult sample crops from representative footage.
- [ ] Train or fine-tune a lightweight baby-vs-adult classifier if ROI mode is not sufficient.
- [ ] Validate baby precision and recall on local footage.

## Phase 6: Raspberry Pi Migration

- [ ] Set up Raspberry Pi 4 with 64-bit Raspberry Pi OS.
- [ ] Attach and validate Raspberry Pi camera with `Picamera2`.
- [x] Implement Pi camera backend.
- [ ] Implement Pi recording backend with `CircularOutput`.
- [ ] Compare ONNX Runtime performance on Pi.
- [ ] If needed, benchmark TFLite/INT8 or NCNN export.
- [ ] Tune analysis resolution, FPS, and buffer sizes for Pi thermals and CPU.
- [ ] Add `systemd` service unit.

## Phase 7: Hardening

- [ ] Add disk retention policy.
- [ ] Add startup health checks and camera failure retries.
- [ ] Add structured logs.
- [ ] Add clip integrity checks.
- [ ] Add graceful shutdown handling.
- [ ] Add watchdog/restart policy.

## Phase 8: Test Coverage

- [x] Unit test storage path creation.
- [x] Unit test event merge and pre-roll rules.
- [ ] Unit test motion scorer.
- [x] Integration test replaying known video clips.
- [ ] Add golden tests for event timestamps.
- [ ] Add platform smoke tests for macOS and Pi.

## First Build Slice

- [ ] Implement macOS-only cat detection first.
- [ ] Verify 2-second pre-roll from webcam input.
- [ ] Save clips correctly under dated folders.
- [ ] Add replay-based tests.
- [ ] Only after that, add baby mode.
