"""Compare single trained models vs. their ensemble (with test-time augmentation)
on a labelled real/fake image folder, in a single inference pass.

Usage:
    cd backend
    python -m evaluation.eval_image_models --data ../scratch_real_eval \
        --models dima806/deepfake_vs_real_image_detection:0 Wvolf/ViT_Deepfake_Detection:0
"""
from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from evaluation.metrics import summarize  # noqa: E402


def _load(model_id):
    import torch
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    proc = AutoImageProcessor.from_pretrained(model_id)
    model = AutoModelForImageClassification.from_pretrained(model_id)
    model.eval()
    return proc, model, torch


def _p_fake(proc, model, torch, pil, fake_idx, tta):
    def one(img):
        inp = proc(images=img, return_tensors="pt")
        with torch.no_grad():
            return float(torch.softmax(model(**inp).logits, dim=-1)[0][fake_idx])
    from PIL import Image
    p = one(pil)
    if tta:
        p = 0.5 * (p + one(pil.transpose(Image.FLIP_LEFT_RIGHT)))
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--models", nargs="+", required=True, help="id:fake_index …")
    ap.add_argument("--tta", action="store_true", default=True)
    ap.add_argument("--no-tta", dest="tta", action="store_false")
    args = ap.parse_args(argv)

    import cv2
    from PIL import Image

    files = ([(p, 0) for p in sorted(glob.glob(str(args.data / "real" / "*")))]
             + [(p, 1) for p in sorted(glob.glob(str(args.data / "fake" / "*")))])
    y = np.array([lab for _, lab in files])

    specs = [(m.rsplit(":", 1)[0], int(m.rsplit(":", 1)[1]) if ":" in m else 0)
             for m in args.models]
    loaded = [(mid, fi, *_load(mid)) for mid, fi in specs]

    t0 = time.time()
    per_model = {mid: [] for mid, _, *_ in loaded}
    for i, (path, _) in enumerate(files, 1):
        bgr = cv2.imread(path)
        pil = Image.fromarray(bgr[:, :, ::-1])
        for mid, fi, proc, model, torch in loaded:
            per_model[mid].append(_p_fake(proc, model, torch, pil, fi, args.tta))
        if i % 50 == 0:
            print(f"  scored {i}/{len(files)}  ({time.time()-t0:.0f}s)", flush=True)

    scores = {mid: np.array(v) for mid, v in per_model.items()}
    ens = np.mean(np.stack(list(scores.values())), axis=0)

    def row(name, s):
        m = summarize(y, s)
        return (f"| {name:46s} | {m.auc:.3f} | {m.eer:.3f} | {m.accuracy:.3f} | "
                f"{m.f1:.3f} | {m.brier:.3f} | {m.ece:.3f} |")

    print("\n| Detector | AUC | EER | Acc | F1 | Brier | ECE |")
    print("|---|---|---|---|---|---|---|")
    for mid in scores:
        print(row(mid.split("/")[-1] + (" +TTA" if args.tta else ""), scores[mid]))
    print(row(f"ENSEMBLE({len(scores)}){' +TTA' if args.tta else ''}", ens))
    print(f"\nScored {len(files)} images, {len(loaded)} models, "
          f"tta={args.tta}, {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
