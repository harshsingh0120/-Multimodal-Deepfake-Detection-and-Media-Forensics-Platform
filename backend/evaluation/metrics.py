"""Detection metrics: ROC-AUC, EER, best-threshold accuracy, Brier, ECE.

Scores are treated as P(manipulated) in [0, 1]; labels are 1 = fake/manipulated,
0 = authentic. All functions are pure and defensive against degenerate inputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

try:
    from sklearn.metrics import roc_auc_score, roc_curve
    _HAVE_SK = True
except Exception:  # pragma: no cover
    _HAVE_SK = False


@dataclass
class MetricSet:
    n: int
    n_pos: int
    n_neg: int
    auc: float | None
    eer: float | None
    eer_threshold: float | None
    best_threshold: float | None
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    brier: float | None
    ece: float | None
    extra: dict = field(default_factory=dict)


def _roc(y_true: np.ndarray, y_score: np.ndarray):
    if _HAVE_SK:
        fpr, tpr, thr = roc_curve(y_true, y_score)
        return fpr, tpr, thr
    # Minimal fallback ROC (ascending thresholds) if sklearn is unavailable.
    order = np.argsort(-y_score)
    ys = y_true[order]
    P = ys.sum()
    N = len(ys) - P
    tpr = np.cumsum(ys) / (P or 1)
    fpr = np.cumsum(1 - ys) / (N or 1)
    thr = y_score[order]
    return np.concatenate([[0], fpr]), np.concatenate([[0], tpr]), np.concatenate([[1], thr])


def equal_error_rate(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    """Return (EER, threshold) where false-accept rate == false-reject rate."""
    fpr, tpr, thr = _roc(y_true, y_score)
    fnr = 1.0 - tpr
    idx = int(np.nanargmin(np.abs(fnr - fpr)))
    eer = float((fpr[idx] + fnr[idx]) / 2.0)
    t = float(thr[idx]) if idx < len(thr) else 0.5
    return eer, t


def expected_calibration_error(y_true: np.ndarray, y_score: np.ndarray, bins: int = 10) -> float:
    """ECE: weighted gap between confidence and accuracy across probability bins."""
    y_true = np.asarray(y_true, dtype=float)
    y_score = np.clip(np.asarray(y_score, dtype=float), 0, 1)
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    n = len(y_score)
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (y_score >= lo) & (y_score < hi if i < bins - 1 else y_score <= hi)
        if not mask.any():
            continue
        conf = float(y_score[mask].mean())
        acc = float(y_true[mask].mean())
        ece += (mask.sum() / n) * abs(conf - acc)
    return float(ece)


def best_threshold_accuracy(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    """Threshold maximising accuracy; returns (threshold, accuracy)."""
    cands = np.unique(np.concatenate([y_score, [0.5]]))
    best_t, best_a = 0.5, 0.0
    for t in cands:
        pred = (y_score >= t).astype(int)
        a = float((pred == y_true).mean())
        if a > best_a:
            best_a, best_t = a, float(t)
    return best_t, best_a


def summarize(y_true, y_score, bins: int = 10) -> MetricSet:
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    n = len(y_true)
    n_pos, n_neg = int(y_true.sum()), int((1 - y_true).sum())

    auc = eer = eer_t = None
    if n_pos > 0 and n_neg > 0:
        try:
            auc = float(roc_auc_score(y_true, y_score)) if _HAVE_SK else None
        except Exception:
            auc = None
        eer, eer_t = equal_error_rate(y_true, y_score)

    best_t, acc = best_threshold_accuracy(y_true, y_score) if n else (0.5, None)
    pred = (y_score >= (best_t if best_t is not None else 0.5)).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision and recall and (precision + recall) else None)
    brier = float(np.mean((y_score - y_true) ** 2)) if n else None
    ece = expected_calibration_error(y_true, y_score, bins) if n_pos and n_neg else None

    return MetricSet(
        n=n, n_pos=n_pos, n_neg=n_neg, auc=auc, eer=eer, eer_threshold=eer_t,
        best_threshold=best_t, accuracy=acc, precision=precision, recall=recall,
        f1=f1, brier=brier, ece=ece,
    )
