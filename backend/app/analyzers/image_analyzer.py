"""Image forensic analyzer.

Measures generator-agnostic manipulation indicators on a still image (or a single
video frame):

  * Error-Level Analysis (ELA) — localised recompression error; splices/edits leave
    face regions with ELA statistics that differ from the surrounding image.
  * Frequency-domain analysis (FFT) — GAN/diffusion imagery tends to show abnormal
    high-frequency energy and periodic spectral peaks (upsampling grid artifacts).
  * Noise-residual consistency — synthetic / blended faces are often denoised, so the
    face carries less sensor noise than the background.
  * Sharpness consistency — over-smoothed faces vs. a sharp background.

Each indicator yields a bounded contribution; the logistic aggregator turns them into
an image manipulation-evidence score in [0, 1]. ELA and frequency heatmaps localise
the evidence (supports "partially manipulated media").
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from ..utils.imaging import heatmap_overlay, normalize01, png_data_uri
from .base import ScoreBuilder, ramp
from .faces import detect_faces


@dataclass
class ImageAnalysis:
    score: float
    confidence: float
    summary: str
    evidence: list = field(default_factory=list)
    features: dict = field(default_factory=dict)
    heatmaps: list = field(default_factory=list)
    faces: list = field(default_factory=list)
    notes: list = field(default_factory=list)


# ----------------------------- primitives ---------------------------------- #

def error_level_analysis(bgr: np.ndarray, quality: int = 90) -> np.ndarray:
    """Return a single-channel ELA magnitude map (float32)."""
    ok, enc = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return np.zeros(bgr.shape[:2], dtype=np.float32)
    recompressed = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    diff = cv2.absdiff(bgr, recompressed).astype(np.float32)
    return diff.mean(axis=2)


def noise_residual(gray: np.ndarray) -> np.ndarray:
    """High-frequency residual = image minus its denoised version."""
    denoised = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.4)
    return gray.astype(np.float32) - denoised.astype(np.float32)


def radial_highfreq_ratio(gray: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Return (high-freq energy ratio, spectral peakiness, log-magnitude spectrum)."""
    g = gray.astype(np.float32)
    g = g - g.mean()
    win = np.outer(np.hanning(g.shape[0]), np.hanning(g.shape[1]))
    f = np.fft.fftshift(np.fft.fft2(g * win))
    mag = np.abs(f)
    log_mag = np.log1p(mag)

    h, w = gray.shape
    cy, cx = h / 2.0, w / 2.0
    yy, xx = np.ogrid[:h, :w]
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    r_norm = r / r.max()

    total = float(mag.sum()) + 1e-9
    high = float(mag[r_norm > 0.5].sum())
    hf_ratio = high / total

    # Peakiness: excess kurtosis of the high-frequency magnitudes (grid artifacts
    # from transposed-conv upsampling produce sharp, regular spectral peaks).
    hf_vals = mag[r_norm > 0.5]
    if hf_vals.size > 16:
        m = hf_vals.mean()
        sd = hf_vals.std() + 1e-9
        peakiness = float(np.mean(((hf_vals - m) / sd) ** 4) - 3.0)
    else:
        peakiness = 0.0
    return hf_ratio, peakiness, log_mag


def _region_mean(map2d: np.ndarray, box) -> float:
    x, y, w, h = box
    sub = map2d[y:y + h, x:x + w]
    return float(sub.mean()) if sub.size else float(map2d.mean())


def _outside_mean(map2d: np.ndarray, box) -> float:
    mask = np.ones(map2d.shape[:2], dtype=bool)
    x, y, w, h = box
    mask[y:y + h, x:x + w] = False
    vals = map2d[mask]
    return float(vals.mean()) if vals.size else float(map2d.mean())


# ------------------------------- analyzer ---------------------------------- #

