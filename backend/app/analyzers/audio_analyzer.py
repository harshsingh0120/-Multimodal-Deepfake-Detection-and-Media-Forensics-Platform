"""Audio forensic analyzer — synthetic speech / voice-manipulation indicators.

Generator-agnostic cues that distinguish natural speech from TTS / voice-conversion /
vocoder output:

  * Prosodic micro-variation — natural speech has rich, irregular variation in energy
    and brightness; synthetic speech is frequently flatter/over-smoothed.
  * MFCC temporal variance — vocoded speech tends to have lower cepstral variability.
  * Spectral flatness — vocoder "buzz" raises flatness in voiced regions.
  * Band-limiting / spectral cliff — many synthesis pipelines band-limit or resample,
    leaving an abrupt high-frequency cut-off.
  * Noise-floor cleanliness — synthetic audio often has an unnaturally silent floor.

Produces an audio score in [0, 1], a log-mel spectrogram heatmap, and per-segment
flags (time ranges that look most synthetic).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import librosa
import numpy as np

from ..config import get_settings
from ..utils.imaging import spectrogram_data_uri
from .base import ScoreBuilder, ramp


@dataclass
class AudioAnalysis:
    score: float
    confidence: float
    summary: str
    evidence: list = field(default_factory=list)
    features: dict = field(default_factory=dict)
    heatmaps: list = field(default_factory=list)
    flagged_segments: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    envelope: np.ndarray | None = None       # RMS envelope (for lip-sync)
    envelope_times: np.ndarray | None = None


def _safe_cv(x: np.ndarray) -> float:
    m = float(np.mean(x))
    return float(np.std(x) / (abs(m) + 1e-9))


def analyze_audio(samples: np.ndarray, sr: int) -> AudioAnalysis:
    s = get_settings()
    sb = ScoreBuilder()
    notes: list[str] = []
    n_fft = 1024
    hop = 256

    # Guard very short clips.
    duration = len(samples) / sr
    if duration < 0.3:
        notes.append("Audio is very short (<0.3s); audio indicators are low-confidence.")

    S = np.abs(librosa.stft(samples, n_fft=n_fft, hop_length=hop)) ** 2
    mel = librosa.feature.melspectrogram(S=S, sr=sr, n_mels=64)
    mel_db = librosa.power_to_db(mel + 1e-10, ref=np.max)

    rms = librosa.feature.rms(S=np.sqrt(S), frame_length=n_fft, hop_length=hop)[0]
    centroid = librosa.feature.spectral_centroid(S=np.sqrt(S), sr=sr, hop_length=hop)[0]
    flatness = librosa.feature.spectral_flatness(S=np.sqrt(S), hop_length=hop)[0]
    rolloff = librosa.feature.spectral_rolloff(S=np.sqrt(S), sr=sr, roll_percent=0.98,
                                               hop_length=hop)[0]
    mfcc = librosa.feature.mfcc(S=librosa.power_to_db(mel + 1e-10), n_mfcc=20)

    times = librosa.frames_to_time(np.arange(rms.shape[0]), sr=sr, hop_length=hop)

    # --- scalar features ---
    rms_cv = _safe_cv(rms)                                  # energy dynamic range
    centroid_cv = _safe_cv(centroid)                        # brightness variation
    flatness_voiced = float(np.mean(flatness[rms > np.percentile(rms, 60)])) if rms.size else float(np.mean(flatness))
    # Cepstral *dynamism*: mean per-frame change of MFCCs, normalised by their spread.
    # Scale-robust (unlike raw variance): natural speech moves the cepstrum more than
    # over-smoothed synthetic speech.
    if mfcc.shape[1] > 2:
        dmfcc = np.abs(np.diff(mfcc[1:], axis=1))
        mfcc_dyn = float(np.mean(dmfcc) / (np.mean(np.abs(mfcc[1:])) + 1e-9))
    else:
        mfcc_dyn = 0.0
    highband_ratio = float(mel[int(0.78 * mel.shape[0]):].sum() / (mel.sum() + 1e-9))
    nyq = sr / 2.0
    rolloff_frac = float(np.median(rolloff) / nyq)          # 1.0 = full band, low = band-limited
    # noise floor: energy of the quietest 15% of frames, in dB
    quiet = np.percentile(rms, 15)
    noise_floor_db = float(20 * np.log10(quiet + 1e-9))

    for k, v in dict(
        rms_cv=rms_cv, centroid_cv=centroid_cv, flatness_voiced=flatness_voiced,
        mfcc_dynamism=mfcc_dyn, highband_ratio=highband_ratio,
        rolloff_fraction=rolloff_frac, noise_floor_db=noise_floor_db,
        duration_sec=duration,
    ).items():
        sb.feat(k, v)

    # --- evidence ---
    sb.add("Energy micro-variation",
           f"Energy coefficient-of-variation = {rms_cv:.2f}. Natural speech varies more; "
           f"low values suggest flat, synthetic prosody.",
           ramp(rms_cv, 1.1, 0.35), weight=1.1)
    sb.add("Brightness variation",
           f"Spectral-centroid CV = {centroid_cv:.2f}. Over-smooth brightness is a TTS cue.",
           ramp(centroid_cv, 0.55, 0.12), weight=1.0)
    sb.add("Cepstral dynamism (MFCC)",
           f"MFCC dynamism = {mfcc_dyn:.3f}. Vocoded/over-smoothed speech changes its "
           f"cepstrum less between frames.",
           ramp(mfcc_dyn, 0.22, 0.08), weight=1.1)
    sb.add("Spectral flatness (voiced)",
           f"Voiced-frame flatness = {flatness_voiced:.3f}. Elevated flatness indicates "
           f"vocoder noise/buzz.",
           ramp(flatness_voiced, 0.08, 0.30), weight=0.9)
    sb.add("Band-limiting / spectral cliff",
           f"Roll-off fraction = {rolloff_frac:.2f} of Nyquist. Sharp band-limiting is "
           f"common in synthesized/resampled audio.",
           ramp(rolloff_frac, 0.75, 0.45), weight=0.9)
    sb.add("Noise-floor cleanliness",
           f"Noise floor = {noise_floor_db:.0f} dB. An unnaturally clean floor can indicate "
           f"fully synthetic audio.",
           ramp(-noise_floor_db, 55.0, 85.0), weight=0.7)

    score = sb.score()

    # confidence grows with duration and amount of voiced content
    voiced_frac = float(np.mean(rms > np.percentile(rms, 60))) if rms.size else 0.0
    confidence = float(min(0.95, 0.3 + 0.4 * ramp(duration, 0.5, 5.0) + 0.25 * voiced_frac))

    # --- per-segment flagging ---
    flagged = _flag_segments(samples, sr, s.AUDIO_SEGMENT_SEC)

    heatmaps = [{
        "title": "Log-mel spectrogram",
        "description": "Time (x) vs. frequency (y). Horizontal banding, abrupt high-frequency "
                       "cut-offs, or overly uniform texture can indicate synthetic speech.",
        "image": spectrogram_data_uri(mel_db),
    }]

    summary = _summarize(score)
    return AudioAnalysis(
        score=score, confidence=confidence, summary=summary,
        evidence=sb.top_evidence(6), features=sb.features, heatmaps=heatmaps,
        flagged_segments=flagged, notes=notes,
        envelope=rms, envelope_times=times,
    )


def _flag_segments(samples: np.ndarray, sr: int, seg_sec: float) -> list[dict]:
    """Score each fixed window for synthetic-likelihood and flag the suspicious ones."""
    seg_len = max(1, int(seg_sec * sr))
    n = len(samples)
    seg_scores = []
    for start in range(0, n, seg_len):
        chunk = samples[start:start + seg_len]
        if len(chunk) < sr * 0.2:
            continue
        hop = 256
        try:
            Sc = np.abs(librosa.stft(chunk, n_fft=512, hop_length=hop)) ** 2
            rms = librosa.feature.rms(S=np.sqrt(Sc), frame_length=512, hop_length=hop)[0]
            flat = librosa.feature.spectral_flatness(S=np.sqrt(Sc), hop_length=hop)[0]
        except Exception:
            continue
        if rms.size == 0:
            continue
        cv = float(np.std(rms) / (np.mean(rms) + 1e-9))
        fl = float(np.mean(flat))
        seg_score = 0.6 * ramp(cv, 1.0, 0.3) + 0.4 * ramp(fl, 0.08, 0.3)
        seg_scores.append((start / sr, (start + len(chunk)) / sr, seg_score))

    if not seg_scores:
        return []
    vals = np.array([s[2] for s in seg_scores])
    thr = max(0.55, float(np.percentile(vals, 75)))
    flagged = []
    for (st, en, sc) in seg_scores:
        if sc >= thr and sc >= 0.5:
            flagged.append({
                "start_sec": round(st, 2), "end_sec": round(en, 2),
                "score": round(float(sc), 3),
                "reason": "Low prosodic variation / elevated spectral flatness in this window.",
            })
    return flagged[:20]


def _summarize(score: float) -> str:
    if score < 0.33:
        lvl = "few synthetic-speech indicators"
    elif score < 0.6:
        lvl = "some synthetic-speech indicators"
    else:
        lvl = "multiple synthetic-speech indicators"
    return f"Audio analysis found {lvl}."
