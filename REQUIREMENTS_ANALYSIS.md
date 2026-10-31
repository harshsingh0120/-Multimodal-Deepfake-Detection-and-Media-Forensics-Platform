# REQUIREMENTS_ANALYSIS.md

> Problem 02 — **Multimodal Deepfake Detection and Media Forensics Platform**
> AI/ML & Deep Learning Hackathon · Domain: Cybersecurity / Computer Vision / Audio Processing / Multimodal AI · Difficulty: **Hard**
> Single source of truth: `02_deepfake_forensics.pdf` (3 pages). This document captures every requirement extracted from that PDF, line by line.

---

## 1. Problem Statement Summary

Deepfakes — fake video, cloned voice, manipulated images — enable fraud, impersonation and misinformation. **Single-modality detectors fail** when attackers combine fake video with synthetic audio, or when compression hides the artifacts a detector relies on. The platform must therefore analyse **multiple modalities together** and fuse the evidence.

## 2. The Actual Problem Being Solved

Give trust-and-safety professionals a **single tool** that ingests a piece of media (image, video, audio, or a combination), runs **forensic analysis across every available modality**, fuses the signals, and returns a **structured, explainable assessment** — not a black-box yes/no. The output must help a human analyst decide, and must be honest about uncertainty.

## 3. Target Users

| User | Need |
|------|------|
| Journalists | Verify footage/photos before publishing |
| Fact-checkers | Assess viral media authenticity |
| Bank fraud teams | Catch voice-cloning / impersonation in KYC & support calls |
| Trust-and-safety analysts | Triage reported media at scale |

## 4. Proposed Solution

A web platform (**FastAPI** backend + **React** frontend) implementing the PDF's reference architecture:

```
Upload → demux (ffmpeg) → face detector → visual branch
                                         → audio branch
                                         → temporal branch
                                         → sync (lip-sync) branch
      → late-fusion head (+ attention-fusion extension hook)
      → calibrator (temperature scaling)
      → report generator (JSON + downloadable PDF)
```

Each branch produces **real, measurable forensic features** (Error-Level Analysis, FFT/DCT spectral artifacts, noise-residual inconsistency, temporal flicker, spectral/vocoder cues, lip-sync correlation). Branch scores are fused, calibrated and explained. A **pluggable model interface** lets trained deep-learning checkpoints (ViT/EfficientNet, wav2vec2/AASIST, SyncNet) be dropped in without changing the pipeline.

## 5. Functional Requirements (from PDF "Core Requirements")

| # | Requirement (verbatim intent) |
|---|-------------------------------|
| F1 | Image, video and audio upload |
| F2 | Automatic frame and audio-segment extraction |
| F3 | Detect facial artifacts and visual inconsistencies |
| F4 | Detect synthetic speech / voice manipulation |
| F5 | Temporal consistency analysis across frames |
| F6 | Lip-sync check between lips and audio |
| F7 | Multimodal fusion of modality predictions |
| F8 | Separate image, video and audio risk scores |
| F9 | Highlight suspicious frames and audio segments |
| F10 | Forensic report with evidence and limitations |

## 6. Advanced Challenges (optional / bonus, PDF "Advanced Challenges")

| # | Challenge | How addressed |
|---|-----------|---------------|
| A1 | Generalization to unseen generators | Generator-agnostic forensic features (not tied to one GAN); pluggable model slot for cross-dataset models; honest limitation note |
| A2 | Robustness to compression, resizing, noise, re-encoding | Features computed on normalized inputs; ELA uses controlled re-compression; robustness discussed + a self-test harness |
| A3 | Cross-modal audio-video consistency | Dedicated lip-sync / sync branch (F6) + fusion penalises modality disagreement |
| A4 | Confidence calibration | Temperature scaling in the calibrator; Expected-Calibration-Error discussion |
| A5 | Partially manipulated media (localized edits) | ELA / noise-residual **heatmaps** localise suspicious regions; per-frame & per-segment flagging |

## 7. Non-Functional Requirements

| # | Requirement | Source / rationale |
|---|-------------|--------------------|
| N1 | Explainability / responsible AI | Rubric 10%; every score has evidence bullets + heatmaps |
| N2 | **Safety:** report "evidence of potential manipulation", never "definitive proof" | PDF "Safety Note" — mandatory wording |
| N3 | Leakage prevention / honest evaluation | Rubric; PDF "Pitfalls": no same-identity train/test leakage, no in-dataset-only accuracy |
| N4 | Reproducibility | Rubric "Data engineering"; deterministic analysis, pinned deps, documented setup |
| N5 | Scalability | Rubric "Innovation and scalability"; modular analyzers, stateless API, pluggable models |
| N6 | Usability / professional UI | Rubric "Presentation and demo"; responsive, clear, accessible UI |
| N7 | Security / privacy | Uploaded media handled transiently, not persisted beyond session; env-based secrets; size/type validation |
| N8 | Performance | PDF timeline implies interactive use; frame subsampling keeps analysis responsive |

## 8. Mandatory Features (must exist to avoid losing marks)

