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
    """Return {modality: model} for every configured & existing checkpoint."""
    s = get_settings()
    registry: dict[str, ModalityModel] = {}
    for modality, path in (
        ("image", s.IMAGE_MODEL_PATH),
        ("audio", s.AUDIO_MODEL_PATH),
        ("sync", s.SYNC_MODEL_PATH),
    ):
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
