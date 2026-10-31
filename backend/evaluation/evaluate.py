"""Evaluate the detector on a labelled dataset.

Dataset formats
---------------
1. Folder convention (default):  <data_dir>/real/**  and  <data_dir>/fake/**
   (any media files; labels taken from the sub-folder name).
2. CSV manifest (--manifest):     columns `path,label`  where label ∈ {real,fake,0,1}.

What it reports
---------------
For the fused detector AND the baselines named in the problem statement
("single-modality models, simple averaging fusion") it computes:
ROC-AUC, EER, best-threshold accuracy / precision / recall / F1, Brier, and ECE.

Usage
-----
    cd backend
    python -m evaluation.evaluate --data path/to/dataset
    python -m evaluation.evaluate --manifest labels.csv --limit 200
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Make `app` importable whether run as a module or a script.
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.pipeline import analyze_path  # noqa: E402
from app.utils.media import detect_media_type  # noqa: E402
from evaluation.metrics import summarize  # noqa: E402

_LABEL_MAP = {"real": 0, "authentic": 0, "genuine": 0, "0": 0,
              "fake": 1, "manipulated": 1, "deepfake": 1, "spoof": 1, "1": 1}
_MODALITIES = ["image", "video", "audio", "sync"]


def _is_media(p: Path) -> bool:
    try:
        detect_media_type(p)
        return True
    except Exception:
        return False


def discover(data_dir: Path | None, manifest: Path | None) -> list[tuple[Path, int]]:
    items: list[tuple[Path, int]] = []
    if manifest:
        with open(manifest, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                label = _LABEL_MAP.get(str(row.get("label", "")).strip().lower())
                p = Path(row["path"])
                if not p.is_absolute():
                    p = manifest.parent / p
                if label is not None and p.exists() and _is_media(p):
                    items.append((p, label))
        return items

    assert data_dir is not None
    seen: set[str] = set()
    for label_name, label in (("real", 0), ("fake", 1)):
        for sub in (data_dir / label_name, data_dir / label_name.capitalize()):
            if sub.is_dir():
                for p in sub.rglob("*"):
                    key = str(p.resolve()).lower()  # Windows FS is case-insensitive
                    if p.is_file() and _is_media(p) and key not in seen:
                        seen.add(key)
                        items.append((p, label))
    return items


def run(items: list[tuple[Path, int]], limit: int | None = None) -> dict:
    if limit:
        items = items[:limit]
    rows = []
    skipped = []
    t0 = time.perf_counter()
    for i, (path, label) in enumerate(items, 1):
        try:
            res = analyze_path(path, path.name, path.stat().st_size)
        except Exception as e:
            skipped.append({"path": str(path), "error": str(e)})
            continue
        mod_scores = {m["modality"]: m["score"] for m in res["modalities"] if m["available"]}
        avg = float(np.mean(list(mod_scores.values()))) if mod_scores else 0.0
        rows.append({
            "path": str(path), "label": label,
            "overall": res["fusion"]["overall_score"],
            "averaging_baseline": avg,
            **{f"mod_{m}": mod_scores.get(m) for m in _MODALITIES},
        })
        print(f"  [{i}/{len(items)}] {path.name:28s} label={label} "
              f"overall={res['fusion']['overall_score']:.3f}", flush=True)
    elapsed = time.perf_counter() - t0
    return {"rows": rows, "skipped": skipped, "elapsed_sec": elapsed}


def _metrics_for(rows, key) -> dict | None:
    pairs = [(r["label"], r[key]) for r in rows if r.get(key) is not None]
    if len(pairs) < 2:
        return None
    y = np.array([p[0] for p in pairs])
    s = np.array([p[1] for p in pairs])
    if y.sum() == 0 or (1 - y).sum() == 0:
        return None
    m = summarize(y, s)
    return m.__dict__


def evaluate(rows) -> dict:
    report = {}
    report["fusion"] = _metrics_for(rows, "overall")
    report["averaging_baseline"] = _metrics_for(rows, "averaging_baseline")
    for m in _MODALITIES:
        r = _metrics_for(rows, f"mod_{m}")
        if r:
            report[f"single_{m}"] = r
    return report


def _fmt(v, p=3):
    return "n/a" if v is None else (f"{v:.{p}f}" if isinstance(v, float) else str(v))


def render_markdown(report: dict, meta: dict) -> str:
    lines = ["# Evaluation Report", "",
             f"- Dataset: `{meta['source']}`",
             f"- Samples scored: **{meta['n']}** ({meta['n_pos']} fake / {meta['n_neg']} real), "
             f"skipped: {meta['skipped']}",
             f"- Engine: `{meta['engine']}`",
             f"- Generated: {meta['generated']}  ·  runtime: {meta['elapsed_sec']:.1f}s", "",
             "| Detector | AUC ↑ | EER ↓ | Accuracy ↑ | Precision | Recall | F1 | Brier ↓ | ECE ↓ |",
             "|----------|------:|------:|-----------:|----------:|-------:|---:|--------:|------:|"]
    order = ["fusion", "averaging_baseline", "single_image", "single_video",
             "single_audio", "single_sync"]
    nice = {"fusion": "**Multimodal fusion**", "averaging_baseline": "Averaging baseline",
            "single_image": "Single · image", "single_video": "Single · video",
            "single_audio": "Single · audio", "single_sync": "Single · sync"}
    for k in order:
        m = report.get(k)
        if not m:
            continue
        lines.append(
            f"| {nice[k]} | {_fmt(m['auc'])} | {_fmt(m['eer'])} | {_fmt(m['accuracy'])} | "
            f"{_fmt(m['precision'])} | {_fmt(m['recall'])} | {_fmt(m['f1'])} | "
            f"{_fmt(m['brier'])} | {_fmt(m['ece'])} |")
    lines += ["", "_AUC/accuracy higher is better; EER/Brier/ECE lower is better. "
              "Fusion should match or beat the single-modality and simple-averaging baselines._"]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evaluate the deepfake detector on a labelled dataset.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--data", type=Path, help="Dataset dir with real/ and fake/ subfolders")
    g.add_argument("--manifest", type=Path, help="CSV manifest with columns path,label")
    ap.add_argument("--limit", type=int, default=None, help="Score at most N files")
    ap.add_argument("--out", type=Path, default=_BACKEND / "evaluation" / "results",
                    help="Output directory")
    args = ap.parse_args(argv)

    # Ensure the markdown table's ↑/↓ glyphs print on Windows consoles (cp1252).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    items = discover(args.data, args.manifest)
    if not items:
        print("No labelled media found. Expected <data>/real and <data>/fake, "
              "or a CSV manifest with path,label.", file=sys.stderr)
        return 2
    print(f"Discovered {len(items)} labelled files. Scoring"
          + (f" (limit {args.limit})" if args.limit else "") + " …")

    run_res = run(items, args.limit)
    rows = run_res["rows"]
    if not rows:
        print("No files could be scored.", file=sys.stderr)
        return 3

    report = evaluate(rows)
    n_pos = sum(r["label"] for r in rows)
    meta = {
        "source": str(args.data or args.manifest),
        "n": len(rows), "n_pos": n_pos, "n_neg": len(rows) - n_pos,
        "skipped": len(run_res["skipped"]),
        "engine": "interpretable-forensic-engine v1.0",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "elapsed_sec": run_res["elapsed_sec"],
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.out / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps({"meta": meta, "metrics": report, "rows": rows,
                    "skipped": run_res["skipped"]}, indent=2), encoding="utf-8")
    md = render_markdown(report, meta)
    (out_dir / "report.md").write_text(md, encoding="utf-8")

    print("\n" + md)
    print(f"\nSaved: {out_dir / 'report.md'}  and  report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
