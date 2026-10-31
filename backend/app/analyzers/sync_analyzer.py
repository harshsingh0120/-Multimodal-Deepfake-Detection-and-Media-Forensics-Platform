"""Lip-sync / cross-modal consistency branch (SyncNet-style, classical implementation).

Correlates a per-frame mouth-openness signal (from the video branch) with the audio
RMS envelope. Genuine talking-head footage shows a strong, positively-lagged
correlation between mouth motion and speech energy; a mismatch (low or implausible
correlation) is evidence that audio and video were not recorded together — a hallmark
of lip-synced deepfakes and dubbed/cloned-voice attacks.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .base import ScoreBuilder, ramp


@dataclass
class SyncAnalysis:
    available: bool
    score: float
    confidence: float
    summary: str
    evidence: list = field(default_factory=list)
    features: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def _zscore(x: np.ndarray) -> np.ndarray:
    sd = x.std()
    if sd < 1e-9:
        return np.zeros_like(x)
    return (x - x.mean()) / sd


def analyze_sync(mouth_series, mouth_times, env, env_times,
                 max_lag_sec: float = 0.3) -> SyncAnalysis:
    sb = ScoreBuilder()
    notes: list[str] = []

    if (mouth_series is None or mouth_times is None or env is None or env_times is None
            or len(mouth_series) < 4 or len(env) < 4):
        return SyncAnalysis(
            available=False, score=0.0, confidence=0.0,
            summary="Lip-sync not evaluated (requires a talking face and an audio track).",
            notes=["Lip-sync branch needs both a detectable face across frames and audio."],
        )

    mouth_series = np.asarray(mouth_series, dtype=np.float32)
    mouth_times = np.asarray(mouth_times, dtype=np.float32)
    env = np.asarray(env, dtype=np.float32)
    env_times = np.asarray(env_times, dtype=np.float32)

    # If the mouth barely moves, correlation is meaningless.
    if float(np.std(mouth_series)) < 1e-4:
        return SyncAnalysis(
            available=False, score=0.0, confidence=0.0,
            summary="Lip-sync not evaluated (insufficient mouth movement detected).",
            notes=["Mouth region showed almost no movement; speaker may be silent/occluded."],
        )

    # Common uniform grid over the overlapping time span.
    t0 = max(mouth_times.min(), env_times.min())
    t1 = min(mouth_times.max(), env_times.max())
    if t1 - t0 < 0.4:
        return SyncAnalysis(
            available=False, score=0.0, confidence=0.0,
            summary="Lip-sync not evaluated (audio/video overlap too short).",
            notes=["Overlapping audio/video span was too short for a reliable correlation."],
        )

    fs = 50.0  # Hz resampling grid
    grid = np.arange(t0, t1, 1.0 / fs)
    m = np.interp(grid, mouth_times, mouth_series)
    a = np.interp(grid, env_times, env)
    m = _zscore(m)
    a = _zscore(a)

    # Cross-correlation over a bounded lag window.
    max_lag = int(max_lag_sec * fs)
    best_corr = -1.0
    best_lag = 0
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            c = np.corrcoef(m[:lag], a[-lag:])[0, 1] if len(m[:lag]) > 3 else 0.0
        elif lag > 0:
            c = np.corrcoef(m[lag:], a[:-lag])[0, 1] if len(m[lag:]) > 3 else 0.0
        else:
            c = np.corrcoef(m, a)[0, 1]
        if np.isnan(c):
            c = 0.0
        if c > best_corr:
            best_corr = c
            best_lag = lag

    zero_lag_corr = float(np.corrcoef(m, a)[0, 1]) if not np.isnan(np.corrcoef(m, a)[0, 1]) else 0.0
    best_lag_sec = best_lag / fs

    sb.feat("lipsync_best_correlation", best_corr)
    sb.feat("lipsync_zero_lag_correlation", zero_lag_corr)
    sb.feat("lipsync_best_lag_sec", best_lag_sec)
    sb.feat("lipsync_overlap_sec", float(t1 - t0))

    # Low correlation → audio and lips disagree → manipulation evidence.
    sb.add("Lip-audio correlation",
           f"Best mouth/audio correlation = {best_corr:.2f} at lag {best_lag_sec:+.02f}s. "
           f"Low correlation means lip motion does not match the speech envelope.",
           ramp(best_corr, 0.45, 0.05), weight=1.6)
    # Implausible lag (lips leading audio a lot, or large offset) is also suspicious.
    sb.add("Audio-visual offset plausibility",
           f"Best alignment lag = {best_lag_sec:+.02f}s. Large offsets suggest dubbing or "
           f"re-timed audio.",
           ramp(abs(best_lag_sec), 0.12, 0.28), weight=0.7)

    # A direct cross-modal mismatch is strong evidence, so the sync branch uses a lower
    # prior (higher bias) than the subtle single-modality statistical cues.
    score = sb.score(bias=-0.2, gain=3.2)
    overlap = float(t1 - t0)
    confidence = float(min(0.9, 0.25 + 0.4 * ramp(overlap, 0.5, 4.0)
                           + 0.25 * ramp(float(np.std(mouth_series)), 1e-3, 5.0)))

    if best_corr < 0.35:
        summary = "Lip-sync check: weak correlation between lip motion and speech (possible mismatch)."
    else:
        summary = "Lip-sync check: lip motion is broadly consistent with the speech envelope."

    return SyncAnalysis(
        available=True, score=score, confidence=confidence, summary=summary,
        evidence=sb.top_evidence(4), features=sb.features, notes=notes,
    )
