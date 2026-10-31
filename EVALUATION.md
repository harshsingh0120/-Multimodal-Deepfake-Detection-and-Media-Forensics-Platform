# EVALUATION.md — Measuring Accuracy (AUC / EER / Accuracy / ECE)

> **Read this first.** The platform ships an *interpretable forensic engine*, not a model
> trained on labelled deepfakes. It therefore has **no inherent "accuracy %"** until you run it
> against a **labelled dataset**. This document provides the harness to do exactly that, and the
> metrics it produces.

---

## 1. What "accuracy" means here

A detection score is `P(manipulated) ∈ [0, 1]`. To measure quality you need media whose true
label (real / fake) is known, then you compute:

| Metric | Meaning | Better |
|--------|---------|--------|
| **ROC-AUC** | ranking quality across all thresholds | higher (1.0 = perfect) |
| **EER** | error rate where false-accept = false-reject (standard for audio/ASVspoof) | lower |
| **Accuracy / Precision / Recall / F1** | at the best decision threshold | higher |
| **Brier** | mean squared error of the probability | lower |
| **ECE** | Expected Calibration Error — do confidences match reality | lower |

The harness reports all of these for the **multimodal fusion** detector **and** the baselines the
problem statement names — each **single modality** and **simple averaging fusion** — so you can see
whether fusion actually helps.

## 2. Run it on a real labelled dataset

```bash
cd backend
# Option A — folder convention:
python -m evaluation.evaluate --data /path/to/dataset       # dataset/real/*  dataset/fake/*
# Option B — CSV manifest with columns: path,label  (label ∈ real|fake|0|1)
python -m evaluation.evaluate --manifest labels.csv --limit 500
```

Outputs a table to the console and writes `backend/evaluation/results/<timestamp>/report.md` and
`report.json` (per-file scores included).

**Recommended datasets** (from the problem statement): FaceForensics++, Celeb-DF v2, DFDC (sample)
for video/image; FakeAVCeleb for audio-video; **ASVspoof 2019/2021**, WaveFake, In-the-Wild for audio.
To avoid the leakage pitfall the problem warns about, **split by identity** and evaluate **cross-dataset**
(train/tune on one generator, test on another).

> For the strongest numbers, enable the trained-model plugins (`IMAGE_MODEL_PATH`, `AUDIO_MODEL_PATH`,
> `SYNC_MODEL_PATH` — see `backend/app/analyzers/model_plugin.py`); the same harness then scores the
> model-backed pipeline unchanged.

## 3. Measured result on a REAL public dataset (the honest answer)

**Dataset:** [`djramirezp/face-classification-dataset`](https://huggingface.co/datasets/djramirezp/face-classification-dataset)
(Hugging Face, MIT) — real human faces vs. GAN/diffusion-generated faces, 224×224.
**Subset scored:** 298 images (148 real / 150 fake), pulled balanced via the datasets-server CDN.
*(The gated benchmarks — FaceForensics++, ASVspoof, DFDC — require registered credentials and
multi-GB downloads, so this openly-licensed set was used as the honest substitute.)*

| Detector | AUC ↑ | EER ↓ | Accuracy ↑ | Brier ↓ | ECE ↓ |
|----------|------:|------:|-----------:|--------:|------:|
| **Multimodal fusion** (= image branch on stills) | **0.275** | 0.728 | **0.503** | 0.454 | 0.446 |

**Read this honestly — the engine does NOT beat chance on this dataset:**
- **Accuracy ≈ 50% = coin-flip.** On real GAN faces, the interpretable engine does **not** reliably
  separate fake from real.
- Mean scores: **real 0.068 vs. fake 0.053** — both near zero. The engine rarely flags these images
  at all, and ranks *real* faces as marginally *more* suspicious than the fakes, so AUC falls **below**
  0.5 (0.275, i.e. weakly inverted).
- **Root cause:** the hand-designed cues assume "synthetic ⇒ extra high-frequency / noise artifacts",
  but modern GAN faces here are *smoother and cleaner* than the real JPEG photographs — so the signal
  is weak and sign-flipped **for this generator**. This is exactly the *"generalization to unseen
  generators"* problem the brief warns about.
- **We deliberately do NOT re-tune thresholds on this test set** to inflate the number — that is the
  leakage pitfall the problem statement explicitly calls out. The legitimate fixes are (a) the
  **trained-model plugin path** (e.g. ViT/EfficientNet trained on FaceForensics++-style data) and
  (b) per-generator **calibration fitted on a separate split** — both already wired as integration
  points in `app/analyzers/model_plugin.py` and `app/analyzers/fusion.py`.

**Takeaway:** measured real-world accuracy on this set is **chance-level**. The interpretable engine
is a transparent, explainable **baseline and triage tool with an honest measurement harness — not a
production-grade detector.** That distinction, and this reproducible evidence, is the point.

## 4. Harness self-test (synthetic — NOT real-world accuracy)

To prove the harness works without downloading anything, generate a labelled **synthetic** set and
score it:

```bash
cd backend
python -m evaluation.make_eval_dataset ./eval_synth
python -m evaluation.evaluate --data ./eval_synth
```

Representative result on 30 controlled synthetic files (15 real / 15 fake):

| Detector | AUC ↑ | EER ↓ | Accuracy ↑ | Precision | Recall | F1 | Brier ↓ | ECE ↓ |
|----------|------:|------:|-----------:|----------:|-------:|---:|--------:|------:|
| **Multimodal fusion** | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.198 | 0.336 |
| Averaging baseline | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.217 | 0.330 |
| Single · image | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.300 | 0.398 |
| Single · video | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.460 | 0.465 |
| Single · audio | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.078 | 0.219 |

**How to read this — honestly:**
- ✅ It confirms the **harness, metrics, and full scoring pipeline work end-to-end**, and that the
  forensic signals cleanly separate the controlled classes (perfect ranking ⇒ AUC 1.0).
- ⚠️ It is **not** a real-world accuracy claim. The synthetic "fakes" carry deterministic artifacts
  (upsampling grid, band-limiting) that are far easier than production deepfakes. Expect materially
  lower AUC on FaceForensics++/ASVspoof/etc.
- 📉 The **Brier/ECE are non-trivial (~0.2–0.4)** even at AUC 1.0: the engine deliberately keeps
  absolute scores conservative ("evidence, not proof"), so probabilities are under-confident on
  obvious fakes. On a real labelled set you would fit the calibrator (temperature + the trained
  plugins) and re-measure ECE — the audio branch is already best-calibrated here (ECE 0.219).

## 5. Bottom line

- **Measured real-world accuracy (this public GAN-face set): ≈ 50% — chance level** (AUC 0.275).
  Reported openly rather than hidden. The interpretable engine does not generalise to this generator
  out of the box.
- **The platform's real value:** a complete, working multimodal pipeline + explainability
  (heatmaps, evidence, safety wording) + **this reproducible, honest measurement harness** that
  surfaces exactly where it fails.
- **To improve the number the right way:** enable the trained-model plugins and fit calibration on a
  held-out split (never on the test set), then re-run this harness on FaceForensics++ / ASVspoof.
- **Software is verified:** 32/32 automated tests pass (see `TESTING.md`); the harness is demonstrated
  on both a real public dataset (above) and a labelled synthetic set (below).
