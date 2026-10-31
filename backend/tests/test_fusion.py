"""Fusion & calibration (F7, F8, A3, A4, N2)."""
from app.analyzers.fusion import (SAFETY_NOTICE, VERDICT_BANDS, Modality, fuse,
                                   verdict_for)


def test_safety_wording_never_definitive():
    """No verdict text may claim proof/definitive/fake; must stay 'potential'."""
    forbidden = ("definitive", "proof", "certain", "guaranteed fake", "confirmed fake")
    for _, _, text in VERDICT_BANDS:
        low = text.lower()
        assert not any(f in low for f in forbidden), text
    assert "never definitive proof" in SAFETY_NOTICE.lower()


def test_higher_modality_scores_raise_overall():
    low = fuse([Modality("image", True, 0.1, 0.8), Modality("audio", True, 0.1, 0.8)])
    high = fuse([Modality("image", True, 0.8, 0.8), Modality("audio", True, 0.8, 0.8)])
    assert high["overall_score"] > low["overall_score"]


def test_temperature_softens_confident_scores():
    """Calibration should pull an extreme fused score toward 0.5, not amplify it."""
    res = fuse([Modality("image", True, 0.95, 0.9), Modality("audio", True, 0.95, 0.9)])
    assert res["overall_score"] < 0.95  # softened


def test_disagreement_lowers_confidence():
    agree = fuse([Modality("image", True, 0.8, 0.9), Modality("audio", True, 0.8, 0.9)])
    disagree = fuse([Modality("image", True, 0.1, 0.9), Modality("audio", True, 0.9, 0.9)])
    assert disagree["cross_modal_consistency"] < agree["cross_modal_consistency"]
    assert disagree["calibrated_confidence"] < agree["calibrated_confidence"]


def test_no_modalities_is_safe():
    res = fuse([])
    assert res["overall_score"] == 0.0
    assert res["verdict_band"] == "Low"


def test_verdict_bands_monotonic():
    assert verdict_for(0.0)[0] == "Low"
    assert verdict_for(0.5)[0] == "Elevated"
    assert verdict_for(0.9)[0] == "Very High"
