"""Imaging helpers: colormaps, overlays, base64 encoding, spectrogram rendering."""
from __future__ import annotations

import base64
import io

import cv2
import numpy as np


def normalize01(arr: np.ndarray) -> np.ndarray:
    """Min-max normalise an array to [0, 1] (safe for constant arrays)."""
    arr = arr.astype(np.float32)
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if hi - lo < 1e-9:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def png_data_uri(bgr_or_gray: np.ndarray) -> str:
    """Encode an OpenCV image (BGR or single-channel) as a base64 PNG data URI."""
    ok, buf = cv2.imencode(".png", bgr_or_gray)
    if not ok:
        raise RuntimeError("Failed to PNG-encode image")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def heatmap_overlay(base_bgr: np.ndarray, intensity: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    """Overlay a [0,1] intensity map on a base image using the JET colormap."""
    h, w = base_bgr.shape[:2]
    inten = cv2.resize(intensity.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    inten = normalize01(inten)
    color = cv2.applyColorMap((inten * 255).astype(np.uint8), cv2.COLORMAP_JET)
    return cv2.addWeighted(color, alpha, base_bgr, 1 - alpha, 0)


def thumbnail_data_uri(bgr: np.ndarray, max_side: int = 160) -> str:
    """Create a small base64 thumbnail from a BGR frame."""
    h, w = bgr.shape[:2]
    scale = max_side / max(h, w)
    if scale < 1:
        bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return png_data_uri(bgr)


def spectrogram_data_uri(spec_db: np.ndarray) -> str:
    """Render a dB spectrogram (freq x time) to a colored base64 PNG, low→high = bottom→top."""
    img = normalize01(spec_db)
    img = (img * 255).astype(np.uint8)
    img = cv2.flip(img, 0)  # put low frequencies at the bottom
    color = cv2.applyColorMap(img, cv2.COLORMAP_MAGMA)
    # Upscale small spectrograms so they are legible in the UI/report.
    h, w = color.shape[:2]
    target_w = 640
    if w < target_w:
        color = cv2.resize(color, (target_w, max(160, int(h * target_w / max(w, 1)))),
                           interpolation=cv2.INTER_NEAREST)
    return png_data_uri(color)


def data_uri_to_png_bytes(data_uri: str) -> bytes:
    """Decode a base64 PNG data URI back to raw bytes (used by the PDF builder)."""
    _, b64 = data_uri.split(",", 1)
    return base64.b64decode(b64)
