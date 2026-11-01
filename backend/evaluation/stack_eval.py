"""Learned-fusion (stacking) evaluation.

Builds per-image features — two trained ViT P(fake) outputs + the interpretable engine's
image score — then evaluates, with stratified 5-fold cross-validation (out-of-fold
predictions, no leakage across folds), how well a simple logistic-regression combiner does
versus each single signal. Demonstrates whether learned fusion beats the best single model.

Feature extraction is cached to an .npz so the (fast) logistic-regression part can be
re-run without repeating ViT inference.

Usage:
    cd backend
    python -m evaluation.stack_eval --data ../scratch_real_eval --cache ../scratch_features.npz
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

MODELS = [("dima806/deepfake_vs_real_image_detection", 0),
          ("Wvolf/ViT_Deepfake_Detection", 0)]


def extract_features(data: Path, cache: Path):
    if cache.exists():
        d = np.load(cache)
        return d["X"], d["y"], list(d["names"])
    import cv2
    import torch
    from PIL import Image
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    from app.analyzers.image_analyzer import analyze_image_bgr

    files = ([(p, 0) for p in sorted(glob.glob(str(data / "real" / "*")))]
             + [(p, 1) for p in sorted(glob.glob(str(data / "fake" / "*")))])
    y = np.array([lab for _, lab in files])

    loaded = []
    for mid, fi in MODELS:
        proc = AutoImageProcessor.from_pretrained(mid)
        model = AutoModelForImageClassification.from_pretrained(mid)
        model.eval()
        loaded.append((mid, fi, proc, model))

    names = [m.split("/")[-1] for m, _ in MODELS] + ["engine"]
    rows = []
    t0 = time.time()
    for i, (path, _) in enumerate(files, 1):
        bgr = cv2.imread(path)
        pil = Image.fromarray(bgr[:, :, ::-1])
        feats = []
        for _mid, fi, proc, model in loaded:
            inp = proc(images=pil, return_tensors="pt")
            with torch.no_grad():
                feats.append(float(torch.softmax(model(**inp).logits, dim=-1)[0][fi]))
        feats.append(float(analyze_image_bgr(bgr, make_heatmaps=False).score))
        rows.append(feats)
        if i % 50 == 0:
            print(f"  features {i}/{len(files)} ({time.time()-t0:.0f}s)", flush=True)
    X = np.array(rows)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, X=X, y=y, names=np.array(names))
    return X, y, names


def cv_auc(X, y, cols):
    """Average per-fold test metrics (avoids distorting global AUC by concatenating
    out-of-fold probabilities that were scaled independently per fold)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    Xs = X[:, cols]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    aucs, eers, accs, f1s, eces = [], [], [], [], []
    for tr, te in skf.split(Xs, y):
        sc = StandardScaler().fit(Xs[tr])
        clf = LogisticRegression(max_iter=1000).fit(sc.transform(Xs[tr]), y[tr])
        p = clf.predict_proba(sc.transform(Xs[te]))[:, 1]
        m = summarize(y[te], p)
        if m.auc is not None:
            aucs.append(m.auc)
        for lst, v in ((eers, m.eer), (accs, m.accuracy), (f1s, m.f1), (eces, m.ece)):
            if v is not None:
                lst.append(v)
    mean = lambda a: float(np.mean(a)) if a else float("nan")
    return mean(aucs), mean(eers), mean(accs), mean(f1s), mean(eces)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--cache", type=Path, default=Path("../scratch_features.npz"))
    args = ap.parse_args(argv)

    X, y, names = extract_features(args.data, args.cache)
    print(f"\nFeatures: {names}  shape={X.shape}")

    # Raw single-signal AUCs (engine is inverted → also show flipped).
    print("\n--- raw single-signal metrics ---")
    for j, nm in enumerate(names):
        m = summarize(y, X[:, j])
        extra = f"  (flipped AUC={summarize(y, 1-X[:, j]).auc:.3f})" if m.auc < 0.5 else ""
        print(f"  {nm:40s} AUC={m.auc:.3f} acc={m.accuracy:.3f}{extra}")

    print("\n--- 5-fold CV logistic-regression fusion (out-of-fold) ---")
    print("| Combiner | AUC | EER | Acc | F1 | ECE |")
    print("|---|---|---|---|---|---|")
    combos = {
        "LR[dima]": [0],
        "LR[dima+wvolf]": [0, 1],
        "LR[dima+wvolf+engine]": [0, 1, 2],
    }
    for name, cols in combos.items():
        auc, eer, acc, f1, ece = cv_auc(X, y, cols)
        print(f"| {name:40s} | {auc:.3f} | {eer:.3f} | {acc:.3f} | {f1:.3f} | {ece:.3f} |")


if __name__ == "__main__":
    main()
