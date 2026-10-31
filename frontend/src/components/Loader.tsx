import { useEffect, useState } from "react";

const STAGES = [
  "Demuxing media & extracting frames/audio…",
  "Running visual forensics (ELA, FFT, noise residual)…",
  "Analysing audio for synthetic-speech cues…",
  "Checking temporal consistency & lip-sync…",
  "Fusing modalities & calibrating confidence…",
  "Generating forensic report…",
];

export default function Loader() {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 1200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="card animate-fade-up px-6 py-10">
      <div className="mx-auto flex max-w-md flex-col items-center gap-5">
        <div className="relative h-16 w-16">
          <div className="absolute inset-0 rounded-full border-4 border-ink-700" />
          <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-brand-500" />
        </div>
        <div className="w-full space-y-2">
          {STAGES.map((s, i) => (
            <div
              key={i}
              className={`flex items-center gap-2 text-xs transition ${
                i < stage ? "text-emerald-300" : i === stage ? "text-white" : "text-slate-500"
              }`}
            >
              <span className="w-4">
                {i < stage ? "✓" : i === stage ? "▸" : "·"}
              </span>
              <span>{s}</span>
            </div>
          ))}
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-700">
          <div
            className="h-full rounded-full bg-brand-500 transition-all duration-700"
            style={{ width: `${((stage + 1) / STAGES.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
