# Presentation Guide — Deepfake Forensics Platform

Companion to **`Deepfake_Forensics_Pitch.pptx`** (22 slides). Contains:

1. How to use this deck
2. Slide-by-slide explanation + speaker notes (what to say)
3. 28 likely judge questions with suggested answers
4. A concise live-demo script

> **Accuracy pledge for the whole deck:** every technology, number and claim matches the real
> codebase. Where the generic "AI-agent" template expected an LLM, RAG, vector DB, external APIs,
> a database or auth, we state plainly that these are **not used** and why — that honesty is a
> strength, not a gap.

Fill in the placeholders `[Your Team Name]`, `[Member 1–3]` on slides 1 and 22 before presenting.

---

## 1. How to use this deck

- **Timing:** 22 slides. At ~45–60s each you land around 18–20 minutes; for a 7–8 minute pitch, present slides **1, 3, 5, 6, 8, 13, 18, 19, 21** and keep the rest as backup/appendix.
- **Design:** dark "forensic" theme, teal accent, one message per slide, diagrams over paragraphs.
- **Speaker notes** are embedded in the .pptx (View → Notes) — the same text is reproduced below.
- **The three slides that win:** Slide 8 (honest "not a chatbot" framing), Slide 16 (the label-bug debugging story), Slide 18 (measured, honest accuracy). These prove you *built and understand* it.

---

## 2. Slide-by-slide explanation + speaker notes

### Slide 1 — Title
**Purpose:** set the one-line identity and the "evidence, not proof" principle.
**Say:** "We built the Multimodal Deepfake Detection & Media Forensics Platform. Upload an image, video or audio clip and get a structured, explainable report on how likely it's manipulated — across every modality. Our principle throughout: we report *evidence of potential manipulation*, never definitive proof."

### Slide 2 — Introduction
**Purpose:** what it is / does / who benefits, in three cards.
**Say:** "It's a web app with an analysis engine. It doesn't just say fake or real — it breaks the decision into four forensic signals, shows where and why, and produces a PDF. Journalists, bank fraud teams and trust-&-safety analysts benefit directly."

### Slide 3 — Problem
**Purpose:** establish the real-world pain and why single-modality/black-box tools fail.
**Say:** "Deepfakes are cheap and convincing. Single-modality detectors fail — attackers mix a fake face with cloned audio or just compress the file. Most tools are black boxes and overfit to one generator. In practice: voice-clone CEO fraud, fake videos of public figures, face-swapped KYC selfies."

### Slide 4 — Motivation & Social Impact
**Purpose:** why it matters to society; the beneficiaries.
**Say:** "The target is trust itself. When any clip can be dismissed as fake, real evidence loses power too. We put a fast, explainable triage tool in the hands of the people who verify media."

### Slide 5 — Proposed Solution
**Purpose:** the Upload→Analyse→Fuse→Report pipeline and the six functionalities.
**Say:** "One pipeline: upload, analyse four branches, fuse with calibrated confidence, report. Separate per-modality scores plus a fused score, explainable evidence, heatmaps, flagged frames/segments, and a PDF."

### Slide 6 — System Architecture
**Purpose:** show the components and data flow; stress "no database, stateless".
**Say:** "Frontend → FastAPI → pipeline → four branches → late fusion + calibration → report. An optional pre-trained ViT can replace the image score. Stateless: no database; media is processed transiently."

### Slide 7 — Technology Stack
**Purpose:** every tech grouped, with role.
**Say:** "Python 3.12 and TypeScript; React/Vite/Tailwind; FastAPI; OpenCV and librosa for vision and audio; scikit-learn and optional PyTorch/Transformers; ReportLab and bundled ffmpeg. Mature libraries, no exotic or paid dependencies."

### Slide 8 — How the AI system works (honest reframe)
**Purpose:** define "agent" accurately; separate from chatbots.
**Say:** "Ours is agentic — it receives input, decides which tools to run, runs them, returns a reasoned decision — but there's no language model, no prompts, no conversation. A chatbot predicts words; our agent measures physical signals with specialised tools and returns a reproducible, inspectable decision."

