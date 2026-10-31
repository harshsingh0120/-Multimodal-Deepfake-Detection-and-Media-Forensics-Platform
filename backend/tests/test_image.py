"""Image branch: discrimination, evidence, heatmaps, determinism (F3, A5, N4)."""
import cv2

from app.analyzers.image_analyzer import analyze_image_bgr


def test_suspect_scores_higher_than_authentic(samples):
    auth = cv2.imread(str(samples["authentic_image"]))
    susp = cv2.imread(str(samples["suspect_image"]))
    a = analyze_image_bgr(auth, make_heatmaps=False)
    s = analyze_image_bgr(susp, make_heatmaps=False)
    assert s.score > a.score + 0.1, (a.score, s.score)
    assert 0.0 <= a.score <= 1.0 and 0.0 <= s.score <= 1.0


def test_features_and_evidence_present(samples):
    img = cv2.imread(str(samples["suspect_image"]))
    res = analyze_image_bgr(img, make_heatmaps=True)
    for key in ("fft_highfreq_ratio", "fft_peakiness", "noise_residual_var",
                "sharpness_laplacian_var", "ela_p95"):
        assert key in res.features
    assert len(res.evidence) >= 3
    assert all(0.0 <= e.contribution <= 1.0 for e in res.evidence)


def test_heatmaps_emitted(samples):
    img = cv2.imread(str(samples["suspect_image"]))
    res = analyze_image_bgr(img, make_heatmaps=True)
    titles = [h["title"] for h in res.heatmaps]
    assert any("Error-Level" in t for t in titles)
    assert any("Frequency" in t for t in titles)
    assert all(h["image"].startswith("data:image/png;base64,") for h in res.heatmaps)


def test_determinism(samples):
    img = cv2.imread(str(samples["authentic_image"]))
    s1 = analyze_image_bgr(img, make_heatmaps=False).score
    s2 = analyze_image_bgr(img, make_heatmaps=False).score
    assert abs(s1 - s2) < 1e-9
