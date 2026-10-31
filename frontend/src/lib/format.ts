import type { ModalityName } from "../types";

export const pct = (v: number): string => `${Math.round(v * 100)}%`;

export function bytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

/** Color system keyed by verdict band / score level. */
export interface BandStyle {
  text: string;
  bg: string;
  ring: string;
  bar: string;
  hex: string;
  label: string;
}

export function bandStyleFor(score: number): BandStyle {
  if (score < 0.25)
    return { label: "Low", text: "text-emerald-300", bg: "bg-emerald-500/10",
      ring: "ring-emerald-500/40", bar: "bg-emerald-400", hex: "#34d399" };
  if (score < 0.45)
    return { label: "Guarded", text: "text-amber-300", bg: "bg-amber-500/10",
      ring: "ring-amber-500/40", bar: "bg-amber-400", hex: "#fbbf24" };
  if (score < 0.65)
    return { label: "Elevated", text: "text-orange-300", bg: "bg-orange-500/10",
      ring: "ring-orange-500/40", bar: "bg-orange-400", hex: "#fb923c" };
  if (score < 0.82)
    return { label: "High", text: "text-red-300", bg: "bg-red-500/10",
      ring: "ring-red-500/40", bar: "bg-red-400", hex: "#f87171" };
  return { label: "Very High", text: "text-rose-300", bg: "bg-rose-500/10",
    ring: "ring-rose-500/40", bar: "bg-rose-500", hex: "#fb7185" };
}

export const modalityIcon: Record<ModalityName, string> = {
  image: "🖼️",
  video: "🎞️",
  audio: "🔊",
  sync: "👄",
};

export const modalityLabel: Record<ModalityName, string> = {
  image: "Image / Visual",
  video: "Video / Temporal",
  audio: "Audio / Voice",
  sync: "Lip-Sync",
};

/** Human-friendly feature key. */
export function prettyKey(k: string): string {
  return k
    .replace(/_/g, " ")
    .replace(/\bfft\b/i, "FFT")
    .replace(/\bela\b/i, "ELA")
    .replace(/\bmfcc\b/i, "MFCC")
    .replace(/\brms\b/i, "RMS")
    .replace(/\bcv\b/i, "CV")
    .replace(/\bsec\b/i, "(s)")
    .replace(/\bdb\b/i, "dB");
}
