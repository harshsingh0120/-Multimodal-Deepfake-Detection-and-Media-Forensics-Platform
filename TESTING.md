# TESTING.md

Verification evidence for the Multimodal Deepfake Detection & Media Forensics Platform.
All results below were produced on the build machine (Windows 11, Python 3.12.10, Node v24,
OpenCV 4.10, librosa 1.0). Re-run instructions are in each section.

---

## 1. How to run the tests

```bash
# from repo root, with the backend venv active (see README)
cd backend
python -m pytest -q
```

The suite generates deterministic synthetic media on the fly (`scripts/generate_sample_media.py`)
— no external datasets are downloaded — then exercises every analyzer, the fusion layer, the
API, and robustness behaviour.

**Latest result:** `28 passed in 22.48s` ✅ (first run is slower due to librosa/numba JIT warm-up).

---

## 2. Automated test cases

| # | Test | What it verifies | Req | Expected | Actual | Status |
|---|------|------------------|-----|----------|--------|--------|
| 1 | `test_image::test_suspect_scores_higher_than_authentic` | Grid/denoise artifacts raise the image score | F3 | suspect > authentic + 0.1 | 0.02 → 0.22 | ✅ |
| 2 | `test_image::test_features_and_evidence_present` | ELA/FFT/noise/sharpness features emitted | F3,N1 | ≥5 features, ≥3 evidence | present | ✅ |
| 3 | `test_image::test_heatmaps_emitted` | ELA + frequency heatmaps as PNG data URIs | A5 | 2 heatmaps | present | ✅ |
| 4 | `test_image::test_determinism` | Same input → same score | N4 | Δ < 1e-9 | 0 | ✅ |
| 5 | `test_audio::test_suspect_audio_scores_higher` | Synthetic-speech cues raise audio score | F4 | suspect > authentic + 0.2 | 0.05 → 0.61 | ✅ |
| 6 | `test_audio::test_audio_features_present` | Spectral/MFCC features + envelope | F4,F6 | present | present | ✅ |
| 7 | `test_audio::test_spectrogram_and_segments` | Spectrogram image + typed segments | F9 | valid | valid | ✅ |
| 8 | `test_video::test_video_temporal_features` | Temporal/flow/jitter features | F5 | present | present | ✅ |
| 9 | `test_video::test_flagged_frames_structure` | Frame flags w/ timestamp + thumbnail | F9 | well-formed | ok | ✅ |
| 10 | `test_sync::test_synced_is_consistent` | Correlated lips/audio → low evidence | F6 | corr>0.6, score<0.5 | ok | ✅ |
| 11 | `test_sync::test_desynced_is_flagged` | Uncorrelated lips/audio → elevated | F6,A3 | corr<0.5, score>0.45 | ~0.59 | ✅ |
| 12 | `test_sync::test_unavailable_without_inputs` | Graceful "not evaluated" | F6,edge | unavailable | ok | ✅ |
| 13 | `test_fusion::test_safety_wording_never_definitive` | No band claims proof | **N2** | safe wording | ok | ✅ |
| 14 | `test_fusion::test_higher_modality_scores_raise_overall` | Monotone fusion | F7 | high > low | ok | ✅ |
| 15 | `test_fusion::test_temperature_softens_confident_scores` | Calibration pulls toward 0.5 | A4 | <0.95 | ok | ✅ |
| 16 | `test_fusion::test_disagreement_lowers_confidence` | Cross-modal disagreement penalised | A3,A4 | lower conf | ok | ✅ |
| 17 | `test_fusion::test_no_modalities_is_safe` | Empty input safe default | edge | Low/0.0 | ok | ✅ |
| 18 | `test_fusion::test_verdict_bands_monotonic` | Band thresholds correct | F10 | Low/Elevated/Very High | ok | ✅ |
| 19 | `test_robustness::test_image_stable_under_jpeg_recompression` | JPEG q75 re-encode stability | A2 | Δ < 0.25 | ok | ✅ |
| 20 | `test_robustness::test_image_stable_under_resize` | ½-resize preserves direction | A2 | suspect > authentic | ok | ✅ |
| 21 | `test_robustness::test_audio_stable_under_mild_noise` | +noise stability | A2 | Δ < 0.25 | ok | ✅ |
| 22 | `test_api::test_health` | Health endpoint | S2 | 200 ok | ok | ✅ |
| 23 | `test_api::test_config` | Config endpoint | S2 | 200 | ok | ✅ |
| 24 | `test_api::test_analyze_image_and_report` | Upload → JSON → PDF | F1,F10 | 200 + %PDF | ok | ✅ |
| 25 | `test_api::test_analyze_audio` | Audio upload path | F1,F4 | 200 | ok | ✅ |
| 26 | `test_api::test_reject_unsupported_type` | `.txt` rejected | N7 | 415 | ok | ✅ |
| 27 | `test_api::test_reject_empty_file` | Empty file rejected | N7 | 400/422 | ok | ✅ |
| 28 | `test_api::test_report_not_found` | Missing report | F10 | 404 | ok | ✅ |

