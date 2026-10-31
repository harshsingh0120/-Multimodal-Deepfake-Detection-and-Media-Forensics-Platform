"""Lightweight face detection shared across analyzers (OpenCV Haar cascade).

Haar is used because it ships with OpenCV (no model download, fully reproducible)
and is adequate for locating the dominant face region that the forensic checks and
lip-sync branch operate on. A stronger detector (RetinaFace/MediaPipe) can be
swapped in behind this same interface.
"""
from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np


@lru_cache(maxsize=1)
def _frontal_cascade() -> "cv2.CascadeClassifier":
    return cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def detect_faces(bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Return face boxes as (x, y, w, h), largest first."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    cascade = _frontal_cascade()
    if cascade.empty():
        return []
    faces = cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5,
                                     minSize=(40, 40))
    boxes = [tuple(int(v) for v in f) for f in faces]
    boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
    return boxes


def largest_face(bgr: np.ndarray) -> tuple[int, int, int, int] | None:
    boxes = detect_faces(bgr)
    return boxes[0] if boxes else None


def mouth_region(box: tuple[int, int, int, int], frame_shape: tuple[int, int]) -> tuple[int, int, int, int]:
    """Estimate the mouth sub-region (lower-middle third of the face box)."""
    x, y, w, h = box
    mx = x + int(0.20 * w)
    mw = int(0.60 * w)
    my = y + int(0.62 * h)
    mh = int(0.30 * h)
    H, W = frame_shape[:2]
    mx = max(0, min(mx, W - 1))
    my = max(0, min(my, H - 1))
    mw = max(1, min(mw, W - mx))
    mh = max(1, min(mh, H - my))
    return (mx, my, mw, mh)
