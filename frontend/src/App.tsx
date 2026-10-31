import { useEffect, useState } from "react";
import Header from "./components/Header";
import UploadPanel from "./components/UploadPanel";
import Loader from "./components/Loader";
import Results from "./components/Results";
import { analyze, getConfig, type ConfigInfo } from "./api";
import type { AnalysisResponse } from "./types";

const DEFAULT_ACCEPT = [
  ".jpg", ".jpeg", ".png", ".webp", ".bmp",
  ".mp4", ".mov", ".avi", ".mkv", ".webm",
  ".wav", ".mp3", ".flac", ".m4a", ".ogg",
];

export default function App() {
  const [cfg, setCfg] = useState<ConfigInfo | null>(null);
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getConfig().then(setCfg).catch(() => setCfg(null));
  }, []);

  const accept = cfg ? [...cfg.image_ext, ...cfg.video_ext, ...cfg.audio_ext] : DEFAULT_ACCEPT;
  const maxMb = cfg?.max_upload_mb ?? 100;

  async function handleAnalyze(file: File) {
    setBusy(true);
    setError(null);
    setData(null);
    try {
      const res = await analyze(file);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-full">
      <Header />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:py-8">
        {!data && !busy && (
          <section className="mb-6 animate-fade-up">
            <h2 className="text-xl font-extrabold text-white sm:text-2xl">
              Verify media across every modality
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-slate-400">
              Upload an image, video or audio clip. The platform runs visual, temporal, audio and
              lip-sync forensics, fuses the evidence with calibrated confidence, and returns an
              explainable report — flagging <em>evidence of potential manipulation</em>, never
              definitive proof.
            </p>
          </section>
        )}

        {!data && (
          <UploadPanel onAnalyze={handleAnalyze} busy={busy} maxMb={maxMb} accept={accept} />
        )}

        {error && (
          <div className="mt-4 animate-fade-up rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-300 ring-1 ring-red-500/30">
            <span className="font-semibold">Analysis error:</span> {error}
          </div>
        )}

        {busy && (
          <div className="mt-5">
            <Loader />
          </div>
        )}

        {data && !busy && (
          <div className="mt-2">
            <Results data={data} onReset={() => setData(null)} />
          </div>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 pt-4 text-center text-[11px] text-slate-500">
        Multimodal Deepfake Detection &amp; Media Forensics Platform · Investigative assistance only,
        not a definitive authentication service.
      </footer>
    </div>
  );
}
