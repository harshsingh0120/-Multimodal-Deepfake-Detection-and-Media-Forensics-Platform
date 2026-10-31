"""Lip-sync branch (F6, A3): correlated signals = consistent; uncorrelated = mismatch."""
import numpy as np

from app.analyzers.sync_analyzer import analyze_sync


def _series(n=120, dur=3.0, seed=0):
    t = np.linspace(0, dur, n)
    rng = np.random.default_rng(seed)
    env = np.abs(np.sin(2 * np.pi * 1.5 * t)) + 0.1 * rng.random(n)
    return t, env


def test_synced_is_consistent():
    t, env = _series(seed=1)
    mouth = env * 10 + 0.5  # mouth openness tracks audio energy
    res = analyze_sync(mouth, t, env, t)
    assert res.available
    assert res.features["lipsync_best_correlation"] > 0.6
    assert res.score < 0.5  # consistent → low manipulation evidence


def test_desynced_is_flagged():
    t, env = _series(seed=2)
    rng = np.random.default_rng(99)
    mouth = rng.random(len(t)) * 10  # mouth motion unrelated to audio
    res = analyze_sync(mouth, t, env, t)
    assert res.available
    assert res.features["lipsync_best_correlation"] < 0.5
    assert res.score > 0.45  # mismatch → elevated evidence


def test_unavailable_without_inputs():
    res = analyze_sync(None, None, None, None)
    assert not res.available and res.score == 0.0
