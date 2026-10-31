import { useCallback, useRef, useState } from "react";
import { bytes } from "../lib/format";

interface Props {
  onAnalyze: (file: File) => void;
  busy: boolean;
  maxMb: number;
  accept: string[];
}

export default function UploadPanel({ onAnalyze, busy, maxMb, accept }: Props) {
  const [drag, setDrag] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const accentExts = accept.map((e) => e.replace(".", "")).join(", ");

  const validate = useCallback(
    (f: File): string | null => {
      const ext = "." + (f.name.split(".").pop() || "").toLowerCase();
      if (!accept.includes(ext)) return `Unsupported type "${ext}". Allowed: ${accentExts}.`;
      if (f.size > maxMb * 1024 * 1024) return `File is ${bytes(f.size)}; limit is ${maxMb} MB.`;
      if (f.size === 0) return "File is empty.";
      return null;
    },
    [accept, accentExts, maxMb]
  );

  const pick = useCallback(
    (f: File | null | undefined) => {
      if (!f) return;
      const e = validate(f);
      setErr(e);
      setFile(e ? null : f);
    },
    [validate]
  );

  return (
    <div className="animate-fade-up">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          pick(e.dataTransfer.files?.[0]);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        className={`card flex cursor-pointer flex-col items-center justify-center gap-3 px-6 py-12 text-center transition
          ${drag ? "ring-2 ring-brand-500/70 bg-brand-500/5" : "hover:border-ink-600"}`}
      >
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-brand-600/15 ring-1 ring-brand-500/30">
          <svg viewBox="0 0 24 24" className="h-7 w-7 text-brand-400" fill="none"
            stroke="currentColor" strokeWidth="1.8">
            <path d="M12 16V4m0 0l-4 4m4-4l4 4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" strokeLinecap="round" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-white">
            Drag &amp; drop media, or <span className="text-brand-400">browse</span>
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Images, video or audio · up to {maxMb} MB
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">{accentExts}</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept={accept.join(",")}
          onChange={(e) => pick(e.target.files?.[0])}
        />
      </div>

      {err && (
        <p className="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-300 ring-1 ring-red-500/30">
          {err}
        </p>
      )}

      {file && (
        <div className="card mt-4 flex items-center justify-between gap-3 px-4 py-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-white">{file.name}</p>
            <p className="text-xs text-slate-400">{bytes(file.size)}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setFile(null);
                setErr(null);
              }}
              disabled={busy}
              className="rounded-lg px-3 py-2 text-xs text-slate-300 ring-1 ring-ink-600 hover:bg-ink-800 disabled:opacity-40"
            >
              Clear
            </button>
            <button
              onClick={() => file && onAnalyze(file)}
              disabled={busy}
              className="rounded-lg bg-brand-600 px-4 py-2 text-xs font-semibold text-ink-950 shadow-lg shadow-brand-600/20 transition hover:bg-brand-500 disabled:opacity-50"
            >
              {busy ? "Analysing…" : "Analyse media"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
