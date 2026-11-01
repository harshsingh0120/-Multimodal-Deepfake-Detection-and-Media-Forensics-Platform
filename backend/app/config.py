"""Central configuration, loaded from environment variables (.env supported).

All tunables live here so the analysis is reproducible and deployment-configurable.
Secrets must never be hard-coded — read them from the environment.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load a .env file from the backend root if present (no-op in production if absent).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_ROOT / ".env")


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    """Runtime settings. Instantiate once via `get_settings()`."""

    # --- Server ---
    APP_NAME: str = os.getenv("APP_NAME", "Multimodal Deepfake Forensics Platform")
    API_VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = _get_int("PORT", 8000)

    # CORS: comma-separated origins allowed to call the API.
    CORS_ORIGINS: list[str] = _get_list(
        "CORS_ORIGINS",
        ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    )

    # --- Upload limits / security ---
    MAX_UPLOAD_MB: int = _get_int("MAX_UPLOAD_MB", 100)

    ALLOWED_IMAGE_EXT: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    ALLOWED_VIDEO_EXT: set[str] = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    ALLOWED_AUDIO_EXT: set[str] = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}

    # Where generated reports/results are cached (transient).
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(_BACKEND_ROOT / "data")))
    # How long (seconds) a result is retained before it may be cleaned up.
    RESULT_TTL_SECONDS: int = _get_int("RESULT_TTL_SECONDS", 3600)

    # --- Analysis tunables ---
    # Max frames sampled from a video (keeps analysis responsive).
    VIDEO_MAX_FRAMES: int = _get_int("VIDEO_MAX_FRAMES", 24)
    # Frames are downscaled so the longest side is at most this many pixels.
    FRAME_MAX_SIDE: int = _get_int("FRAME_MAX_SIDE", 720)
    # Audio analysis sample rate.
    AUDIO_SR: int = _get_int("AUDIO_SR", 16000)
    # Audio segment length (seconds) used for per-segment flagging.
    AUDIO_SEGMENT_SEC: float = _get_float("AUDIO_SEGMENT_SEC", 1.0)

    # Fusion calibration temperature (>1 softens confidence; see analyzers/fusion.py).
    CALIBRATION_TEMPERATURE: float = _get_float("CALIBRATION_TEMPERATURE", 1.3)

    # --- Optional trained-model plugins (disabled unless provided) ---
    # Hugging Face image-classification model id (or local dir) for the image branch,
    # e.g. "dima806/deepfake_vs_real_image_detection". Requires torch + transformers.
    IMAGE_MODEL_ID: str = os.getenv("IMAGE_MODEL_ID", "")
    # Which output index is the "fake" class. -1 = auto-detect from id2label.
    # Some published checkpoints ship a REVERSED id2label (e.g. dima806 → set this to 0).
    IMAGE_MODEL_FAKE_INDEX: int = _get_int("IMAGE_MODEL_FAKE_INDEX", -1)
    # Paths to drop-in torch checkpoints; when unset the interpretable engine is used.
    IMAGE_MODEL_PATH: str = os.getenv("IMAGE_MODEL_PATH", "")
    AUDIO_MODEL_PATH: str = os.getenv("AUDIO_MODEL_PATH", "")
    SYNC_MODEL_PATH: str = os.getenv("SYNC_MODEL_PATH", "")

    def ffmpeg_exe(self) -> str:
        """Return a usable ffmpeg binary path (bundled via imageio-ffmpeg)."""
        env = os.getenv("FFMPEG_BINARY")
        if env and Path(env).exists():
            return env
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return settings
