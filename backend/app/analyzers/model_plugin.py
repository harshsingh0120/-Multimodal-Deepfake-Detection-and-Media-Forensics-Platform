"""Pluggable deep-model interface.

The always-on engine uses interpretable forensic signal processing (no GPU / no
datasets required, fully reproducible). For teams that have trained checkpoints
(e.g. ViT/EfficientNet on FaceForensics++, wav2vec2/AASIST on ASVspoof, SyncNet for
lip-sync), this module defines a drop-in contract: set the corresponding
`*_MODEL_PATH` env var and implement `predict()` to return a score in [0, 1].

When no weights are configured, `load_plugins()` returns an empty registry and the
pipeline transparently falls back to the forensic analyzers. This keeps the system
honest: we never fabricate a "model" score when no model is present.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

from ..config import get_settings


class ModalityModel(Protocol):
    modality: str

    def predict(self, payload) -> float:  # returns manipulation probability in [0,1]
        ...


class _HFImageClassifier:
    """Trained image deepfake detector via Hugging Face `transformers`.

    Wraps any `*ForImageClassification` model (e.g. a ViT fine-tuned for real/fake
    faces). Returns P(fake) for a BGR numpy frame. torch + transformers are imported
    lazily so the core engine never depends on them.
    """

    modality = "image"

    def __init__(self, model_id: str, fake_index: int = -1):
        self.model_id = model_id
        self.fake_index_override = fake_index
        self._model = None
        self._proc = None
        self._torch = None
        self._fake_idx = 1

    def _ensure_loaded(self):
        if self._model is not None:
            return
        import torch
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        self._torch = torch
        self._proc = AutoImageProcessor.from_pretrained(self.model_id)
        self._model = AutoModelForImageClassification.from_pretrained(self.model_id)
        self._model.eval()
        if self.fake_index_override >= 0:
            # Explicit override — needed for checkpoints whose id2label is reversed
            # (e.g. dima806/deepfake_vs_real_image_detection → fake index is 0).
            self._fake_idx = self.fake_index_override
        else:
            id2label = getattr(self._model.config, "id2label", {}) or {}
            self._fake_idx = next(
                (int(i) for i, lbl in id2label.items() if "fake" in str(lbl).lower()
                 or "spoof" in str(lbl).lower()),
                1 if len(id2label) > 1 else 0,
            )

    def predict(self, payload) -> float:
        self._ensure_loaded()
        import numpy as np
        from PIL import Image

        img = payload
        if isinstance(img, np.ndarray):
            img = Image.fromarray(img[:, :, ::-1])  # BGR → RGB
        inputs = self._proc(images=img, return_tensors="pt")
        with self._torch.no_grad():
            logits = self._model(**inputs).logits
        probs = self._torch.softmax(logits, dim=-1)[0]
        return float(probs[self._fake_idx].item())


class _TorchCheckpointModel:
    """Reference wrapper. Loads a torch checkpoint lazily.

    Implement `predict()` for your architecture. This stub intentionally raises until
    specialised, so an unconfigured/partial plugin never silently returns fake scores.
    """

    def __init__(self, modality: str, weights_path: str):
        self.modality = modality
        self.weights_path = weights_path
        self._model = None

    def _ensure_loaded(self):
        if self._model is not None:
            return
        import torch  # noqa: lazy import; torch is optional

        self._model = torch.load(self.weights_path, map_location="cpu")
        self._model.eval()

    def predict(self, payload) -> float:
        self._ensure_loaded()
        raise NotImplementedError(
            f"Implement inference for the '{self.modality}' checkpoint at "
            f"{self.weights_path} (preprocess `payload` → model → probability)."
        )


def load_plugins() -> dict[str, ModalityModel]:
    """Return {modality: model} for every configured plugin.

    Priority for the image branch: a Hugging Face `IMAGE_MODEL_ID` (trained classifier)
    overrides the generic torch-checkpoint path.
    """
    s = get_settings()
    registry: dict[str, ModalityModel] = {}

    if s.IMAGE_MODEL_ID:
        registry["image"] = _HFImageClassifier(s.IMAGE_MODEL_ID, s.IMAGE_MODEL_FAKE_INDEX)

    for modality, path in (
        ("image", s.IMAGE_MODEL_PATH),
        ("audio", s.AUDIO_MODEL_PATH),
        ("sync", s.SYNC_MODEL_PATH),
    ):
        if modality in registry:
            continue
        if path and Path(path).exists():
            registry[modality] = _TorchCheckpointModel(modality, path)
    return registry


def active_engine_name() -> str:
    plugins = load_plugins()
    if plugins:
        return "forensic-engine + trained-plugins(" + ",".join(sorted(plugins)) + ")"
    return "interpretable-forensic-engine v1.0"


def try_model_score(registry: dict, modality: str, payload) -> Optional[float]:
    """Attempt a plugin prediction; return None on any failure (engine falls back)."""
    model = registry.get(modality)
    if model is None:
        return None
    try:
        val = float(model.predict(payload))
        return min(1.0, max(0.0, val))
    except Exception:
        return None
