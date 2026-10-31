import type { AnalysisResponse } from "./types";

// In dev the Vite proxy forwards /api → backend, so a relative base works everywhere.
// Override with VITE_API_BASE to point at a remote backend.
const BASE = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") || "";

export interface HealthInfo {
  status: string;
  app: string;
  version: string;
  engine: string;
  ffmpeg: boolean;
}

export interface ConfigInfo {
  max_upload_mb: number;
  image_ext: string[];
  video_ext: string[];
  audio_ext: string[];
  engine: string;
}

async function asError(res: Response): Promise<never> {
  let detail = `${res.status} ${res.statusText}`;
  try {
    const body = await res.json();
    if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    /* ignore non-JSON */
  }
  throw new Error(detail);
}

export async function getHealth(): Promise<HealthInfo> {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) return asError(res);
  return res.json();
}

export async function getConfig(): Promise<ConfigInfo> {
  const res = await fetch(`${BASE}/api/config`);
  if (!res.ok) return asError(res);
  return res.json();
}

export async function analyze(file: File, signal?: AbortSignal): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/analyze`, { method: "POST", body: form, signal });
  if (!res.ok) return asError(res);
  return res.json();
}

export function reportUrl(path: string): string {
  return `${BASE}${path}`;
}
