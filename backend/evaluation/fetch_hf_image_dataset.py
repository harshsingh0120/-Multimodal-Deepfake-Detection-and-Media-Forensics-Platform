"""Fetch a *balanced* real/fake image subset from a Hugging Face image dataset,
using the datasets-server HTTP API (CDN-backed, no full download), into
<out>/real and <out>/fake so `evaluate.py --data <out>` can score it.

Example:
    python -m evaluation.fetch_hf_image_dataset \
        --dataset djramirezp/face-classification-dataset --per-class 150 --out ./eval_data

Label mapping: the dataset's ClassLabel names are read automatically; any name containing
"real"/"genuine"/"authentic" is treated as real, otherwise fake.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.parse
import urllib.request


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "eval-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def _server(path: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    return _get(f"https://datasets-server.huggingface.co/{path}?{qs}")


def _is_real(name: str) -> bool:
    n = name.lower()
    return any(k in n for k in ("real", "genuine", "authentic", "bonafide", "bona-fide"))


def fetch(dataset: str, per_class: int, out: pathlib.Path, config: str, split: str) -> dict:
    out_real = out / "real"
    out_fake = out / "fake"
    out_real.mkdir(parents=True, exist_ok=True)
    out_fake.mkdir(parents=True, exist_ok=True)

    info = _server("size", {"dataset": dataset, "config": config, "split": split})
    n_rows = info["size"]["splits"][0]["num_rows"]

    feats = _server("rows", {"dataset": dataset, "config": config, "split": split,
                             "offset": 0, "length": 1})["features"]
    label_names = None
    for f in feats:
        t = f.get("type", {})
        if t.get("_type") == "ClassLabel":
            label_names = t.get("names")
    if not label_names:
        raise SystemExit("Dataset has no ClassLabel feature; cannot map real/fake.")
    real_label = next((i for i, nm in enumerate(label_names) if _is_real(nm)), None)

    buckets = {"real": [], "fake": []}
    # Scan from both ends inward (datasets are often label-sorted).
    offsets = []
    step = 100
    lo, hi = 0, max(0, n_rows - step)
    while lo <= hi:
        offsets.append(lo)
        if hi != lo:
            offsets.append(hi)
        lo += step
        hi -= step

    for off in offsets:
        if len(buckets["real"]) >= per_class and len(buckets["fake"]) >= per_class:
            break
        try:
            rows = _server("rows", {"dataset": dataset, "config": config, "split": split,
                                    "offset": off, "length": step})["rows"]
        except Exception:
            continue
        for r in rows:
            row = r["row"]
            lab = row.get("label")
            kind = "real" if lab == real_label else "fake"
            if len(buckets[kind]) >= per_class:
                continue
            img = row.get("image")
            src = img.get("src") if isinstance(img, dict) else None
            if src:
                buckets[kind].append(src)

    def download(kind):
        folder = out / kind
        n = 0
        for i, src in enumerate(buckets[kind]):
            try:
                req = urllib.request.Request(src, headers={"User-Agent": "eval-fetch/1.0"})
                with urllib.request.urlopen(req, timeout=40) as r:
                    (folder / f"{kind}_{i:04d}.jpg").write_bytes(r.read())
                n += 1
            except Exception:
                pass
        return n

    t0 = time.time()
    got = {k: download(k) for k in ("real", "fake")}
    return {"dataset": dataset, "rows": n_rows, "label_names": label_names,
            "downloaded": got, "elapsed_sec": round(time.time() - t0, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--per-class", type=int, default=150)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--config", default="default")
    ap.add_argument("--split", default="train")
    args = ap.parse_args(argv)
    res = fetch(args.dataset, args.per_class, args.out, args.config, args.split)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
