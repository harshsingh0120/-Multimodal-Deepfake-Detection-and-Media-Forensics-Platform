"""Generate a *labelled* synthetic dataset to exercise the evaluation harness.

Creates  <out>/real/*  and  <out>/fake/*  with images, audio and a couple of videos,
at varying difficulty (some fakes are deliberately subtle, some reals carry mild
high-frequency content) so the resulting AUC/EER are non-degenerate.

IMPORTANT: these are controlled synthetic signals, NOT real deepfakes. Metrics on
this set demonstrate that the harness works and that the forensic signals separate
the controlled classes — they are NOT a claim of real-world accuracy. Point the
harness at a real labelled dataset (FaceForensics++, ASVspoof, …) for that.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, filtfilt

SR = 16000


# ------------------------------- images ------------------------------------ #

def _base_texture(rng, h=480, w=480):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = 120 + 60 * np.sin(xx / rng.uniform(140, 220)) + 40 * np.cos(yy / rng.uniform(110, 170))
    noise = rng.normal(0, 1, (h, w)).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), rng.uniform(1.6, 2.4)) * rng.uniform(14, 22)
    img = np.clip(base + noise, 0, 255).astype(np.uint8)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def real_image(rng):
    return _base_texture(rng)


def fake_image(rng):
    """Grid/upsampling artifact + over-smoothed patch; difficulty varies."""
    img = _base_texture(rng).astype(np.float32)
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    amp = rng.uniform(5.0, 18.0)                 # weak → subtle fake
    img += (amp * (np.sin(xx * np.pi / 2.0) + np.sin(yy * np.pi / 2.0)))[..., None]
    cy, cx = h // 2, w // 2
    r = min(h, w) // 4
    sigma = rng.uniform(2.5, 4.5)
    img[cy - r:cy + r, cx - r:cx + r] = cv2.GaussianBlur(
        img[cy - r:cy + r, cx - r:cx + r], (0, 0), sigma)
    return np.clip(img, 0, 255).astype(np.uint8)


# ------------------------------- audio ------------------------------------- #

def real_audio(rng, dur=3.0, sr=SR):
    t = np.linspace(0, dur, int(dur * sr), endpoint=False)
    f0 = rng.uniform(120, 170) + 30 * np.sin(2 * np.pi * 0.4 * t) + rng.normal(0, 4, t.shape)
    phase = np.cumsum(2 * np.pi * f0 / sr)
    sig = np.zeros_like(t)
    for k in range(1, 26):
        amp = (1.0 / k) * (1.0 + 0.6 * np.sin(2 * np.pi * (0.3 + 0.07 * k) * t + k))
        sig += amp * np.sin(k * phase)
    gate = (np.sin(2 * np.pi * rng.uniform(2.8, 3.6) * t) > -0.1).astype(np.float32)
    gate = gaussian_filter1d(gate, sigma=sr * 0.015)
    sig = sig * gate + rng.normal(0, 0.03, sig.shape)
    return (0.7 * sig / (np.max(np.abs(sig)) + 1e-9)).astype(np.float32)


def fake_audio(rng, dur=3.0, sr=SR):
    t = np.linspace(0, dur, int(dur * sr), endpoint=False)
    f0 = rng.uniform(120, 170)
    phase = np.cumsum(2 * np.pi * f0 / sr * np.ones_like(t))
    sig = np.zeros_like(t)
    for k in range(1, 13):
        sig += (1.0 / k) * np.sin(k * phase)
    # small, varying amount of residual variation so some fakes are subtler
    sig *= (0.8 + rng.uniform(0.0, 0.12) * np.sin(2 * np.pi * 3 * t))
    cutoff = rng.uniform(2500, 5200)
    b, a = butter(6, cutoff / (sr / 2), btype="low")
    sig = filtfilt(b, a, sig) + rng.normal(0, 0.004, sig.shape)
    return (0.7 * sig / (np.max(np.abs(sig)) + 1e-9)).astype(np.float32)


# ------------------------------- video ------------------------------------- #

def _write_video(path, frame_fn, n=36, fps=12, size=(320, 320)):
    h, w = size
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(n):
        vw.write(frame_fn(i))
    vw.release()


def real_video(path, rng):
    _write_video(path, lambda _i: _base_texture(rng, 320, 320))


def fake_video(path, rng):
    def frame(_i):
        return fake_image(rng)[:320, :320]
    _write_video(path, frame)


# ------------------------------- driver ------------------------------------ #

def generate(out: Path, per_class_images=8, per_class_audio=6, per_class_videos=1, seed=7):
    rng = np.random.default_rng(seed)
    (out / "real").mkdir(parents=True, exist_ok=True)
    (out / "fake").mkdir(parents=True, exist_ok=True)
    count = 0
    for i in range(per_class_images):
        cv2.imwrite(str(out / "real" / f"img_{i:02d}.png"), real_image(rng)); count += 1
        cv2.imwrite(str(out / "fake" / f"img_{i:02d}.png"), fake_image(rng)); count += 1
    for i in range(per_class_audio):
        sf.write(str(out / "real" / f"aud_{i:02d}.wav"), real_audio(rng), SR); count += 1
        sf.write(str(out / "fake" / f"aud_{i:02d}.wav"), fake_audio(rng), SR); count += 1
    for i in range(per_class_videos):
        real_video(out / "real" / f"vid_{i:02d}.mp4", rng); count += 1
        fake_video(out / "fake" / f"vid_{i:02d}.mp4", rng); count += 1
    return count


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("eval_synth")
    n = generate(out)
    print(f"Generated {n} labelled files under {out} (real/ and fake/).")