- All 10 core requirements **F1–F10**.
- Per-modality scores **and** a fused score (F7, F8).
- Heatmaps (F3/A5), flagged frames/segments (F9), confidence (A4), limitations (F10, N3).
- **Downloadable PDF report** (PDF "Expected Deliverable").
- Safety wording **N2** everywhere a verdict is shown.
- GitHub repo with setup instructions, documented architecture, dataset/preprocessing methodology, evaluation vs baselines, limitations/failure cases, one technically challenging feature, short presentation (PDF "Mandatory Submission Checklist").

## 9. Optional / Extension Features

- Attention-fusion (beyond late fusion) — architecture hook provided.
- Trained deep-model plugins (ViT/EfficientNet, wav2vec2/AASIST, SyncNet) — interface provided, weights optional.
- Robustness curves under JPEG/H.264 — self-test harness + methodology documented.

## 10. Technical Constraints & Technology Guidance

- **Suggested tech (followed):** PyTorch*, OpenCV, ViT/EfficientNet*, wav2vec2/AASIST*/spectrogram CNNs, SyncNet-style lip-sync*, Grad-CAM-style heatmaps, **FastAPI**.
  - Items marked `*` require GPU + large datasets to train; in this environment they are exposed as a **pluggable interface** (drop-in weights) while the always-on engine uses interpretable forensic signal processing. This is disclosed honestly (N1, N3).
- **No hard technology mandate** is stated beyond "Suggested"; FastAPI is adopted as it is explicitly suggested.
- Must run as a **working prototype** (rubric 10%).

## 11. Expected Inputs and Outputs

**Inputs:** a single file — image (`.jpg/.jpeg/.png/.webp/.bmp`), video (`.mp4/.mov/.avi/.mkv/.webm`), or audio (`.wav/.mp3/.flac/.m4a/.ogg`). Video may or may not carry an audio track.

**Outputs (JSON + PDF):**
- Overall verdict band + risk score (0–1) with safety wording.
- Separate **image / video / audio / sync** risk scores (those that apply).
- Calibrated confidence.
- Flagged frames (timestamps + thumbnails) and flagged audio segments (time ranges).
- Heatmaps (ELA/noise residual, frequency) and spectrogram.
- Evidence bullets per modality + overall.
- Limitations list.
- Downloadable forensic PDF report.

## 12. Evaluation Criteria & Judging Parameters

**Domain metrics (PDF "Evaluation"):** AUC, EER (audio), per-generator accuracy (cross-dataset), robustness curves under JPEG/H.264, ECE (calibration). Baselines: single-modality models, simple averaging fusion.

**Standard Judging Rubric (PDF p2–3):**

| Criterion | Weight |
|-----------|-------|
| Problem understanding | 10% |
| Technical depth | 20% |
| Data engineering (quality, leakage prevention, reproducibility) | 10% |
| Model performance (metrics, baselines, honest evaluation) | 15% |
| System architecture | 15% |
| Working prototype | 10% |
| Explainability and responsible AI | 10% |
| Innovation and scalability | 5% |
| Presentation and demo | 5% |

## 13. Submission Requirements (PDF "Mandatory Submission Checklist")

- ☐ GitHub repository with setup instructions → `README.md`
- ☐ Working prototype or recorded demo → running app + demo script
- ☐ Documented system architecture → `README.md` + this file
- ☐ Dataset sources and preprocessing methodology → `README.md` §Datasets & Methodology
- ☐ Evaluation results with baseline comparisons → `README.md` §Evaluation + `backend/tests`
- ☐ Limitations and failure cases → `README.md` §Limitations, every report
- ☐ One technically challenging feature demonstrated → **multimodal lip-sync + late-fusion calibration**
- ☐ Short presentation (problem, approach, results, future work) → `README.md` §Presentation

## 14. Potential Edge Cases

- Unsupported / corrupt file → validated, friendly error.
- Image with **no face** → facial-artifact checks marked N/A; global forensic checks still run.
- Video with **no audio track** → audio & sync branches skipped, noted in report.
- Audio-only file → image/video/sync skipped.
- Very short media (< 1 frame / < 0.5 s audio) → graceful handling.
- Oversized upload → rejected by size limit (env-configurable).
- Heavily compressed media → lower confidence, flagged as a robustness limitation.
- Multiple faces → analysed; largest face used for sync.

## 15. Ambiguities in the PDF (and resolutions)

| Ambiguity | Resolution |
|-----------|-----------|
| No explicit datasets shipped / no training mandate for the demo | Build an always-working interpretable forensic engine; expose trained-model plugin slot. Datasets (FaceForensics++, Celeb-DF, DFDC, FakeAVCeleb, ASVspoof, WaveFake) are documented as the methodology for the model path, not bundled (licensing + size). |
| "Downloadable PDF report" format unspecified | Standard A4 PDF via ReportLab with embedded evidence images. |
| Exact score scale unspecified | 0–1 risk with named bands; never a hard "fake/real" label (satisfies N2). |
| Fusion type ("late fusion first, attention as extension") | Late fusion implemented; attention-fusion left as a documented hook. |
| No auth requirement stated | No user auth required; security handled via validation, transient storage, env secrets. |
