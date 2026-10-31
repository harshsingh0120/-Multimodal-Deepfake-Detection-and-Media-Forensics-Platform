"""Pydantic response/request schemas for the API contract."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """A single named forensic indicator and its contribution."""

    name: str
    detail: str
    # Normalised contribution toward "evidence of manipulation" in [0, 1].
    contribution: float = Field(ge=0.0, le=1.0)


class FlaggedFrame(BaseModel):
    index: int
    timestamp_sec: float
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    thumbnail: Optional[str] = None  # base64 data URI


class FlaggedSegment(BaseModel):
    start_sec: float
    end_sec: float
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class HeatmapImage(BaseModel):
    title: str
    description: str
    image: str  # base64 data URI (PNG)


class ModalityResult(BaseModel):
    modality: Literal["image", "video", "audio", "sync"]
    available: bool
    score: float = Field(ge=0.0, le=1.0, description="Risk/manipulation-evidence score")
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    evidence: list[Evidence] = []
    features: dict[str, float] = {}
    heatmaps: list[HeatmapImage] = []
    flagged_frames: list[FlaggedFrame] = []
    flagged_segments: list[FlaggedSegment] = []
    notes: list[str] = []


class FusionResult(BaseModel):
    overall_score: float = Field(ge=0.0, le=1.0)
    calibrated_confidence: float = Field(ge=0.0, le=1.0)
    verdict_band: str
    verdict_text: str
    weights: dict[str, float]
    cross_modal_consistency: Optional[float] = None
    rationale: list[str] = []


class MediaMeta(BaseModel):
    filename: str
    media_type: Literal["image", "video", "audio"]
    size_bytes: int
    duration_sec: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    has_audio: Optional[bool] = None
    sample_rate: Optional[int] = None


class AnalysisResponse(BaseModel):
    analysis_id: str
    created_at: str
    engine: str
    media: MediaMeta
    modalities: list[ModalityResult]
    fusion: FusionResult
    limitations: list[str]
    safety_notice: str
    report_url: str
    processing_ms: int


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    engine: str
    ffmpeg: bool
