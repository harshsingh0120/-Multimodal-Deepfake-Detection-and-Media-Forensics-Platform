import type { AnalysisResponse } from "../types";
import VerdictBanner from "./VerdictBanner";
import ModalityCard from "./ModalityCard";

export default function Results({ data, onReset }: { data: AnalysisResponse; onReset: () => void }) {
  const order = { image: 0, video: 1, audio: 2, sync: 3 } as const;
  const mods = [...data.modalities].sort((a, b) => order[a.modality] - order[b.modality]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Forensic assessment
        </h2>
        <button
          onClick={onReset}
          className="rounded-lg px-3 py-1.5 text-xs text-slate-300 ring-1 ring-ink-600 hover:bg-ink-800"
        >
          ↺ Analyse another file
        </button>
      </div>

      <VerdictBanner data={data} />

      <div className="grid gap-4 md:grid-cols-2">
        {mods.map((m) => (
          <ModalityCard key={m.modality} m={m} />
        ))}
      </div>

      {/* Fusion rationale */}
      <section className="card animate-fade-up p-5">
        <h3 className="text-sm font-semibold text-white">Fusion &amp; calibration rationale</h3>
        <ul className="mt-3 space-y-1.5">
          {data.fusion.rationale.map((r, i) => (
            <li key={i} className="flex gap-2 text-xs text-slate-300">
              <span className="text-brand-400">▸</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
        {Object.keys(data.fusion.weights).length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(data.fusion.weights).map(([k, v]) => (
              <span key={k} className="rounded-md bg-ink-800 px-2.5 py-1 font-mono text-[11px] text-slate-300 ring-1 ring-ink-600">
                {k}: {(v * 100).toFixed(0)}%
              </span>
            ))}
          </div>
        )}
      </section>

      {/* Limitations */}
      <section className="card animate-fade-up p-5">
        <h3 className="text-sm font-semibold text-white">Limitations &amp; failure cases</h3>
        <ul className="mt-3 space-y-1.5">
          {data.limitations.map((l, i) => (
            <li key={i} className="flex gap-2 text-xs text-slate-400">
              <span className="text-amber-400">•</span>
              <span>{l}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