def analyze_image_bgr(bgr: np.ndarray, make_heatmaps: bool = True,
                      faces: list | None = None) -> ImageAnalysis:
    sb = ScoreBuilder()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    notes: list[str] = []

    if faces is None:
        faces = detect_faces(bgr)

    ela = error_level_analysis(bgr)
    resid = noise_residual(gray)
    hf_ratio, peakiness, log_mag = radial_highfreq_ratio(gray)

    ela_mean = float(ela.mean())
    ela_p95 = float(np.percentile(ela, 95))
    resid_var_global = float(resid.var())
    lap_var_global = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    sb.feat("ela_mean", ela_mean)
    sb.feat("ela_p95", ela_p95)
    sb.feat("fft_highfreq_ratio", hf_ratio)
    sb.feat("fft_peakiness", peakiness)
    sb.feat("noise_residual_var", resid_var_global)
    sb.feat("sharpness_laplacian_var", lap_var_global)
    sb.feat("faces_detected", float(len(faces)))

    # --- Frequency-domain indicators (global, generator-agnostic) ---
    # Healthy photographs concentrate energy in low frequencies; excess high-freq
    # ratio or strong spectral peaks indicate synthesis/upsampling artifacts.
    sb.add("Frequency high-band energy",
           f"High-frequency energy ratio = {hf_ratio:.3f} (elevated ratios are "
           f"associated with synthetic upsampling).",
           ramp(hf_ratio, 0.18, 0.42), weight=1.1)
    sb.add("Spectral peak regularity",
           f"High-band spectral peakiness = {peakiness:.1f} (regular peaks suggest "
           f"transposed-convolution grid artifacts).",
           ramp(peakiness, 6.0, 40.0), weight=1.0)

    # --- Global ELA energy ---
    sb.add("Global recompression error (ELA)",
           f"Mean ELA = {ela_mean:.2f}, p95 = {ela_p95:.2f}. Inconsistent recompression "
           f"error can indicate localized edits.",
           ramp(ela_p95, 10.0, 45.0), weight=0.9)

    # --- Face-conditioned indicators ---
    if faces:
        box = faces[0]
        face_ela = _region_mean(ela, box)
        bg_ela = _outside_mean(ela, box)
        ela_ratio = face_ela / (bg_ela + 1e-6)

        x, y, w, h = box
        face_gray = gray[y:y + h, x:x + w]
        face_resid = noise_residual(face_gray) if face_gray.size else resid
        face_noise = float(face_resid.var())
        bg_noise = resid_var_global
        noise_ratio = face_noise / (bg_noise + 1e-6)

        face_sharp = float(cv2.Laplacian(face_gray, cv2.CV_64F).var()) if face_gray.size else lap_var_global
        sharp_ratio = face_sharp / (lap_var_global + 1e-6)

        sb.feat("face_ela_ratio", ela_ratio)
        sb.feat("face_noise_ratio", noise_ratio)
        sb.feat("face_sharpness_ratio", sharp_ratio)

        sb.add("Face vs. background ELA",
               f"Face/background ELA ratio = {ela_ratio:.2f}. Values far from 1.0 "
               f"suggest the face was edited or blended separately.",
               max(ramp(ela_ratio, 1.6, 4.0), ramp(ela_ratio, 0.6, 0.25)), weight=1.2)
        sb.add("Face noise consistency",
               f"Face/background noise ratio = {noise_ratio:.2f}. A much smoother face "
               f"(low ratio) is a common blending/denoising artifact.",
               ramp(noise_ratio, 0.7, 0.2), weight=1.2)
        sb.add("Face sharpness consistency",
               f"Face/background sharpness ratio = {sharp_ratio:.2f}. An unusually soft "
               f"face region can indicate GAN synthesis.",
               ramp(sharp_ratio, 0.6, 0.15), weight=0.8)
    else:
        notes.append("No face detected — facial-artifact checks (F3) were skipped; "
                     "only global image forensics were applied.")

    score = sb.score()
    # Confidence: higher when a face is present and the image is reasonably sized.
    px = gray.shape[0] * gray.shape[1]
    size_conf = ramp(px, 80_000, 350_000)
    face_conf = 0.85 if faces else 0.55
    confidence = float(min(0.95, 0.35 + 0.4 * size_conf + 0.2 * (face_conf - 0.5) * 2))

    heatmaps = []
    if make_heatmaps:
        ela_vis = heatmap_overlay(bgr, normalize01(ela))
        for (x, y, w, h) in faces[:3]:
            cv2.rectangle(ela_vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
        heatmaps.append({
            "title": "Error-Level Analysis",
            "description": "Bright regions recompress differently from their surroundings "
                           "(possible localized manipulation). Green boxes mark detected faces.",
            "image": png_data_uri(ela_vis),
        })
        spec_vis = cv2.applyColorMap((normalize01(log_mag) * 255).astype(np.uint8),
                                     cv2.COLORMAP_INFERNO)
        heatmaps.append({
            "title": "Frequency spectrum",
            "description": "Log-magnitude 2D FFT. A bright central blob is normal; regular "
                           "off-center peaks or a bright high-frequency halo suggest synthesis.",
            "image": png_data_uri(spec_vis),
        })

    summary = _summarize(score, bool(faces))
    return ImageAnalysis(
        score=score, confidence=confidence, summary=summary,
        evidence=sb.top_evidence(6), features=sb.features,
        heatmaps=heatmaps, faces=faces, notes=notes,
    )


def _summarize(score: float, has_face: bool) -> str:
    face_txt = "a face was analysed" if has_face else "no face was found, global forensics only"
    if score < 0.33:
        lvl = "few visual manipulation indicators"
    elif score < 0.6:
        lvl = "some visual indicators worth review"
    else:
        lvl = "multiple visual manipulation indicators"
    return f"Image analysis found {lvl} ({face_txt})."
