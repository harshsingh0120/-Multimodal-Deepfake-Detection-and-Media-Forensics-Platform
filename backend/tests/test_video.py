"""Video branch: temporal features and frame flagging (F2, F5, F9)."""
from app.utils.media import extract_frames
from app.analyzers.video_analyzer import analyze_video


def test_video_temporal_features(samples):
    vf = extract_frames(samples["sample_video"])
    assert len(vf.frames) >= 3
    res = analyze_video(vf)
    for key in ("mean_frame_score", "frame_score_std", "face_jitter",
                "flow_irregularity", "frames_analyzed"):
        assert key in res.features
    assert 0.0 <= res.score <= 1.0


def test_flagged_frames_structure(samples):
    vf = extract_frames(samples["sample_video"])
    res = analyze_video(vf)
    for fr in res.flagged_frames:
        assert "timestamp_sec" in fr and "thumbnail" in fr
        assert fr["thumbnail"].startswith("data:image/png;base64,")
        assert 0.0 <= fr["score"] <= 1.0