### Slide 9 — AI / ML Implementation
**Purpose:** the three layers (engine, ViT, fusion) + the honest "not used" box.
**Say:** "Three layers: an interpretable forensic engine with no training; an optional pre-trained ViT we download and run; and a learned logistic-regression fusion. We deliberately use no LLM, RAG, embeddings or vector DB — this is a perception problem, not a language one."

### Slide 10 — Backend Implementation
**Purpose:** modules, endpoints, request flow.
**Say:** "FastAPI app: main.py routes and validation, utils/media.py for ingest and ffmpeg demux, analyzers for each branch, pipeline.py orchestrates, pdf_report.py builds the PDF. POST /api/analyze returns the JSON; /api/report/{id} the PDF. Temp files are deleted after."

### Slide 11 — Frontend Implementation
**Purpose:** the React dashboard and how it talks to the backend.
**Say:** "React 18 + Vite + TypeScript + Tailwind, compiled to static files the backend can serve. A fetch() POST to /api/analyze; the typed JSON drives the gauge, bars, evidence, heatmaps."

### Slide 12 — APIs & External Integrations
**Purpose:** what talks to what; the "no API keys" headline.
**Say:** "At runtime, one API: our own. At build time, anonymous public downloads from Hugging Face for the model and dataset. ffmpeg is a bundled binary, not a service. Zero API keys anywhere — nothing to leak."

### Slide 13 — Complete Working Workflow
**Purpose:** the 7-step end-to-end flow and edge-case handling.
**Say:** "Upload → validate → ingest/demux → analyse branches → fuse & calibrate → build report → deliver. We handle no-face, no-audio, corrupt, oversized and empty files gracefully — that's what makes it a working prototype, not a happy-path demo."

### Slide 14 — Important Features
**Purpose:** each feature with mechanism + tech.
**Say:** "Per-modality and fused scoring; lip-sync by correlating mouth motion with audio loudness; ELA/FFT heatmaps; flagged frames and segments; calibrated confidence; and the PDF — each built from OpenCV, librosa, scikit-learn, ReportLab."

### Slide 15 — Security, Reliability & Limitations
**Purpose:** safety posture + honest limits; the "no hallucination" point.
**Say:** "Validation, transient storage, no DB, no secrets, CORS allow-list. 32 tests pass; graceful edge cases; deterministic and stateless. Limits stated openly. There's no generative model, so nothing to hallucinate."

### Slide 16 — Implementation Challenges
**Purpose:** prove you built it — real bugs and fixes.
**Say:** "OpenCV 5 removed the face detector → pinned 4.10. No system ffmpeg → bundled it. The pre-trained ViT scored *worse than chance* → we found a reversed label in the model, verified on known-real faces, and fixed it to 0.78. Our own engine was chance-level → we reported it honestly and added the trained path."

### Slide 17 — Demo & Screenshots
**Purpose:** show the real product.
**Say:** "Real screenshots: the verdict dashboard with gauge and evidence, and an ELA heatmap showing *where* the image looks edited. In the live demo I'll upload a sample and download the PDF."

### Slide 18 — Evaluation & Results
**Purpose:** the honest, measured numbers — the credibility slide.
**Say:** "We measured on 237 real-vs-deepfake faces, cross-dataset, no test-set tuning. The engine alone is 0.27 — below chance, and we say so. The ViT reaches 0.78. The learned fusion of the ViTs *with* our engine reaches 0.82 with near-perfect calibration. Our 'weak' signal is complementary — it makes a strong model better."

### Slide 19 — Innovation & Competitive Advantage
**Purpose:** six differentiators.
**Say:** "Truly multimodal *and* cross-modal; explainable by construction; proven complementary fusion; honest and responsible; zero lock-in; and the right agentic shape for a perception task."

### Slide 20 — Future Scope
**Purpose:** credible roadmap that fits the architecture.
**Say:** "Fine-tune with identity-disjoint cross-generator splits; drop in trained audio/video plugins; attention fusion; containerised scale; richer localisation; case management. Every heavy model is already an optional plugin."

### Slide 21 — Conclusion
**Purpose:** tie problem→solution→tech→proof→impact; strong close.
**Say:** "Problem: deepfakes defeat single-modality black boxes. Solution: a multimodal, explainable platform. Tech: mature and open, no GPU, no keys. Proof: tests pass, AUC 0.82 honestly measured. Impact: a practical triage tool. We don't just claim a number — we show the evidence, the limits, and the reasoning. That's what forensics should be."