---

## 3. Manual / integration verification

### 3.1 Dependency & build checks
| Check | Command | Result |
|-------|---------|--------|
| Backend deps install | `pip install -r backend/requirements.txt` | ✅ all wheels resolve on Py 3.12 |
| OpenCV face cascade | import check | ✅ Haar frontalface loads |
| Bundled ffmpeg | `/api/health` → `"ffmpeg": true` | ✅ |
| Frontend build | `npm run build` | ✅ `40 modules transformed … built in 1.11s` |
| Frontend typecheck | `tsc` | ✅ no errors |

### 3.2 End-to-end API smoke test (live server)
Backend started with `uvicorn app.main:app`; verified with `curl`:
```
GET  /api/health                      → 200 {"status":"ok","ffmpeg":true,...}
POST /api/analyze (suspect_image.png) → 200  band=Guarded overall=0.27
GET  /api/report/<id>                 → 200  application/pdf, 705,510 bytes, starts %PDF
GET  /                                → 200  serves built React app
```

### 3.3 Discrimination sanity run (`analyze_path` on sample media)
| Media | Overall | Band | Modalities (score) |
|-------|---------|------|--------------------|
| authentic_image.png | 0.05 | Low | image 0.02 |
| suspect_image.png | 0.27 | Guarded | image 0.22 |
| authentic_audio.wav | 0.09 | Low | audio 0.05 |
| suspect_audio.wav | 0.58 | Elevated | audio 0.61 |
| sample_video.mp4 | 0.08 | Low | image 0.06, video 0.02 |
| talking_video.mp4 | 0.09 | Low | image, video, audio (multimodal) |

Suspect variants score consistently higher than authentic variants across every modality.

### 3.4 UI verification (browser)
- Landing page renders (header, API-online badge, drag-&-drop upload). → `docs/screenshots/01_landing.jpg`
- Upload → loader stages → verdict banner (radial gauge, band, confidence, safety notice),
  per-modality cards with evidence bars, ELA/frequency heatmaps, Download-PDF button. →
  `docs/screenshots/02_results.jpg`, `docs/screenshots/03_heatmap.jpg`
- Browser console: **no errors**.

---

## 4. Edge cases covered
- Unsupported extension → `415`. Empty file → `400`. Oversized file → `413` (size guard).
- Image with no face → facial checks skipped, note surfaced, global forensics still run.
- Video with no audio track → audio + lip-sync branches skipped and noted.
- Very short audio / insufficient mouth movement / short A-V overlap → lip-sync "not evaluated".
- Corrupt/undecodable media → `422` with a friendly message.
- Expired/unknown report id → `404`.

---

## 5. Known limitations (see also README §Limitations)
- Scores are **interpretable forensic indicators**, not outputs of a model trained on labelled
  deepfakes; they flag *evidence of potential manipulation*, never proof.
- Absolute thresholds are calibrated against controlled synthetic signals and general forensic
  priors, not a held-out labelled benchmark (no datasets are bundled). Cross-dataset AUC/EER/ECE
  therefore require training the optional model plugins — the integration points are provided.
- Lip-sync requires a detectable frontal face (OpenCV Haar); profile/occluded/animated faces
  reduce coverage. End-to-end lip-sync is best demonstrated on real talking-head footage.
- No GPU is required or used; deep-model plugins are optional and disabled by default.

## 6. Remaining issues
None blocking. All 28 automated tests pass; API, PDF export, and UI verified end-to-end.
