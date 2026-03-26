from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
import importlib
from pathlib import Path
import shutil
import subprocess

from catcam.config import AppConfig
from catcam.recording.base import RecorderBackend
from catcam.storage.metadata import write_event_metadata
from catcam.storage.paths import build_clip_paths, ensure_day_directory
from catcam.types import Detection, EventDecision, EventRecord, FramePacket


@dataclass
class NativeRecordingSession:
    event_id: str
    label: str
    start_time: datetime
    clip_path: Path
    metadata_path: Path
    temp_path: Path
    labels: Counter[str] = field(default_factory=Counter)
    confidences: dict[str, float] = field(default_factory=dict)
    last_written_time: datetime | None = None


class PiNativeRecorder(RecorderBackend):
    def __init__(self, config: AppConfig, camera_backend) -> None:
        self.config = config
        self.camera_backend = camera_backend
        self.native_camera = None
        self._session: NativeRecordingSession | None = None
        self._encoder = None
        self._buffer_output = None
        self._file_output_factory = None
        self._encoder_started = False

    @property
    def active(self) -> bool:
        return self._session is not None

    def open(self) -> None:
        if self._encoder_started:
            return
        native_camera = self.camera_backend.native_camera()
        if native_camera is None:
            raise RuntimeError("Pi native recorder requires an active Picamera2 camera")
        self.native_camera = native_camera

        encoders_module = importlib.import_module("picamera2.encoders")
        outputs_module = importlib.import_module("picamera2.outputs")
        h264_encoder_cls = getattr(encoders_module, "H264Encoder")
        circular_output_cls = getattr(outputs_module, "CircularOutput", None)
        if circular_output_cls is None:
            raise RuntimeError("Picamera2 CircularOutput is required for Pi native recording")
        self._file_output_factory = getattr(outputs_module, "FileOutput", None)

        self._encoder = h264_encoder_cls()
        self._buffer_output = circular_output_cls(
            buffersize=max(1, round(self.config.recording.pre_event_seconds * self.config.camera.fps)),
            outputtofile=False,
        )
        if hasattr(self._encoder, "output"):
            self._encoder.output = self._buffer_output
            self._start_encoder(self._encoder)
        else:
            self._start_encoder(self._encoder, self._buffer_output)
        self._encoder_started = True

    def start(self, decision: EventDecision, pre_event_frames: list[FramePacket]):
        if self._session is not None:
            return self._session
        if decision.event_id is None or decision.label is None or decision.event_start is None:
            raise ValueError("event decision is missing required start fields")
        if not self._encoder_started:
            self.open()

        clip_path, metadata_path = build_clip_paths(
            root=self.config.recording.root,
            timestamp=decision.event_start,
            label=decision.label,
            event_id=decision.event_id,
            container=self.config.recording.container,
        )
        ensure_day_directory(self.config.recording.root, decision.event_start)
        temp_path = clip_path.with_suffix(".h264.part")
        if temp_path.exists():
            temp_path.unlink()

        session = NativeRecordingSession(
            event_id=decision.event_id,
            label=decision.label,
            start_time=decision.event_start,
            clip_path=clip_path,
            metadata_path=metadata_path,
            temp_path=temp_path,
        )
        self._session = session
        self._open_output(temp_path)
        return session

    def write_frame(self, packet: FramePacket, detections: list[Detection] | None = None) -> None:
        session = self._require_session()
        session.last_written_time = packet.wall_time
        if detections:
            for detection in detections:
                session.labels.update([detection.label])
                previous = session.confidences.get(detection.label, 0.0)
                session.confidences[detection.label] = max(previous, detection.confidence)

    def finalize(self, decision: EventDecision) -> EventRecord:
        session = self._require_session()
        self._close_output()

        event_end = decision.event_end or session.last_written_time or session.start_time
        self._materialize_clip(session)
        record = EventRecord(
            event_id=session.event_id,
            label=session.label,
            start_time=session.start_time,
            end_time=event_end,
            pre_event_seconds=self.config.recording.pre_event_seconds,
            source_camera=self.config.camera.device,
            profile=self.config.profile,
            clip_path=session.clip_path,
            metadata_path=session.metadata_path,
            confidence_summary=session.confidences,
        )
        write_event_metadata(record)
        self._session = None
        return record

    def close(self) -> None:
        if self.active:
            self._close_output()
            self._session = None
        if self._encoder_started:
            self._stop_encoder()
            self._encoder_started = False
        self._buffer_output = None
        self._encoder = None

    def _materialize_clip(self, session: NativeRecordingSession) -> None:
        if self.config.recording.container == "h264":
            shutil.move(str(session.temp_path), str(session.clip_path))
            return

        if self.config.recording.container != "mp4":
            raise ValueError(f"Unsupported Pi recording container: {self.config.recording.container}")

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required to remux Pi H.264 output to MP4")

        command = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(self.config.camera.fps),
            "-i",
            str(session.temp_path),
            "-c",
            "copy",
            str(session.clip_path),
        ]
        subprocess.run(command, check=True)
        session.temp_path.unlink(missing_ok=True)

    def _open_output(self, temp_path: Path) -> None:
        output = self._require_buffer_output()
        if hasattr(output, "fileoutput") and hasattr(output, "start"):
            output.fileoutput = str(temp_path)
            output.start()
            return

        if hasattr(output, "open_output"):
            target = self._file_output_factory(str(temp_path)) if self._file_output_factory else str(temp_path)
            output.open_output(target)
            return

        raise RuntimeError("Unsupported CircularOutput API shape")

    def _close_output(self) -> None:
        output = self._require_buffer_output()
        if hasattr(output, "stop"):
            output.stop()
            return
        if hasattr(output, "close_output"):
            output.close_output()
            return
        raise RuntimeError("Unsupported CircularOutput API shape")

    def _start_encoder(self, *args) -> None:
        if hasattr(self.native_camera, "start_encoder"):
            try:
                self.native_camera.start_encoder(*args)
            except TypeError:
                self.native_camera.start_encoder(args[0], args[1])
            return
        if hasattr(self.native_camera, "start_recording") and len(args) >= 2:
            self.native_camera.start_recording(args[0], args[1])
            return
        raise RuntimeError("Native Pi camera does not expose a supported encoder start API")

    def _stop_encoder(self) -> None:
        if hasattr(self.native_camera, "stop_encoder"):
            self.native_camera.stop_encoder()
            return
        if hasattr(self.native_camera, "stop_recording"):
            self.native_camera.stop_recording()
            return
        raise RuntimeError("Native Pi camera does not expose a supported encoder stop API")

    def _require_buffer_output(self):
        if self._buffer_output is None:
            raise RuntimeError("Pi native recorder has not been opened")
        return self._buffer_output

    def _require_session(self) -> NativeRecordingSession:
        if self._session is None:
            raise RuntimeError("recording session is not active")
        return self._session
