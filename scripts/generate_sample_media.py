"""Generate deterministic synthetic sample media for demos and automated tests.

These are NOT real deepfakes — they are controlled signals that exercise each branch:
an "authentic-like" variant (natural statistics) and a "suspect-like" variant
(synthesis artifacts). Run directly to populate a `samples/` folder:

    python scripts/generate_sample_media.py samples
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf

SR = 16000
RNG = np.random.default_rng(42)


# ------------------------------- images ------------------------------------ #

def authentic_image(size=(480, 480)) -> np.ndarray:
    """Natural-looking texture: smooth gradients + spatially-correlated (1/f) noise."""
    h, w = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = 120 + 60 * np.sin(xx / 180.0) + 40 * np.cos(yy / 140.0)
    noise = RNG.normal(0, 1, (h, w)).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), 2.0) * 18.0  # correlated → low high-freq
    img = np.clip(base + noise, 0, 255).astype(np.uint8)
    bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    bgr[..., 2] = np.clip(bgr[..., 2].astype(np.float32) * 1.05, 0, 255).astype(np.uint8)
    return bgr


def suspect_image(size=(480, 480)) -> np.ndarray:
    """Synthesis cues: periodic high-frequency grid + an over-smoothed central patch."""
    img = authentic_image(size).astype(np.float32)
    h, w = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    grid = 16.0 * (np.sin(xx * np.pi / 2.0) + np.sin(yy * np.pi / 2.0))  # checkerboard-ish
    img += grid[..., None]
    cy, cx = h // 2, w // 2
    r = min(h, w) // 4
    patch = img[cy - r:cy + r, cx - r:cx + r]
    img[cy - r:cy + r, cx - r:cx + r] = cv2.GaussianBlur(patch, (0, 0), 4.0)  # denoised face
    return np.clip(img, 0, 255).astype(np.uint8)


# ------------------------------- audio ------------------------------------- #

def _harmonic(f0, dur, sr, harmonics, jitter=0.0, vibrato=0.0):
    t = np.linspace(0, dur, int(dur * sr), endpoint=False)
    sig = np.zeros_like(t)
    f = f0 * (1 + vibrato * np.sin(2 * np.pi * 5 * t)) if vibrato else f0 * np.ones_like(t)
    if jitter:
        f = f + RNG.normal(0, jitter * f0, t.shape)
    phase = np.cumsum(2 * np.pi * f / sr)
    for k in range(1, harmonics + 1):
        sig += (1.0 / k) * np.sin(k * phase)
    return t, sig


def authentic_audio(dur=3.0, sr=SR) -> np.ndarray:
    """Speech-like: drifting pitch, moving formants, syllabic gating, noise floor, full band."""
    from scipy.ndimage import gaussian_filter1d
    t = np.linspace(0, dur, int(dur * sr), endpoint=False)
    # Pitch contour: slow drift + fast jitter.
    f0 = 140 + 30 * np.sin(2 * np.pi * 0.4 * t) + RNG.normal(0, 4, t.shape)
    phase = np.cumsum(2 * np.pi * f0 / sr)
    # Moving formants: each harmonic amplitude modulated at its own rate.
    sig = np.zeros_like(t)
    for k in range(1, 26):
        amp = (1.0 / k) * (1.0 + 0.6 * np.sin(2 * np.pi * (0.3 + 0.07 * k) * t + k))
        sig += amp * np.sin(k * phase)
    # Syllabic gating: energy drops to near-zero between "syllables" → high dynamics.
    gate = (np.sin(2 * np.pi * 3.2 * t) > -0.1).astype(np.float32)
    gate = gaussian_filter1d(gate, sigma=sr * 0.015)
    sig = sig * gate
    sig += RNG.normal(0, 0.03, sig.shape)  # natural noise floor
    return (0.7 * sig / (np.max(np.abs(sig)) + 1e-9)).astype(np.float32)


def suspect_audio(dur=3.0, sr=SR) -> np.ndarray:
    """Synthetic-like: steady pitch, flat amplitude, band-limited, essentially noiseless."""
    t, sig = _harmonic(140, dur, sr, harmonics=12, jitter=0.0, vibrato=0.0)
    sig = sig * 0.8  # near-constant amplitude (low micro-variation)
    # band-limit (low-pass ~3 kHz) to emulate vocoder/resample cut-off
    from scipy.signal import butter, filtfilt
    b, a = butter(6, 3000 / (sr / 2), btype="low")
    sig = filtfilt(b, a, sig)
    return (0.7 * sig / (np.max(np.abs(sig)) + 1e-9)).astype(np.float32)


# ------------------------------- video ------------------------------------- #

def make_video(path: Path, n_frames=48, fps=12, size=(360, 360),
               mouth_from=None) -> None:
    """Write a silent MP4 with a moving 'mouth' patch (optionally driven by an envelope)."""
    h, w = size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
    for i in range(n_frames):
        frame = authentic_image((h, w))
        openness = (mouth_from[i] if mouth_from is not None and i < len(mouth_from)
                    else 0.5 + 0.5 * np.sin(i / 3.0))
        cy, cx = int(h * 0.62), w // 2
        axis = max(2, int(18 * abs(openness)))
        cv2.ellipse(frame, (cx, cy), (26, axis), 0, 0, 360, (20, 20, 30), -1)
        vw.write(frame)
    vw.release()


def mux_audio(video_in: Path, audio: np.ndarray, sr: int, out: Path) -> bool:
    """Mux a numpy audio track into a video using the bundled ffmpeg."""
    import imageio_ffmpeg
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        sf.write(str(wav), audio, sr)
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(video_in), "-i", str(wav),
               "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)]
        try:
            p = subprocess.run(cmd, capture_output=True, timeout=120)
            return p.returncode == 0 and out.exists()
        except Exception:
            return False


# ------------------------------- driver ------------------------------------ #

def generate_all(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    p = out_dir / "authentic_image.png"
    cv2.imwrite(str(p), authentic_image()); paths["authentic_image"] = p
    p = out_dir / "suspect_image.png"
    cv2.imwrite(str(p), suspect_image()); paths["suspect_image"] = p

    p = out_dir / "authentic_audio.wav"
    sf.write(str(p), authentic_audio(), SR); paths["authentic_audio"] = p
    p = out_dir / "suspect_audio.wav"
    sf.write(str(p), suspect_audio(), SR); paths["suspect_audio"] = p

    # Silent video (exercises video/temporal branch)
    silent = out_dir / "sample_video.mp4"
    make_video(silent); paths["sample_video"] = silent

    # Talking video with muxed audio (exercises full multimodal + lip-sync path)
    talking_silent = out_dir / "_talking_silent.mp4"
    aud = authentic_audio(dur=4.0)
    n = 48
    seg = max(1, len(aud) // n)
    env = np.array([np.abs(aud[i * seg:(i + 1) * seg]).mean() for i in range(n)])
    env = env / (env.max() + 1e-9)
    make_video(talking_silent, n_frames=n, mouth_from=env)
    talking = out_dir / "talking_video.mp4"
    if mux_audio(talking_silent, aud, SR, talking):
        paths["talking_video"] = talking
    talking_silent.unlink(missing_ok=True)

    return paths


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("samples")
    created = generate_all(out)
    print("Generated sample media:")
    for k, v in created.items():
        print(f"  {k:18s} -> {v}")
