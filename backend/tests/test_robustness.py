"""Robustness (A2): scores should be stable under mild re-encoding / resizing / noise."""
import cv2
import numpy as np

from app.analyzers.audio_analyzer import analyze_audio
from app.analyzers.image_analyzer import analyze_image_bgr
from app.utils.media import ingest


def test_image_stable_under_jpeg_recompression(samples):
    img = cv2.imread(str(samples["authentic_image"]))
    base = analyze_image_bgr(img, make_heatmaps=False).score
    ok, enc = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    recon = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    after = analyze_image_bgr(recon, make_heatmaps=False).score
    assert abs(base - after) < 0.25, (base, after)


def test_image_stable_under_resize(samples):
    img = cv2.imread(str(samples["suspect_image"]))
    base = analyze_image_bgr(img, make_heatmaps=False).score
    small = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
    after = analyze_image_bgr(small, make_heatmaps=False).score
    # Direction (suspect stays elevated vs an authentic baseline) must be preserved.
    auth = analyze_image_bgr(cv2.imread(str(samples["authentic_image"])),
                             make_heatmaps=False).score
    assert after > auth


def test_audio_stable_under_mild_noise(samples):
    ing = ingest(samples["authentic_audio"])
    base = analyze_audio(ing.audio.samples, ing.audio.sr).score
    noisy = ing.audio.samples + np.random.default_rng(0).normal(
        0, 0.01, ing.audio.samples.shape).astype("float32")
    after = analyze_audio(noisy, ing.audio.sr).score
    assert abs(base - after) < 0.25, (base, after)
