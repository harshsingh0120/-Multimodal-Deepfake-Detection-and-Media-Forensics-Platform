"""Orchestrator: ingest media → run modality analyzers → fuse → assemble response.

Routing:
  * image  → image branch
  * audio  → audio branch
  * video  → image branch (representative frame) + video (temporal) branch
             + audio branch + lip-sync branch (when an audio track exists)
Each branch returns an independent score (requirement F8). Fusion combines them.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from .analyzers import fusion as fusion_mod
from .analyzers.audio_analyzer import analyze_audio
from .analyzers.image_analyzer import analyze_image_bgr
from .analyzers.model_plugin import active_engine_name, load_plugins, try_model_score
from .analyzers.sync_analyzer import analyze_sync
from .analyzers.video_analyzer import analyze_video
from .utils import media as media_utils


def _evidence_list(items) -> list[dict]:
    return [{"name": e.name, "detail": e.detail, "contribution": round(float(e.contribution), 3)}
            for e in items]


def _round_features(feats: dict) -> dict:
    return {k: round(float(v), 4) for k, v in feats.items()}


GLOBAL_LIMITATIONS = [
    "Scores are interpretable forensic indicators, not the output of a model trained on "
    "labelled deepfakes; they flag *evidence*, never proof.",
    "Heavy compression, re-encoding, resizing or low resolution can suppress artifacts and "
    "lower reliability.",
    "Generalisation to unseen generators is inherently limited; a confident 'authentic' "
    "result does not guarantee authenticity.",
    "Face-dependent checks require a detectable frontal face; profile/occluded faces reduce "
    "coverage.",
]


def analyze_path(file_path: Path, original_name: str, size_bytes: int) -> dict:
    t_start = time.perf_counter()
    registry = load_plugins()
    ingest = media_utils.ingest(file_path)
    modalities: list[dict] = []
    fuse_inputs: list[fusion_mod.Modality] = []
    limitations = list(GLOBAL_LIMITATIONS)

    media_meta = {
        "filename": original_name,
        "media_type": ingest.media_type,
        "size_bytes": size_bytes,
        "duration_sec": ingest.meta.get("duration_sec"),
        "width": ingest.meta.get("width"),
        "height": ingest.meta.get("height"),
        "fps": ingest.meta.get("fps"),
        "has_audio": ingest.has_audio if ingest.media_type == "video" else (
            ingest.media_type == "audio"),
        "sample_rate": ingest.meta.get("sample_rate"),
    }

    # ---------------- IMAGE input ----------------
    if ingest.media_type == "image":
        ia = analyze_image_bgr(ingest.image, make_heatmaps=True)
        model_score = try_model_score(registry, "image", ingest.image)
        score = model_score if model_score is not None else ia.score
        modalities.append(_image_modality(ia, score, model_score is not None))
        fuse_inputs.append(fusion_mod.Modality("image", True, score, ia.confidence))

    # ---------------- AUDIO input ----------------
    elif ingest.media_type == "audio":
        aa = analyze_audio(ingest.audio.samples, ingest.audio.sr)
        model_score = try_model_score(registry, "audio", ingest.audio)
        score = model_score if model_score is not None else aa.score
        modalities.append(_audio_modality(aa, score, model_score is not None))
        fuse_inputs.append(fusion_mod.Modality("audio", True, score, aa.confidence))

    # ---------------- VIDEO input ----------------
    else:
        va = analyze_video(ingest.video)
        fuse_inputs.append(fusion_mod.Modality("video", True, va.score, va.confidence))
        modalities.append(_video_modality(va))

        # Representative-frame image branch (separate "image" score, req. F8)
        rep_idx = int(len(ingest.video.frames) // 2)
        rep_frame = ingest.video.frames[rep_idx]
        ia = analyze_image_bgr(rep_frame, make_heatmaps=True)
        modalities.insert(0, _image_modality(ia, ia.score, False,
                                             summary_prefix="Representative frame: "))
        fuse_inputs.append(fusion_mod.Modality("image", True, ia.score, ia.confidence * 0.8))

        if ingest.audio is not None:
            aa = analyze_audio(ingest.audio.samples, ingest.audio.sr)
            modalities.append(_audio_modality(aa, aa.score, False))
            fuse_inputs.append(fusion_mod.Modality("audio", True, aa.score, aa.confidence))

            sync = analyze_sync(va.mouth_series, va.mouth_times,
                                aa.envelope, aa.envelope_times)
            modalities.append(_sync_modality(sync))
            if sync.available:
                fuse_inputs.append(fusion_mod.Modality("sync", True, sync.score, sync.confidence))
            else:
                limitations.append("Lip-sync branch could not run on this clip "
                                   "(needs a talking face + audible speech).")
        else:
            modalities.append(_sync_modality_unavailable(
                "No audio track in this video — audio and lip-sync branches were skipped."))
            limitations.append("Video had no audio track; audio and lip-sync analysis skipped.")

    fusion_result = fusion_mod.fuse(fuse_inputs)
    processing_ms = int((time.perf_counter() - t_start) * 1000)

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engine": active_engine_name(),
        "media": media_meta,
        "modalities": modalities,
        "fusion": fusion_result,
        "limitations": limitations,
        "safety_notice": fusion_mod.SAFETY_NOTICE,
        "processing_ms": processing_ms,
    }


# ---------------- modality → schema dict converters ---------------- #

def _image_modality(ia, score, used_model, summary_prefix="") -> dict:
    return {
        "modality": "image",
        "available": True,
        "score": round(float(score), 4),
        "confidence": round(float(ia.confidence), 4),
        "summary": summary_prefix + ia.summary + (" [trained model]" if used_model else ""),
        "evidence": _evidence_list(ia.evidence),
        "features": _round_features(ia.features),
        "heatmaps": ia.heatmaps,
        "flagged_frames": [],
        "flagged_segments": [],
        "notes": ia.notes,
    }


def _audio_modality(aa, score, used_model) -> dict:
    return {
        "modality": "audio",
        "available": True,
        "score": round(float(score), 4),
        "confidence": round(float(aa.confidence), 4),
        "summary": aa.summary + (" [trained model]" if used_model else ""),
        "evidence": _evidence_list(aa.evidence),
        "features": _round_features(aa.features),
        "heatmaps": aa.heatmaps,
        "flagged_frames": [],
        "flagged_segments": aa.flagged_segments,
        "notes": aa.notes,
    }


def _video_modality(va) -> dict:
    return {
        "modality": "video",
        "available": True,
        "score": round(float(va.score), 4),
        "confidence": round(float(va.confidence), 4),
        "summary": va.summary,
        "evidence": _evidence_list(va.evidence),
        "features": _round_features(va.features),
        "heatmaps": va.heatmaps,
        "flagged_frames": va.flagged_frames,
        "flagged_segments": [],
        "notes": va.notes,
    }


def _sync_modality(sync) -> dict:
    return {
        "modality": "sync",
        "available": sync.available,
        "score": round(float(sync.score), 4),
        "confidence": round(float(sync.confidence), 4),
        "summary": sync.summary,
        "evidence": _evidence_list(sync.evidence),
        "features": _round_features(sync.features),
        "heatmaps": [],
        "flagged_frames": [],
        "flagged_segments": [],
        "notes": sync.notes,
    }


def _sync_modality_unavailable(msg: str) -> dict:
    return {
        "modality": "sync", "available": False, "score": 0.0, "confidence": 0.0,
        "summary": msg, "evidence": [], "features": {}, "heatmaps": [],
        "flagged_frames": [], "flagged_segments": [], "notes": [msg],
    }
