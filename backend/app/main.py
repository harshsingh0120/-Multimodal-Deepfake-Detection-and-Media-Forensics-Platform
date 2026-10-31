"""FastAPI application exposing the forensic analysis pipeline."""
from __future__ import annotations

import shutil
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .analyzers.model_plugin import active_engine_name
from .pipeline import analyze_path
from .report.pdf_report import build_pdf
from .utils.media import MediaError, detect_media_type

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="Multimodal deepfake detection & media forensics — image, video, audio, "
                "lip-sync, fusion, calibrated confidence and downloadable forensic reports.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory result cache (transient; not a durable store). Maps id -> (ts, result, pdf_bytes).
_RESULTS: dict[str, tuple[float, dict, bytes]] = {}


def _prune_cache() -> None:
    now = time.time()
    stale = [k for k, (ts, _, _) in _RESULTS.items()
             if now - ts > settings.RESULT_TTL_SECONDS]
    for k in stale:
        _RESULTS.pop(k, None)


@app.get("/api/health")
def health():
    try:
        settings.ffmpeg_exe()
        ffmpeg_ok = True
    except Exception:
        ffmpeg_ok = False
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "engine": active_engine_name(),
        "ffmpeg": ffmpeg_ok,
    }


@app.get("/api/config")
def config():
    return {
        "max_upload_mb": settings.MAX_UPLOAD_MB,
        "image_ext": sorted(settings.ALLOWED_IMAGE_EXT),
        "video_ext": sorted(settings.ALLOWED_VIDEO_EXT),
        "audio_ext": sorted(settings.ALLOWED_AUDIO_EXT),
        "engine": active_engine_name(),
    }


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    _prune_cache()
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()

    # Validate extension early (clear error before touching disk).
    try:
        detect_media_type(Path(filename))
    except MediaError as e:
        raise HTTPException(status_code=415, detail=str(e))

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    tmp_dir = Path(tempfile.mkdtemp(prefix="dfx_"))
    tmp_path = tmp_dir / f"input{suffix}"
    size = 0
    try:
        with open(tmp_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {settings.MAX_UPLOAD_MB} MB limit.")
                out.write(chunk)

        if size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        try:
            result = analyze_path(tmp_path, filename, size)
        except MediaError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

        analysis_id = uuid.uuid4().hex[:12]
        result["analysis_id"] = analysis_id
        result["report_url"] = f"/api/report/{analysis_id}"
        try:
            pdf_bytes = build_pdf(result, analysis_id)
        except Exception:
            pdf_bytes = b""
        _RESULTS[analysis_id] = (time.time(), result, pdf_bytes)
        return JSONResponse(result)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.get("/api/report/{analysis_id}")
def report(analysis_id: str):
    entry = _RESULTS.get(analysis_id)
    if entry is None:
        raise HTTPException(status_code=404,
                            detail="Report not found or expired. Re-run the analysis.")
    _, result, pdf_bytes = entry
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Report could not be generated.")
    out = settings.DATA_DIR / f"report_{analysis_id}.pdf"
    out.write_bytes(pdf_bytes)
    fname = f"forensic_report_{analysis_id}.pdf"
    return FileResponse(str(out), media_type="application/pdf", filename=fname)


@app.get("/api/result/{analysis_id}")
def get_result(analysis_id: str):
    entry = _RESULTS.get(analysis_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    return JSONResponse(entry[1])


# --- Optionally serve the built frontend (single-command demo) --------------- #
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "docs": "/docs",
            "health": "/api/health",
            "note": "Frontend build not found; run the React dev server (see README).",
        }
