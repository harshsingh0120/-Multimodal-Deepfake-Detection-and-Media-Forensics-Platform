"""Media ingestion: type detection, frame sampling, and audio demux.

Audio (whether a standalone file or a video's audio track) is always routed through
the bundled ffmpeg into a mono WAV at a fixed sample rate, so every downstream
analyzer sees a uniform signal regardless of the input container/codec.
"""
from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import soundfile as sf

from ..config import get_settings


class MediaError(ValueError):
    """Raised when media cannot be read or is unsupported."""


@dataclass
class VideoFrames:
    frames: list[np.ndarray]           # BGR frames (downscaled)
    timestamps: list[float]            # seconds for each frame
    fps: float
    width: int
    height: int
    frame_count: int
    duration_sec: float


@dataclass
class AudioSignal:
    samples: np.ndarray                # mono float32 in [-1, 1]
    sr: int
    duration_sec: float
    source: str = "file"               # "file" or "video"


@dataclass
class IngestResult:
    media_type: str                    # image | video | audio
    image: Optional[np.ndarray] = None
    video: Optional[VideoFrames] = None
    audio: Optional[AudioSignal] = None
    has_audio: bool = False
    meta: dict = field(default_factory=dict)


def detect_media_type(path: Path) -> str:
    s = get_settings()
    ext = path.suffix.lower()
    if ext in s.ALLOWED_IMAGE_EXT:
        return "image"
    if ext in s.ALLOWED_VIDEO_EXT:
        return "video"
    if ext in s.ALLOWED_AUDIO_EXT:
        return "audio"
    raise MediaError(
        f"Unsupported file type '{ext}'. Allowed: images "
        f"{sorted(s.ALLOWED_IMAGE_EXT)}, video {sorted(s.ALLOWED_VIDEO_EXT)}, "
        f"audio {sorted(s.ALLOWED_AUDIO_EXT)}."
    )


def _downscale(frame: np.ndarray, max_side: int) -> np.ndarray:
    h, w = frame.shape[:2]
    scale = max_side / max(h, w)
    if scale < 1:
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return frame


def load_image(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)  # unicode-safe on Windows
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise MediaError("Could not decode image (corrupt or unsupported encoding).")
    return _downscale(img, get_settings().FRAME_MAX_SIDE)


def extract_frames(path: Path, max_frames: Optional[int] = None) -> VideoFrames:
    """Evenly sample up to `max_frames` frames from a video."""
    s = get_settings()
    max_frames = max_frames or s.VIDEO_MAX_FRAMES
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise MediaError("Could not open video (corrupt or unsupported codec).")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if fps <= 0:
        fps = 25.0  # fall back to a sane default when metadata is missing

    frames: list[np.ndarray] = []
    timestamps: list[float] = []

    if total and total > 0:
        idxs = np.linspace(0, max(total - 1, 0), num=min(max_frames, total), dtype=int)
        idx_set = sorted(set(int(i) for i in idxs))
        for i in idx_set:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            frames.append(_downscale(frame, s.FRAME_MAX_SIDE))
            timestamps.append(i / fps)
    else:
        # Unknown length: stream sequentially and keep an even subset.
        collected = []
        count = 0
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            collected.append((count, frame))
            count += 1
            if count > 5000:  # safety cap
                break
        total = count
        if collected:
            idxs = np.linspace(0, len(collected) - 1, num=min(max_frames, len(collected)), dtype=int)
            for i in sorted(set(int(x) for x in idxs)):
                fi, frame = collected[i]
                frames.append(_downscale(frame, s.FRAME_MAX_SIDE))
                timestamps.append(fi / fps)
    cap.release()

    if not frames:
        raise MediaError("No frames could be decoded from the video.")

    duration = (total / fps) if total else (timestamps[-1] if timestamps else 0.0)
    return VideoFrames(
        frames=frames, timestamps=timestamps, fps=float(fps),
        width=width or frames[0].shape[1], height=height or frames[0].shape[0],
        frame_count=total, duration_sec=float(duration),
    )


def _ffmpeg_extract_wav(src: Path, dst: Path, sr: int) -> bool:
    """Decode any container's audio track to mono WAV at `sr`. Returns success."""
    s = get_settings()
    cmd = [
        s.ffmpeg_exe(), "-y", "-i", str(src),
        "-vn", "-ac", "1", "-ar", str(sr), "-f", "wav", str(dst),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return proc.returncode == 0 and dst.exists() and dst.stat().st_size > 128


def load_audio(path: Path, source: str = "file") -> Optional[AudioSignal]:
    """Load audio from any file/video via ffmpeg → WAV. Returns None if no audio."""
    s = get_settings()
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        if not _ffmpeg_extract_wav(path, wav, s.AUDIO_SR):
            return None
        try:
            samples, sr = sf.read(str(wav), dtype="float32", always_2d=False)
        except Exception:
            return None
    if samples is None or len(samples) == 0:
        return None
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    samples = np.asarray(samples, dtype=np.float32)
    duration = len(samples) / float(sr)
    if duration < 0.05:  # effectively silent / empty track
        return None
    return AudioSignal(samples=samples, sr=int(sr), duration_sec=float(duration), source=source)


def ingest(path: Path) -> IngestResult:
    """Top-level ingestion dispatch based on detected media type."""
    media_type = detect_media_type(path)

    if media_type == "image":
        img = load_image(path)
        return IngestResult(
            media_type="image", image=img, has_audio=False,
            meta={"width": img.shape[1], "height": img.shape[0]},
        )

    if media_type == "video":
        vf = extract_frames(path)
        audio = load_audio(path, source="video")
        return IngestResult(
            media_type="video", video=vf, audio=audio, has_audio=audio is not None,
            meta={
                "width": vf.width, "height": vf.height, "fps": vf.fps,
                "duration_sec": vf.duration_sec, "has_audio": audio is not None,
                "sample_rate": audio.sr if audio else None,
            },
        )

    # audio
    audio = load_audio(path, source="file")
    if audio is None:
        raise MediaError("Audio file contained no decodable audio.")
    return IngestResult(
        media_type="audio", audio=audio, has_audio=True,
        meta={"duration_sec": audio.duration_sec, "sample_rate": audio.sr},
    )
