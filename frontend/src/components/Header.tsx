import { useEffect, useState } from "react";
import { getHealth, type HealthInfo } from "../api";

export default function Header() {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [down, setDown] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setDown(true));
  }, []);

  return (
    <header className="sticky top-0 z-20 border-b border-ink-700/60 bg-ink-950/70 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-600/20 ring-1 ring-brand-500/40">
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none">
              <path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5l8-3z" fill="#14b8a6" />
              <path d="M8.5 12l2.2 2.2L15.5 9.5" stroke="#0b0f1a" strokeWidth="1.8"
                strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="leading-tight">
            <h1 className="text-base font-extrabold text-white sm:text-lg">
              Deepfake Detection <span className="text-brand-400">&amp; Media Forensics</span>
            </h1>
            <p className="text-[11px] text-slate-400">
              Multimodal · image · video · audio · lip-sync · calibrated fusion
            </p>
          </div>
        </div>
        <div className="hidden items-center gap-2 text-xs sm:flex">
          <StatusDot ok={!down && !!health} />
          <span className="text-slate-400">
            {down
              ? "API offline"
              : health
                ? `API online · ${health.ffmpeg ? "ffmpeg ✓" : "ffmpeg ✗"}`
                : "connecting…"}
          </span>
        </div>
      </div>
    </header>
  );
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      {ok && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/60" />
      )}
      <span
        className={`relative inline-flex h-2.5 w-2.5 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`}
      />
    </span>
  );
}
