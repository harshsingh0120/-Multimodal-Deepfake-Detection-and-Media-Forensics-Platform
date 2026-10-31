"""Audio branch: synthetic-speech discrimination, segments, spectrogram (F4, F9)."""
from app.utils.media import ingest
from app.analyzers.audio_analyzer import analyze_audio


def _analyze(path):
    ing = ingest(path)
    return analyze_audio(ing.audio.samples, ing.audio.sr)


def test_suspect_audio_scores_higher(samples):
    a = _analyze(samples["authentic_audio"])
    s = _analyze(samples["suspect_audio"])
    assert s.score > a.score + 0.2, (a.score, s.score)


def test_audio_features_present(samples):
    res = _analyze(samples["suspect_audio"])
    for key in ("rms_cv", "centroid_cv", "mfcc_dynamism", "rolloff_fraction",
                "noise_floor_db"):
        assert key in res.features
    assert res.envelope is not None and len(res.envelope) > 1


def test_spectrogram_and_segments(samples):
    res = _analyze(samples["suspect_audio"])
    assert res.heatmaps and res.heatmaps[0]["image"].startswith("data:image/png;base64,")
    # flagged_segments is a list of well-formed dicts (may be empty but typed)
    for seg in res.flagged_segments:
        assert seg["end_sec"] > seg["start_sec"]
        assert 0.0 <= seg["score"] <= 1.0
