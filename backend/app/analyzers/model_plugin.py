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

    def __init__(self, model_id: str, fake_index: int = -1, tta: bool = False):
        self.model_id = model_id
        self.fake_index_override = fake_index
        self.tta = tta
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

    def _p_fake(self, pil_img) -> float:
        inputs = self._proc(images=pil_img, return_tensors="pt")
        with self._torch.no_grad():
            logits = self._model(**inputs).logits
        probs = self._torch.softmax(logits, dim=-1)[0]
        return float(probs[self._fake_idx].item())

    def predict(self, payload) -> float:
        self._ensure_loaded()
        import numpy as np
        from PIL import Image

        img = payload
        if isinstance(img, np.ndarray):
            img = Image.fromarray(img[:, :, ::-1])  # BGR → RGB
        p = self._p_fake(img)
        if self.tta:  # average with the horizontal flip
            p = 0.5 * (p + self._p_fake(img.transpose(Image.FLIP_LEFT_RIGHT)))
        return p


class _EnsembleImageModel:
    """Averages P(fake) across several image models (optionally with TTA)."""

    modality = "image"

    def __init__(self, members: list[_HFImageClassifier]):
        self.members = members

    def predict(self, payload) -> float:
        scores = [m.predict(payload) for m in self.members]
        return float(sum(scores) / len(scores)) if scores else 0.0


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
        ids = [m.strip() for m in s.IMAGE_MODEL_ID.split(",") if m.strip()]
        idx_tokens = [t.strip() for t in str(s.IMAGE_MODEL_FAKE_INDEX).split(",") if t.strip()]
        def _idx_for(i: int) -> int:
            tok = idx_tokens[i] if i < len(idx_tokens) else (idx_tokens[0] if idx_tokens else "-1")
            try:
                return int(tok)
            except ValueError:
                return -1
        members = [_HFImageClassifier(mid, _idx_for(i), s.IMAGE_MODEL_TTA)
                   for i, mid in enumerate(ids)]
        registry["image"] = members[0] if len(members) == 1 else _EnsembleImageModel(members)

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
