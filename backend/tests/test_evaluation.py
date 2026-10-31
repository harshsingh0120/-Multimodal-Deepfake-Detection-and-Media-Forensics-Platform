"""Evaluation metrics (AUC / EER / accuracy / ECE) sanity checks."""
import numpy as np

from evaluation.metrics import (equal_error_rate, expected_calibration_error,
                                summarize)


def test_perfect_separation():
    y = np.array([0, 0, 0, 1, 1, 1])
    s = np.array([0.1, 0.2, 0.15, 0.8, 0.9, 0.85])
    m = summarize(y, s)
    assert m.auc == 1.0
    assert m.eer == 0.0
    assert m.accuracy == 1.0


def test_random_scores_auc_near_half():
    rng = np.random.default_rng(0)
    y = np.array([0, 1] * 100)
    s = rng.random(200)
    m = summarize(y, s)
    assert 0.35 < m.auc < 0.65  # no signal → ~0.5


def test_eer_bounds():
    y = np.array([0, 0, 1, 1])
    s = np.array([0.2, 0.4, 0.6, 0.8])
    eer, thr = equal_error_rate(y, s)
    assert 0.0 <= eer <= 1.0
    assert 0.0 <= thr <= 1.0


def test_ece_is_zero_for_calibrated():
    # Scores exactly equal to empirical accuracy per group → ECE ≈ 0.
    y = np.array([0, 0, 1, 1])
    s = np.array([0.0, 0.0, 1.0, 1.0])
    assert expected_calibration_error(y, s, bins=5) < 1e-6
