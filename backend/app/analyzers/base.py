"""Shared scoring primitives for the forensic analyzers.

Design philosophy
-----------------
Each analyzer measures a set of *real* forensic indicators (floats). Every indicator
is mapped to a bounded contribution in [0, 1] via a smooth, monotonic response curve
with a documented operating point. Contributions are combined with a logistic
("weighted evidence") aggregator into a modality score in [0, 1].

The scores are *interpretable manipulation-evidence indicators*, not the output of a
model trained on labelled deepfakes. This is deliberate and disclosed (responsible-AI
requirement N2/N3): we never claim proof, only evidence.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def ramp(value: float, low: float, high: float) -> float:
    """Linear ramp: 0 below `low`, 1 above `high`, linear in between.

    If low > high the ramp is inverted (1 below high, 0 above low).
    """
    if low == high:
        return 1.0 if value >= low else 0.0
    if low < high:
        return float(min(1.0, max(0.0, (value - low) / (high - low))))
    # inverted
    return float(min(1.0, max(0.0, (low - value) / (low - high))))


def band(value: float, center: float, tol: float) -> float:
    """1.0 when `value` is near `center`, decaying to 0 at distance `tol`."""
    if tol <= 0:
        return 1.0 if value == center else 0.0
    d = abs(value - center) / tol
    return float(max(0.0, 1.0 - d))


@dataclass
class EvidenceItem:
    name: str
    detail: str
    contribution: float  # [0, 1]
    weight: float = 1.0


@dataclass
class ScoreBuilder:
    """Accumulates weighted evidence and produces a logistic modality score."""

    items: list[EvidenceItem] = field(default_factory=list)
    features: dict[str, float] = field(default_factory=dict)

    def add(self, name: str, detail: str, contribution: float, weight: float = 1.0) -> None:
        contribution = float(min(1.0, max(0.0, contribution)))
        self.items.append(EvidenceItem(name, detail, contribution, weight))

    def feat(self, key: str, value: float) -> None:
        self.features[key] = float(value)

    def score(self, bias: float = -1.1, gain: float = 2.8, max_emphasis: float = 0.2) -> float:
        """Logistic aggregation of weighted evidence (noisy-OR flavoured).

        `bias` sets the prior (negative → "assume authentic until evidence");
        `gain` controls how sharply accumulated evidence raises the score.
        `max_emphasis` blends in the single strongest indicator, because in forensics
        one strong, well-localised artifact is itself informative — but it is kept small
        so a lone noisy feature cannot dominate.
        """
        if not self.items:
            return 0.0
        wsum = sum(i.weight for i in self.items) or 1.0
        mean_c = sum(i.weight * i.contribution for i in self.items) / wsum
        max_c = max(i.contribution for i in self.items)
        eff = (1.0 - max_emphasis) * mean_c + max_emphasis * max_c
        return float(sigmoid(bias + gain * (2.0 * eff - 1.0)))

    def top_evidence(self, k: int = 6) -> list[EvidenceItem]:
        return sorted(self.items, key=lambda i: i.contribution * i.weight, reverse=True)[:k]
