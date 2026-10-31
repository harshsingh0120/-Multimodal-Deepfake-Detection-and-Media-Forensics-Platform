export interface Evidence {
  name: string;
  detail: string;
  contribution: number;
}

export interface FlaggedFrame {
  index: number;
  timestamp_sec: number;
  score: number;
  reason: string;
  thumbnail?: string | null;
}

export interface FlaggedSegment {
  start_sec: number;
  end_sec: number;
  score: number;
  reason: string;
}

export interface HeatmapImage {
  title: string;
  description: string;
  image: string;
}

export type ModalityName = "image" | "video" | "audio" | "sync";

export interface ModalityResult {
  modality: ModalityName;
  available: boolean;
  score: number;
  confidence: number;
  summary: string;
  evidence: Evidence[];
  features: Record<string, number>;
  heatmaps: HeatmapImage[];
  flagged_frames: FlaggedFrame[];
  flagged_segments: FlaggedSegment[];
  notes: string[];
}

export interface FusionResult {
  overall_score: number;
  calibrated_confidence: number;
  verdict_band: string;
  verdict_text: string;
  weights: Record<string, number>;
  cross_modal_consistency: number | null;
  rationale: string[];
}

export interface MediaMeta {
  filename: string;
  media_type: "image" | "video" | "audio";
  size_bytes: number;
  duration_sec?: number | null;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  has_audio?: boolean | null;
  sample_rate?: number | null;
}

export interface AnalysisResponse {
  analysis_id: string;
  created_at: string;
  engine: string;
  media: MediaMeta;
  modalities: ModalityResult[];
  fusion: FusionResult;
  limitations: string[];
  safety_notice: string;
  report_url: string;
  processing_ms: number;
}
