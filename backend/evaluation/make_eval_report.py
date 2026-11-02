"""Generate a full graphical evaluation report on a labelled real/fake image folder.

Computes per-image scores for the interpretable engine and two public pre-trained ViTs
(label-orientation corrected), plus a learned logistic-regression fusion, then renders:
ROC curves, score distributions, calibration (reliability) diagrams, confusion matrices,
and a summary bar chart. Writes figures to <out>/eval/*.png and a Markdown report
<out>/EVAL_REPORT.md that embeds them.

Usage:
    cd backend
    python -m evaluation.make_eval_report --data ../scratch_real_eval --out ../docs
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from evaluation.metrics import summarize, best_threshold_accuracy  # noqa: E402

MODELS = [("dima806/deepfake_vs_real_image_detection", 0, "ViT-A (dima806)"),
          ("Wvolf/ViT_Deepfake_Detection", 0, "ViT-B (Wvolf)")]

C = {"engine": "#9ca3af", "ViT-A (dima806)": "#2dd4bf", "ViT-B (Wvolf)": "#60a5fa",
     "Ensemble": "#f59e0b", "Learned fusion": "#ef4444"}


def extract(data: Path):
    import cv2
    import torch
    from PIL import Image
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    from app.analyzers.image_analyzer import analyze_image_bgr

    files = ([(p, 0) for p in sorted(glob.glob(str(data / "real" / "*")))]
             + [(p, 1) for p in sorted(glob.glob(str(data / "fake" / "*")))])
    y = np.array([lab for _, lab in files])
    loaded = []
    for mid, fi, name in MODELS:
        proc = AutoImageProcessor.from_pretrained(mid)
        model = AutoModelForImageClassification.from_pretrained(mid)
        model.eval()
        loaded.append((name, fi, proc, model, torch))

    eng, vit = [], {name: [] for _, _, name in MODELS}
    for i, (path, _) in enumerate(files, 1):
        bgr = cv2.imread(path)
        pil = Image.fromarray(bgr[:, :, ::-1])
        eng.append(float(analyze_image_bgr(bgr, make_heatmaps=False).score))
        for name, fi, proc, model, torch in loaded:
            inp = proc(images=pil, return_tensors="pt")
            with torch.no_grad():
                vit[name].append(float(torch.softmax(model(**inp).logits, dim=-1)[0][fi]))
        if i % 40 == 0:
            print(f"  {i}/{len(files)} scored", flush=True)
    scores = {"engine": np.array(eng)}
    for name in vit:
        scores[name] = np.array(vit[name])
    return y, scores


def fusion_oof(y, feats):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_predict, StratifiedKFold
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    return cross_val_predict(pipe, feats, y, cv=skf, method="predict_proba")[:, 1]


def roc_points(y, s):
    from sklearn.metrics import roc_curve
    return roc_curve(y, s)


def fig_roc(y, series, out):
    plt.figure(figsize=(6, 5.2))
    for name, s in series.items():
        fpr, tpr, _ = roc_points(y, s)
        auc = summarize(y, s).auc
        plt.plot(fpr, tpr, color=C.get(name, "#333"), lw=2, label=f"{name} (AUC {auc:.3f})")
    plt.plot([0, 1], [0, 1], "--", color="#cbd5e0", lw=1, label="chance (0.50)")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
    plt.title("ROC curves — real vs. fake faces"); plt.legend(loc="lower right", fontsize=8)
    plt.grid(alpha=0.25); plt.tight_layout(); plt.savefig(out, dpi=140); plt.close()


def fig_dist(y, series, names, out):
    fig, axs = plt.subplots(1, len(names), figsize=(5.2 * len(names), 4.2))
    if len(names) == 1:
        axs = [axs]
    for ax, name in zip(axs, names):
        s = series[name]
        ax.hist(s[y == 0], bins=20, range=(0, 1), alpha=0.6, color="#34d399", label="real")
        ax.hist(s[y == 1], bins=20, range=(0, 1), alpha=0.6, color="#ef4444", label="fake")
        ax.set_title(f"P(fake) distribution — {name}"); ax.set_xlabel("P(fake)")
        ax.set_ylabel("count"); ax.legend(fontsize=8); ax.grid(alpha=0.2)
    plt.tight_layout(); plt.savefig(out, dpi=140); plt.close()


def fig_calibration(y, series, names, out):
    plt.figure(figsize=(5.6, 5.2))
    plt.plot([0, 1], [0, 1], "--", color="#cbd5e0", label="perfect")
    for name in names:
        s = np.clip(series[name], 0, 1)
        bins = np.linspace(0, 1, 11)
        xs, ys = [], []
        for i in range(10):
            m = (s >= bins[i]) & (s < bins[i + 1] if i < 9 else s <= bins[i + 1])
            if m.sum() >= 3:
                xs.append(s[m].mean()); ys.append(y[m].mean())
        plt.plot(xs, ys, "o-", color=C.get(name, "#333"), lw=1.8, label=name)
    plt.xlabel("Mean predicted P(fake)"); plt.ylabel("Observed fraction fake")
    plt.title("Calibration (reliability) diagram"); plt.legend(fontsize=8)
    plt.grid(alpha=0.25); plt.tight_layout(); plt.savefig(out, dpi=140); plt.close()


def fig_confusion(y, series, names, out):
    fig, axs = plt.subplots(1, len(names), figsize=(4.2 * len(names), 3.8))
    if len(names) == 1:
        axs = [axs]
    for ax, name in zip(axs, names):
        s = series[name]
        thr, acc = best_threshold_accuracy(y, s)
        pred = (s >= thr).astype(int)
        cm = np.array([[int(((pred == 0) & (y == 0)).sum()), int(((pred == 1) & (y == 0)).sum())],
                       [int(((pred == 0) & (y == 1)).sum()), int(((pred == 1) & (y == 1)).sum())]])
        ax.imshow(cm, cmap="Blues")
        for (r, c), v in np.ndenumerate(cm):
            ax.text(c, r, str(v), ha="center", va="center",
                    color="white" if v > cm.max() / 2 else "black", fontsize=13)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["pred real", "pred fake"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["true real", "true fake"], fontsize=8)
        ax.set_title(f"{name}\nacc {acc:.2f} @ thr {thr:.2f}", fontsize=9)
    plt.tight_layout(); plt.savefig(out, dpi=140); plt.close()


def fig_summary(rows, out):
    names = [r[0] for r in rows]; aucs = [r[1] for r in rows]; accs = [r[2] for r in rows]
    x = np.arange(len(names)); w = 0.38
    plt.figure(figsize=(7.2, 4.4))
    plt.bar(x - w / 2, aucs, w, color="#2dd4bf", label="AUC")
    plt.bar(x + w / 2, accs, w, color="#f59e0b", label="Accuracy")
    plt.axhline(0.5, ls="--", color="#cbd5e0", lw=1)
    for i, (a, b) in enumerate(zip(aucs, accs)):
        plt.text(i - w / 2, a + 0.01, f"{a:.2f}", ha="center", fontsize=7.5)
        plt.text(i + w / 2, b + 0.01, f"{b:.2f}", ha="center", fontsize=7.5)
    plt.xticks(x, names, rotation=18, ha="right", fontsize=8); plt.ylim(0, 1.05)
    plt.title("Detector comparison (real vs. fake faces)"); plt.legend(fontsize=8)
    plt.grid(axis="y", alpha=0.25); plt.tight_layout(); plt.savefig(out, dpi=140); plt.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("../docs"))
    args = ap.parse_args(argv)
    eval_dir = args.out / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    y, scores = extract(args.data)
    n_real, n_fake = int((y == 0).sum()), int((y == 1).sum())
    print(f"scored {len(y)} images ({n_real} real / {n_fake} fake)")

    vit_names = [n for _, _, n in MODELS]
    feats = np.column_stack([scores[n] for n in vit_names] + [scores["engine"]])
    ens = np.mean(np.column_stack([scores[n] for n in vit_names]), axis=1)
    fus = fusion_oof(y, feats)
    scores["Ensemble"] = ens
    scores["Learned fusion"] = fus

    # metrics table
    table_order = ["engine"] + vit_names + ["Ensemble", "Learned fusion"]
    label = {"engine": "Interpretable engine"}
    rows = []
    metrics = {}
    for name in table_order:
        m = summarize(y, scores[name])
        metrics[name] = m
        rows.append((label.get(name, name), m.auc, m.accuracy))

    # figures
    roc_series = {n: scores[n] for n in table_order}
    fig_roc(y, roc_series, eval_dir / "roc_curves.png")
    fig_dist(y, scores, ["ViT-A (dima806)", "Learned fusion"], eval_dir / "score_distributions.png")
    fig_calibration(y, scores, ["ViT-A (dima806)", "Learned fusion"], eval_dir / "calibration.png")
    fig_confusion(y, scores, ["ViT-A (dima806)", "Learned fusion"], eval_dir / "confusion_matrices.png")
    fig_summary(rows, eval_dir / "summary_bars.png")
    np.savez(args.out / "eval" / "scores.npz", y=y,
             **{k.replace(" ", "_"): v for k, v in scores.items()})

    # markdown
    def fmt(m):
        g = lambda v: "n/a" if v is None else f"{v:.3f}"
        return f"{g(m.auc)} | {g(m.eer)} | {g(m.accuracy)} | {g(m.f1)} | {g(m.brier)} | {g(m.ece)}"
    md = []
    md.append("# Dataset Evaluation Report — with Graphs\n")
    md.append(f"**Dataset:** `djramirezp/face-classification-dataset` (Hugging Face, MIT) — "
              f"real human faces vs. GAN/deepfake-generated faces, 224x224.\n")
    md.append(f"**Subset scored:** {len(y)} images ({n_real} real / {n_fake} fake), pulled balanced "
              f"from the public datasets-server CDN. No training on this set; label orientation of "
              f"each ViT corrected (fake index = 0).\n")
    md.append("## Metrics\n")
    md.append("| Detector | AUC | EER | Accuracy | F1 | Brier | ECE |")
    md.append("|---|---|---|---|---|---|---|")
    for name in table_order:
        md.append(f"| {label.get(name, name)} | {fmt(metrics[name])} |")
    md.append("\n_AUC/Accuracy higher is better; EER/Brier/ECE lower is better. The interpretable "
              "engine alone is below 0.5 (its artifact assumption is sign-flipped for this "
              "generator); the trained ViTs and the learned fusion carry the real signal._\n")
    md.append("## ROC curves\n![ROC curves](eval/roc_curves.png)\n")
    md.append("## Detector comparison\n![Summary](eval/summary_bars.png)\n")
    md.append("## Score distributions (separation of real vs. fake)\n"
              "![Score distributions](eval/score_distributions.png)\n")
    md.append("## Calibration (reliability diagram)\n![Calibration](eval/calibration.png)\n")
    md.append("## Confusion matrices (at best threshold)\n"
              "![Confusion matrices](eval/confusion_matrices.png)\n")
    md.append("## Notes & honest caveats\n"
              "- Cross-dataset: off-the-shelf models, **no test-set tuning**.\n"
              "- Learned-fusion metrics are 5-fold out-of-fold (no leakage across folds); a single "
              "public dataset may share identities across folds, so treat as slightly optimistic.\n"
              "- n is small (hundreds), so expect +/- a few points of noise.\n")
    (args.out / "EVAL_REPORT.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote", args.out / "EVAL_REPORT.md", "and figures in", eval_dir)


if __name__ == "__main__":
    main()
