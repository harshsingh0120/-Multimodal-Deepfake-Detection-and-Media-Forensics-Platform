import { useState } from "react";
import type { ModalityResult } from "../types";
import { bandStyleFor, modalityIcon, modalityLabel, pct, prettyKey } from "../lib/format";

export default function ModalityCard({ m }: { m: ModalityResult }) {
  const [showFeatures, setShowFeatures] = useState(false);
  const style = bandStyleFor(m.score);

  if (!m.available) {
    return (
      <div className="card animate-fade-up p-5 opacity-70">
        <div className="flex items-center gap-2">
          <span className="text-lg">{modalityIcon[m.modality]}</span>
          <h3 className="text-sm font-semibold text-slate-300">{modalityLabel[m.modality]}</h3>
          <span className="ml-auto rounded-full bg-ink-800 px-2 py-0.5 text-[10px] text-slate-400 ring-1 ring-ink-600">
            not evaluated
          </span>
        </div>
        <p className="mt-2 text-xs text-slate-400">{m.summary}</p>
      </div>
    );
  }

  const features = Object.entries(m.features);

  return (
    <div className="card animate-fade-up flex flex-col p-5">
      <div className="flex items-center gap-2">
        <span className="text-lg">{modalityIcon[m.modality]}</span>
        <h3 className="text-sm font-semibold text-white">{modalityLabel[m.modality]}</h3>
        <span className={`ml-auto rounded-full px-2.5 py-0.5 text-xs font-bold ${style.bg} ${style.text}`}>
          {pct(m.score)}
        </span>
      </div>

      {/* score bar */}
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-ink-700">
        <div className={`h-full rounded-full ${style.bar} transition-all duration-700`}
          style={{ width: pct(m.score) }} />
      </div>
      <div className="mt-1 flex justify-between text-[11px] text-slate-400">
        <span>{style.label} evidence</span>
        <span>confidence {pct(m.confidence)}</span>
      </div>

      <p className="mt-3 text-xs leading-relaxed text-slate-300">{m.summary}</p>

      {/* evidence */}
      {m.evidence.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Key indicators
          </p>
          {m.evidence.map((e, i) => (
            <div key={i} className="group">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-xs font-medium text-slate-200" title={e.name}>
                  {e.name}
                </span>
                <span className="shrink-0 font-mono text-[11px] text-slate-400">
                  {pct(e.contribution)}
                </span>
              </div>
              <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-ink-700">
                <div className={`h-full ${bandStyleFor(e.contribution).bar}`}
                  style={{ width: pct(e.contribution) }} />
              </div>
              <p className="mt-1 text-[11px] leading-snug text-slate-400">{e.detail}</p>
            </div>
          ))}
        </div>
      )}

      {/* heatmaps */}
      {m.heatmaps.length > 0 && (
        <div className="mt-4 space-y-3">
          {m.heatmaps.map((h, i) => (
            <figure key={i} className="overflow-hidden rounded-xl ring-1 ring-ink-700">
              <img src={h.image} alt={h.title} className="w-full bg-ink-950 object-contain" />
              <figcaption className="bg-ink-800/80 px-3 py-2 text-[11px] text-slate-300">
                <span className="font-semibold text-white">{h.title}.</span> {h.description}
              </figcaption>
            </figure>
          ))}
        </div>
      )}

      {/* flagged frames */}
      {m.flagged_frames.length > 0 && (
        <div className="mt-4">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Suspicious frames
          </p>
          <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
            {m.flagged_frames.map((fr, i) => (
              <div key={i} className="shrink-0 text-center">
                {fr.thumbnail ? (
                  <img src={fr.thumbnail} alt={`frame ${fr.timestamp_sec}s`}
                    className="h-16 w-16 rounded-lg object-cover ring-1 ring-red-500/40" />
                ) : (
                  <div className="grid h-16 w-16 place-items-center rounded-lg bg-ink-800 text-xs">
                    {fr.timestamp_sec}s
                  </div>
                )}
                <span className="mt-1 block text-[10px] text-slate-400">
                  {fr.timestamp_sec}s · {pct(fr.score)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* flagged segments */}
      {m.flagged_segments.length > 0 && (
        <div className="mt-4">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Suspicious audio segments
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {m.flagged_segments.map((s, i) => (
              <span key={i}
                className="rounded-md bg-red-500/10 px-2 py-1 text-[11px] text-red-300 ring-1 ring-red-500/30">
                {s.start_sec}–{s.end_sec}s · {pct(s.score)}
              </span>
            ))}
          </div>
        </div>
      )}

      {m.notes.length > 0 && (
        <div className="mt-3 space-y-1">
          {m.notes.map((n, i) => (
            <p key={i} className="text-[11px] italic text-amber-300/80">⚠ {n}</p>
          ))}
        </div>
      )}

      {/* feature table */}
      {features.length > 0 && (
        <div className="mt-4 border-t border-ink-700 pt-3">
          <button
            onClick={() => setShowFeatures((v) => !v)}
            className="flex w-full items-center justify-between text-[11px] font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-200"
          >
            <span>Raw forensic features ({features.length})</span>
            <span>{showFeatures ? "▲" : "▼"}</span>
          </button>
          {showFeatures && (
            <div className="mt-2 grid grid-cols-1 gap-x-4 gap-y-1 sm:grid-cols-2">
              {features.map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-2 text-[11px]">
                  <span className="truncate text-slate-400" title={prettyKey(k)}>{prettyKey(k)}</span>
                  <span className="shrink-0 font-mono text-slate-200">
                    {Number.isInteger(v) ? v : v.toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