### Slide 22 — Thank You / Q&A
**Say:** "Thank you — questions? Happy to run the live demo, walk through the lip-sync math, or discuss how we measured accuracy honestly."

---

## 3. Judge Q&A — 28 questions with suggested answers

**Framing / scope**

1. **"Is this really an AI agent?"** — It's agentic in the real sense: it autonomously decides which analysis tools to run per file, runs them, and returns a reasoned decision. It is not an LLM chatbot — and we're explicit about that. For a perception task, measuring signals with specialised tools is the correct design; a language model would add cost and opacity without improving detection.

2. **"Where's the LLM / RAG / vector database?"** — Deliberately absent. The task is image/audio perception, not language. We use computer-vision and audio models instead. Adding RAG/vectors would be buzzword-driven, not problem-driven.

3. **"Why should I trust a tool with no neural net in the core?"** — The *core* is interpretable signal processing so every output is explainable and reproducible. For raw accuracy we add an optional trained ViT. You get explainability by default and accuracy on demand — and we measured both.

**Technical depth**

4. **"How does the lip-sync check actually work?"** — We build a per-frame "mouth openness" signal from the detected face region, build the audio loudness (RMS) envelope, resample both to a common timeline, and compute their cross-correlation with a small lag search. Genuine talking heads correlate strongly at a plausible lag; dubbed or cloned audio does not.

5. **"How is the fused score computed?"** — Confidence-weighted late fusion of the available branch scores, plus a penalty when branches disagree, then temperature scaling to calibrate confidence. Weights are documented, not black-box.

6. **"What is temperature scaling / ECE?"** — Temperature scaling divides the model's logit by a constant T>1 to soften over-confident probabilities. ECE (Expected Calibration Error) measures whether a "70% fake" prediction is actually fake ~70% of the time. Our fused ECE is 0.025 — very well calibrated.

7. **"Why is your own engine below 0.5 AUC — isn't that broken?"** — It's *inverted* for this generator: these GAN faces are smoother than the real JPEGs, and our engine assumes "synthetic ⇒ extra artifacts". We report it honestly rather than hide it; and in fusion that signal is still useful because a learned combiner can use its sign.

