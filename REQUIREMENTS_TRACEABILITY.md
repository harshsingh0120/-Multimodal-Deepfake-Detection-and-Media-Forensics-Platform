# REQUIREMENTS_TRACEABILITY.md

Every requirement from `02_deepfake_forensics.pdf` → implementation → test. Status is set to **Verified** only after the test passes (see `TESTING.md`).

Legend — Priority: **M** = Mandatory, **O** = Optional/bonus. Status: Pending / In Progress / Completed / **Verified**.

## Core Functional Requirements

| ID | Requirement | PDF loc. | Pri | Implementation | File(s) / module | Test | Status |
|----|-------------|----------|-----|----------------|------------------|------|--------|
| F1 | Image, video & audio upload | p1 Core #1 | M | Multipart upload endpoint + type sniffing | `backend/app/main.py` (`/api/analyze`), `backend/app/utils/media.py` | `test_api.py::test_analyze_image/audio/video` | Verified |
| F2 | Frame & audio-segment extraction | p1 Core #2 | M | Even frame sampling (OpenCV), audio demux via bundled ffmpeg, segment windowing | `utils/media.py` (`extract_frames`, `extract_audio`), `analyzers/audio_analyzer.py` | `test_media.py`, `test_video.py` | Verified |
| F3 | Detect facial artifacts & visual inconsistencies | p1 Core #3 | M | ELA, noise-residual face-vs-bg ratio, sharpness/edge consistency, FFT artifacts, Haar face detection | `analyzers/image_analyzer.py` | `test_image.py` | Verified |
| F4 | Detect synthetic speech / voice manipulation | p1 Core #4 | M | Spectral flatness/rolloff/bandwidth, MFCC stats, vocoder/band-limit cues, micro-variation | `analyzers/audio_analyzer.py` | `test_audio.py` | Verified |
| F5 | Temporal consistency across frames | p1 Core #5 | M | Optical-flow stats, per-frame score variance, face-box jitter | `analyzers/video_analyzer.py` (`_temporal_consistency`) | `test_video.py` | Verified |
| F6 | Lip-sync check (lips vs audio) | p1 Core #6 | M | Mouth-region openness time series ↔ audio RMS envelope correlation + best-lag | `analyzers/sync_analyzer.py` | `test_video.py::test_sync` | Verified |
| F7 | Multimodal fusion of predictions | p1 Core #7 | M | Weighted late fusion + disagreement penalty + temperature calibration | `analyzers/fusion.py` | `test_fusion.py` | Verified |
| F8 | Separate image/video/audio risk scores | p1 Core #8 | M | Each analyzer returns an independent `ModalityResult.score` surfaced in the response | `analyzers/*`, `schemas.py` | `test_fusion.py`, `test_api.py` | Verified |
| F9 | Highlight suspicious frames & audio segments | p1 Core #9 | M | Per-frame flags (timestamp+thumbnail) & per-segment flags (time range) | `video_analyzer.py`, `audio_analyzer.py` | `test_video.py`, `test_audio.py` | Verified |
| F10 | Forensic report with evidence & limitations | p1 Core #10 | M | JSON assessment + downloadable PDF with evidence, heatmaps, limitations | `report/pdf_report.py`, `main.py` (`/api/report/{id}`) | `test_api.py::test_report_pdf` | Verified |

## Advanced Challenges

| ID | Requirement | PDF loc. | Pri | Implementation | File(s) | Test | Status |
|----|-------------|----------|-----|----------------|---------|------|--------|
| A1 | Generalization to unseen generators | p1 | O | Generator-agnostic signal features; pluggable model slot; documented limitation | `analyzers/*`, `analyzers/model_plugin.py`, README | `test_image.py` (feature determinism) | Completed |
| A2 | Robustness to compression/resize/noise | p1 | O | Normalized inputs; robustness self-test (re-encode/resize/noise) | `backend/tests/test_robustness.py` | `test_robustness.py` | Verified |
| A3 | Cross-modal audio-video consistency | p1 | O | Sync branch + fusion disagreement penalty | `sync_analyzer.py`, `fusion.py` | `test_fusion.py::test_disagreement` | Verified |
| A4 | Confidence calibration | p1 | O | Temperature scaling; confidence from modality agreement & coverage | `fusion.py` (`calibrate`) | `test_fusion.py::test_calibration` | Verified |
| A5 | Partially manipulated / localized edits | p1 | O | ELA & noise heatmaps; per-region / per-frame / per-segment localisation | `image_analyzer.py` (heatmap), `utils/imaging.py` | `test_image.py::test_heatmap` | Verified |

## Non-Functional / Responsible-AI

| ID | Requirement | PDF loc. | Pri | Implementation | File(s) | Test | Status |
|----|-------------|----------|-----|----------------|---------|------|--------|
| N1 | Explainability | rubric | M | Evidence bullets + heatmaps + per-feature contributions | all analyzers, frontend | `test_api.py` (evidence present) | Verified |
| N2 | Safety wording ("potential", never "proof") | p2 Safety | M | Centralised verdict text; asserted in tests & PDF | `analyzers/fusion.py` (`VERDICT_BANDS`), `report/pdf_report.py` | `test_fusion.py::test_safety_wording` | Verified |
| N3 | Leakage prevention / honest eval | p2 Pitfalls | M | No training-on-test; interpretable features; documented | README §Evaluation | manual/doc | Completed |
| N4 | Reproducibility | rubric | M | Deterministic analysis, pinned `requirements.txt`, seeded sample gen | `requirements.txt`, `scripts/generate_sample_media.py` | `test_image.py` determinism | Verified |
| N5 | Scalability | rubric | O | Stateless API, modular analyzers, plugin slot | architecture | doc | Completed |
| N6 | Professional responsive UI | rubric | M | React + Tailwind dashboard, mobile→desktop | `frontend/` | manual UI test | Completed |
| N7 | Security / privacy | implied | M | Size+type validation, transient storage, env secrets, CORS allowlist | `config.py`, `main.py`, `.env.example` | `test_api.py::test_reject_bad_file` | Verified |
| N8 | Performance | implied | O | Frame subsampling, capped resolution | `video_analyzer.py` config | `test_video.py` timing | Completed |

## Submission Checklist (PDF p3)

| ID | Item | Deliverable | Status |
|----|------|-------------|--------|
| S1 | GitHub repo + setup | `README.md`, `.env.example`, `requirements.txt`, `package.json` | Completed |
| S2 | Working prototype / demo | running app + `scripts/generate_sample_media.py` demo flow | Verified |
| S3 | Documented architecture | `README.md` §Architecture, `REQUIREMENTS_ANALYSIS.md` | Completed |
| S4 | Dataset sources + preprocessing | `README.md` §Datasets & Methodology | Completed |
| S5 | Evaluation vs baselines | `README.md` §Evaluation, `backend/tests` | Completed |
| S6 | Limitations & failure cases | `README.md` §Limitations, every report | Completed |
| S7 | One technically challenging feature | multimodal lip-sync + calibrated fusion | Verified |
| S8 | Short presentation | `README.md` §Presentation | Completed |
