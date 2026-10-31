"""Multimodal late fusion + confidence calibration.

Combines the available per-modality scores into a single manipulation-evidence score,
penalising cross-modal disagreement (e.g. a clean face but mismatched lip-sync), and
calibrates confidence with temperature scaling. Verdict wording is centralised here and
*always* framed as "evidence of potential manipulation" — never proof (safety req. N2).

An attention-fusion head can replace `fuse()` behind the same signature; late fusion is
the baseline, as the reference architecture specifies.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..config import get_settings
from .base import sigmoid

# Base modality weights (renormalised over whichever modalities are available).
BASE_WEIGHTS = {"image": 0.25, "video": 0.30, "audio": 0.25, "sync": 0.20}

# (lower_bound, label, template). Every template uses safe, non-definitive wording.
VERDICT_BANDS = [
    (0.00, "Low",
     "Low evidence of manipulation. The analysed signals are largely consistent with "
     "authentic media, but this is not a guarantee of authenticity."),
    (0.25, "Guarded",
     "Limited evidence of potential manipulation. Some indicators are present; treat with "
     "mild caution and corroborate with context."),
    (0.45, "Elevated",
     "Evidence of potential manipulation. Multiple indicators warrant careful review before "
     "trusting this media."),
    (0.65, "High",
     "Strong evidence of potential manipulation. Several forensic indicators align; the media "
     "should not be trusted without independent verification."),
    (0.82, "Very High",
     "Strong evidence of potential manipulation across modalities. Independent verification is "
     "strongly recommended."),
]

SAFETY_NOTICE = (
    "This platform reports *evidence of potential manipulation*, never definitive proof. "
    "Results are probabilistic forensic indicators intended to assist human review, not to "
    "serve as sole or conclusive authentication."
)


@dataclass
class Modality:
    name: str
    available: bool
    score: float
    confidence: float


def _logit(p: float) -> float:
    p = min(1 - 1e-6, max(1e-6, p))
    return math.log(p / (1 - p))


def verdict_for(score: float) -> tuple[str, str]:
    label, text = VERDICT_BANDS[0][1], VERDICT_BANDS[0][2]
    for lb, lab, txt in VERDICT_BANDS:
        if score >= lb:
            label, text = lab, txt
    return label, text


def fuse(modalities: list[Modality]) -> dict:
    s = get_settings()
    available = [m for m in modalities if m.available]
    if not available:
        label, text = verdict_for(0.0)
        return {
            "overall_score": 0.0, "calibrated_confidence": 0.0,
            "verdict_band": label, "verdict_text": text,
            "weights": {}, "cross_modal_consistency": None,
            "rationale": ["No modality could be analysed."],
        }

    # Renormalise weights over available modalities, scaled by each one's confidence.
    raw = {m.name: BASE_WEIGHTS.get(m.name, 0.2) * (0.5 + 0.5 * m.confidence) for m in available}
    wsum = sum(raw.values()) or 1.0
    weights = {k: v / wsum for k, v in raw.items()}

    fused = sum(weights[m.name] * m.score for m in available)

    # Cross-modal disagreement (std of scores). High disagreement both lowers confidence
    # and slightly raises the score, because an inconsistent story is itself suspicious.
    scores = [m.score for m in available]
    mean_s = sum(scores) / len(scores)
    disagreement = (sum((x - mean_s) ** 2 for x in scores) / len(scores)) ** 0.5
    consistency = max(0.0, 1.0 - 2.0 * disagreement)

    if len(available) > 1:
        fused = min(1.0, fused + 0.10 * disagreement)

    # Temperature scaling (calibration): T>1 softens over-confident logits toward 0.5.
    T = max(0.5, s.CALIBRATION_TEMPERATURE)
    calibrated_score = sigmoid(_logit(fused) / T)

    # Confidence: mean modality confidence, boosted by coverage, cut by disagreement.
    mean_conf = sum(m.confidence for m in available) / len(available)
    coverage = len(available) / 4.0
    calibrated_confidence = max(0.05, min(0.95,
        0.5 * mean_conf + 0.3 * coverage + 0.2 * consistency))

    label, text = verdict_for(calibrated_score)

    rationale = [
        f"Fused {len(available)} modality score(s): "
        + ", ".join(f"{m.name}={m.score:.2f}" for m in available) + ".",
        f"Late-fusion weights: " + ", ".join(f"{k}={v:.2f}" for k, v in weights.items()) + ".",
        f"Cross-modal consistency = {consistency:.2f} "
        f"({'agreement' if consistency > 0.6 else 'some disagreement'}).",
        f"Temperature-scaled (T={T:.2f}) fused score = {calibrated_score:.2f}.",
    ]

    return {
        "overall_score": round(float(calibrated_score), 4),
        "calibrated_confidence": round(float(calibrated_confidence), 4),
        "verdict_band": label,
        "verdict_text": text,
        "weights": {k: round(v, 3) for k, v in weights.items()},
        "cross_modal_consistency": round(float(consistency), 3),
        "rationale": rationale,
    }
