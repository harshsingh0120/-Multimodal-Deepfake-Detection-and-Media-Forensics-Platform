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

## 3. Harness self-test (synthetic — NOT real-world accuracy)

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

## 4. Bottom line

- **Current measured real-world accuracy: none claimed** — by design, and stated openly.
- **To obtain it:** point `evaluation/evaluate.py` at a labelled dataset; the harness returns
  AUC / EER / accuracy / ECE for fusion vs. the baselines.
- **Software is verified:** 28/28 automated tests pass (see `TESTING.md`); the evaluation harness
  is demonstrated working on a labelled synthetic set above.