8. **"Then how does fusion beat the best single model?"** — The engine's errors are *complementary* to the ViT's. A logistic combiner learns to weight each signal (including the engine's inverted direction), lifting AUC from 0.78 to 0.82 and massively improving calibration.

9. **"How did you avoid data leakage?"** — No training on the test set; the fusion is 5-fold cross-validated out-of-fold; thresholds are never tuned on the evaluation data. We also flag the one caveat: a single dataset may share identities across folds, so we call the number directional.

10. **"How do you get frames and audio from a video?"** — OpenCV samples frames evenly (capped for speed); the bundled ffmpeg (via imageio-ffmpeg) demuxes the audio track to a mono WAV the audio branch analyses.

11. **"What exactly does the image branch measure?"** — Error-Level Analysis (recompression inconsistency), FFT high-frequency energy and spectral peaks (GAN upsampling artifacts), face-vs-background noise and sharpness ratios. Each is a documented formula.

12. **"What does the audio branch measure?"** — Energy and brightness micro-variation, MFCC dynamism, spectral flatness, band-limiting/roll-off, and noise-floor cleanliness — cues that separate natural speech from TTS/vocoder output.

**Engineering / architecture**

13. **"Why FastAPI over Flask/Django?"** — It's async, typed (Pydantic validation), auto-generates OpenAPI docs, and is explicitly suggested by the problem. Less boilerplate than Django for a single-purpose API; stronger typing than Flask.

14. **"Why React + Vite + Tailwind?"** — React for component structure, Vite for instant builds and a dev proxy, Tailwind for consistent styling without a CSS sprawl. It compiles to static files our backend serves.

15. **"Why no database?"** — Privacy by design. Uploaded media is sensitive; we process it transiently and delete it. Results live in a short-lived in-memory cache. Statelessness also means we scale by adding workers.

16. **"How does it scale?"** — The API is stateless, so horizontal scaling is `uvicorn --workers N` or more replicas behind a load balancer. Heavy models are optional, cached, lazily loaded. Future: a queue + worker pool for batch/stream.

17. **"Do you need a GPU?"** — No. The core engine is CPU-only. The optional ViT also runs on CPU (slower first request while it loads); a GPU would speed it up but isn't required.

18. **"How big is the model and where does it come from?"** — The optional ViT is a ~340 MB public checkpoint from Hugging Face, downloaded anonymously once and cached. No account or key.

**Security / reliability / ethics**

19. **"What stops a malicious upload?"** — Strict type and size validation, processing in an isolated temp dir, no code execution from uploaded content, and deletion after analysis. We only read pixels/audio samples.

20. **"How do you prevent AI hallucinations?"** — There's no generative model in the pipeline, so there's nothing to hallucinate. Outputs are deterministic measurements; the optional ViT returns a bounded probability, not free text.

21. **"Could this tool be misused to 'prove' something is real/fake?"** — We guard against it with wording: every verdict says *evidence of potential manipulation, never proof*, and a "Low" result explicitly does not guarantee authenticity. It's a triage aid for humans, not an authenticator.

22. **"What are the false-positive/negative risks?"** — Real but compressed media can trip visual cues (false positive); a high-quality unseen-generator fake can evade them (false negative). That's exactly why we fuse modalities, calibrate confidence, and show evidence for human review.

23. **"What are the honest limitations?"** — Indicators not proof; compression hides artifacts; limited generalisation to unseen generators; facial checks need a visible face; small evaluation sample. All stated on Slide 15 and in every report.

**Results / product**

24. **"Is 78% accuracy good enough?"** — As a cross-dataset, honestly-measured triage number with off-the-shelf models and no tuning, yes — it's credible and useful for human-in-the-loop review. It is not a sole authenticator, and we don't claim it is. The path to higher is in-domain fine-tuning.

25. **"How is this different from existing deepfake detectors?"** — Multimodal *and* cross-modal (lip-sync), explainable by construction, calibrated and honest, with a proven complementary-fusion result. Most tools are single-modality black boxes.

26. **"Can it run in real time / on a call?"** — Images and short clips are near-instant; long videos take seconds (we subsample frames). A streaming mode is future work (Slide 20).

27. **"What's the single most technically challenging feature?"** — The multimodal lip-sync consistency combined with calibrated fusion — and operationally, diagnosing and fixing the reversed-label bug in the pre-trained model.

28. **"If we gave you a GPU and a week, what would you do?"** — Fine-tune ViT/EfficientNet on FaceForensics++ and wav2vec2/AASIST on ASVspoof with identity-disjoint, cross-generator splits, add trained audio/video plugins and attention fusion, then re-run the same evaluation harness and publish AUC/EER/ECE.

---

## 4. Live-demo script (~2–3 minutes)

**Setup (before you present):**
```bash
# from the project root
./scripts/run.ps1          # builds frontend + starts server at http://localhost:8000
# optional: generate demo media
python scripts/generate_sample_media.py samples
```

**Script:**
1. **Open** `http://localhost:8000`. "This is the live platform — notice 'API online', meaning the browser is talking to our FastAPI backend."
2. **Upload a suspect audio** (`samples/suspect_audio.wav`). "Watch the staged loader — demux, visual, audio, sync, fusion, report." → Result: **Elevated**, audio score high. "It flagged synthetic-speech cues and shows exactly which ones."
3. **Reset, upload the suspect image** (`samples/suspect_image.png`). → **Guarded**. **Scroll to the ELA heatmap.** "This shows *where* the image recompresses differently — localisation, not just a score."
4. **Upload the authentic image** for contrast → **Low**. "Same engine, clean result."
5. **Click Download PDF.** "Every analysis produces a shareable forensic record — verdict, evidence, heatmaps, limitations."
6. *(Optional, if time)* "And this is the honest part —" show `docs/DATASET_EVALUATION_REPORT.pdf` ROC curve. "Measured on real data: our engine alone is chance, the trained model is 0.78, fusion is 0.82. We show the evidence, not just a number."

**Fallback if the server won't start live:** present Slides 17 and 18 (screenshots + ROC) and the committed `docs/DATASET_EVALUATION_REPORT.pdf`.

**One-line close:** "We don't just claim a number — we show the evidence, the limits, and the reasoning. That's what forensics should be."
