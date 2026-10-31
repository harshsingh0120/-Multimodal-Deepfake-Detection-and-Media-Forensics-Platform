"""Video forensic analyzer.

Runs the image analyzer on sampled frames, then adds a *temporal* branch:

  * Per-frame score variance — authentic footage is temporally stable; deepfakes flicker
    as the generator re-synthesises each frame.
  * Face-box jitter — unstable face localisation across frames.
  * Optical-flow irregularity — abrupt, inconsistent motion energy between frames.

Emits a video score, flags the most suspicious frames (timestamp + thumbnail), and
exposes the per-frame mouth-openness series used by the lip-sync branch.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from ..utils.imaging import thumbnail_data_uri
from ..utils.media import VideoFrames
from .base import ScoreBuilder, ramp
from .faces import largest_face, mouth_region
from .image_analyzer import analyze_image_bgr


@dataclass
class VideoAnalysis:
    score: float
    confidence: float
    summary: str
    evidence: list = field(default_factory=list)
    features: dict = field(default_factory=dict)
    heatmaps: list = field(default_factory=list)
    flagged_frames: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    # for lip-sync branch:
    mouth_series: np.ndarray | None = None
    mouth_times: np.ndarray | None = None


def analyze_video(vf: VideoFrames) -> VideoAnalysis:
    sb = ScoreBuilder()
    notes: list[str] = []
    frames = vf.frames
    times = vf.timestamps

    per_frame_scores: list[float] = []
    face_centers: list[tuple[float, float] | None] = []
    mouth_vals: list[float] = []
    mouth_times: list[float] = []
    frame_face_boxes: list[tuple | None] = []
    best_image_analysis = None
    best_idx = 0

    for i, frame in enumerate(frames):
        face = largest_face(frame)
        frame_face_boxes.append(face)
        ia = analyze_image_bgr(frame, make_heatmaps=False, faces=[face] if face else [])
        per_frame_scores.append(ia.score)
        if best_image_analysis is None or ia.score > best_image_analysis.score:
            best_image_analysis = ia
            best_idx = i

        if face:
            x, y, w, h = face
            face_centers.append((x + w / 2.0, y + h / 2.0))
            mx, my, mw, mh = mouth_region(face, frame.shape)
            mouth = cv2.cvtColor(frame[my:my + mh, mx:mx + mw], cv2.COLOR_BGR2GRAY)
            # vertical gradient energy ≈ how "open" / active the mouth is
            gy = cv2.Sobel(mouth, cv2.CV_32F, 0, 1, ksize=3)
            mouth_vals.append(float(np.mean(np.abs(gy))))
            mouth_times.append(times[i])
        else:
            face_centers.append(None)

    scores = np.array(per_frame_scores, dtype=np.float32)
    mean_frame_score = float(scores.mean())
    frame_score_std = float(scores.std())

    # --- temporal: face-box jitter ---
    jitter = _face_jitter(face_centers, frames[0].shape)
    # --- temporal: optical-flow irregularity ---
    flow_irreg = _flow_irregularity(frames)

    sb.feat("frames_analyzed", float(len(frames)))
    sb.feat("mean_frame_score", mean_frame_score)
    sb.feat("frame_score_std", frame_score_std)
    sb.feat("face_jitter", jitter)
    sb.feat("flow_irregularity", flow_irreg)
    sb.feat("faces_present_fraction",
            float(np.mean([1.0 if b else 0.0 for b in frame_face_boxes])) if frame_face_boxes else 0.0)

    # Per-frame visual evidence (average of the visual branch across frames)
    sb.add("Per-frame visual artifacts",
           f"Mean per-frame image-forensics score = {mean_frame_score:.2f} across "
           f"{len(frames)} sampled frames.",
           mean_frame_score, weight=1.3)
    sb.add("Temporal flicker",
           f"Std-dev of per-frame scores = {frame_score_std:.2f}. High frame-to-frame "
           f"variation indicates generator flicker.",
           ramp(frame_score_std, 0.10, 0.30), weight=1.1)
    sb.add("Face-box jitter",
           f"Normalised face-center jitter = {jitter:.3f}. Unstable face tracking is a "
           f"synthesis cue.",
           ramp(jitter, 0.02, 0.12), weight=0.8)
    sb.add("Optical-flow irregularity",
           f"Flow irregularity = {flow_irreg:.2f}. Inconsistent inter-frame motion can "
           f"indicate frame-wise manipulation.",
           ramp(flow_irreg, 0.4, 1.4), weight=0.8)

    score = sb.score()

    confidence = float(min(0.95, 0.4 + 0.3 * ramp(len(frames), 4, 16)
                           + 0.2 * (1.0 if any(frame_face_boxes) else 0.0)))

    if not any(frame_face_boxes):
        notes.append("No face detected in any sampled frame — facial/temporal face checks "
                     "are limited; global per-frame forensics still applied.")

    # --- flagged frames: highest-scoring / most-deviating frames ---
    flagged = _flag_frames(frames, times, scores)

    # heatmap from the single most suspicious frame
    heatmaps = []
    if best_image_analysis is not None:
        full = analyze_image_bgr(frames[best_idx], make_heatmaps=True,
                                 faces=[frame_face_boxes[best_idx]] if frame_face_boxes[best_idx] else [])
        for hm in full.heatmaps:
            hm = dict(hm)
            hm["title"] = f"{hm['title']} (frame @ {times[best_idx]:.2f}s)"
            heatmaps.append(hm)

    summary = _summarize(score, any(frame_face_boxes))
    return VideoAnalysis(
        score=score, confidence=confidence, summary=summary,
        evidence=sb.top_evidence(6), features=sb.features, heatmaps=heatmaps,
        flagged_frames=flagged, notes=notes,
        mouth_series=np.array(mouth_vals) if mouth_vals else None,
        mouth_times=np.array(mouth_times) if mouth_times else None,
    )


def _face_jitter(centers: list, frame_shape) -> float:
    pts = [c for c in centers if c is not None]
    if len(pts) < 3:
        return 0.0
    arr = np.array(pts, dtype=np.float32)
    diffs = np.linalg.norm(np.diff(arr, axis=0), axis=1)
    diag = float(np.hypot(frame_shape[0], frame_shape[1]))
    return float(np.std(diffs) / (diag + 1e-9))


def _flow_irregularity(frames: list[np.ndarray]) -> float:
    if len(frames) < 3:
        return 0.0
    mags = []
    prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    for f in frames[1:]:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        if g.shape != prev.shape:
            g = cv2.resize(g, (prev.shape[1], prev.shape[0]))
        flow = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 2, 15, 3, 5, 1.1, 0)
        mags.append(float(np.mean(np.linalg.norm(flow, axis=2))))
        prev = g
    mags = np.array(mags)
    if mags.mean() < 1e-6:
        return 0.0
    # coefficient of variation of inter-frame motion energy
    return float(mags.std() / (mags.mean() + 1e-9))


def _flag_frames(frames, times, scores) -> list[dict]:
    if len(scores) == 0:
        return []
    thr = max(0.5, float(np.percentile(scores, 80)))
    order = np.argsort(scores)[::-1]
    flagged = []
    for i in order:
        if scores[i] >= thr and scores[i] >= 0.45:
            flagged.append({
                "index": int(i),
                "timestamp_sec": round(float(times[i]), 2),
                "score": round(float(scores[i]), 3),
                "reason": "Elevated per-frame visual-manipulation indicators.",
                "thumbnail": thumbnail_data_uri(frames[i]),
            })
        if len(flagged) >= 6:
            break
    return flagged


def _summarize(score: float, has_face: bool) -> str:
    face_txt = "faces were tracked" if has_face else "no faces were tracked"
    if score < 0.33:
        lvl = "few temporal/visual manipulation indicators"
    elif score < 0.6:
        lvl = "some temporal/visual indicators"
    else:
        lvl = "multiple temporal/visual manipulation indicators"
    return f"Video analysis found {lvl} ({face_txt})."
