import type { AnalysisResponse } from "../types";
import { bandStyleFor, bytes, pct } from "../lib/format";
import { reportUrl } from "../api";
import ScoreMeter from "./ScoreMeter";

export default function VerdictBanner({ data }: { data: AnalysisResponse }) {
  const f = data.fusion;
  const style = bandStyleFor(f.overall_score);
  const m = data.media;

  return (
    <section className={`card animate-fade-up overflow-hidden ring-1 ${style.ring}`}>
      <div className="grid gap-6 p-5 sm:p-6 md:grid-cols-[auto,1fr]">
        <div className="flex items-center justify-center">
          <ScoreMeter score={f.overall_score} />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${style.bg} ${style.text} ring-1 ${style.ring}`}>
              {f.verdict_band} · evidence of potential manipulation
            </span>
            <span className="rounded-full bg-ink-800 px-3 py-1 text-xs text-slate-300 ring-1 ring-ink-600">
              confidence {pct(f.calibrated_confidence)}
            </span>
            {f.cross_modal_consistency != null && (
              <span className="rounded-full bg-ink-800 px-3 py-1 text-xs text-slate-300 ring-1 ring-ink-600">
                cross-modal consistency {pct(f.cross_modal_consistency)}
              </span>
            )}
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-200">{f.verdict_text}</p>
          <p className="mt-2 text-xs italic leading-relaxed text-slate-400">{data.safety_notice}</p>

          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-slate-400">
            <span>📄 {m.filename}</span>
            <span>· {m.media_type}</span>
            <span>· {bytes(m.size_bytes)}</span>
            {m.duration_sec ? <span>· {m.duration_sec.toFixed(1)}s</span> : null}
            {m.width ? <span>· {m.width}×{m.height}</span> : null}
            <span>· {data.processing_ms} ms</span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <a
              href={reportUrl(data.report_url)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-xs font-semibold text-ink-950 shadow-lg shadow-brand-600/20 transition hover:bg-brand-500"
            >
              ⬇ Download PDF report
            </a>
            <span className="inline-flex items-center rounded-lg bg-ink-800 px-3 py-2 font-mono text-[11px] text-slate-400 ring-1 ring-ink-600">
              {data.engine}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
