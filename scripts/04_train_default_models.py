"""Step 4: train all three architectures with spec-default hyperparameters, 5 seeds each.

Usage: python scripts/04_train_default_models.py --freq daily   (or 15min)

Writes:
  reports/experiments.jsonl                one line per run (FR-M5)
  reports/04_default_{freq}.json/.md       mean +/- std comparison incl. simple baselines
  models/default_{freq}/{arch}_seed{s}.pt  best-epoch weights
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")  # Windows console default is cp1252

from regime.config import ROOT, load_config
from regime.dataset import load_windows
from regime.models import ARCHITECTURES, build_model, count_params
from regime.train import classification_metrics, predict_proba, train_model


def baselines(data, classes) -> dict:
    X_tr, y_tr = data.subset("train")
    X_val, y_val = data.subset("val")
    majority = np.bincount(y_tr).argmax()
    # Logistic regression on the last bar's features only: does the sequence model add anything?
    lr = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X_tr[:, -1], y_tr)
    # Persistence uses the HMM label of bar t, which the classifiers never see -> reference only.
    val_mask = data.split == "val"
    prev_label = np.concatenate([[data.y[0]], data.y[:-1]])[val_mask]
    return {
        "majority_class": classification_metrics(y_val, np.full_like(y_val, majority), classes),
        "logistic_regression_last_bar": classification_metrics(y_val, lr.predict(X_val[:, -1]), classes),
        "persistence_reference": classification_metrics(y_val, prev_label, classes),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freq", choices=["daily", "15min"], default="daily")
    ap.add_argument("--archs", nargs="+", default=list(ARCHITECTURES))
    args = ap.parse_args()

    cfg = load_config()
    tcfg, classes = cfg["training"], cfg["sequence"]["classes"]
    data = load_windows(ROOT / cfg["data"]["processed_dir"], args.freq, cfg)
    X_tr, y_tr = data.subset("train")
    X_val, y_val = data.subset("val")
    n_features = X_tr.shape[2]
    print(f"{args.freq}: X_train {X_tr.shape}, X_val {X_val.shape}")
    print("train class counts", dict(zip(classes, np.bincount(y_tr, minlength=4).tolist())),
          "| val", dict(zip(classes, np.bincount(y_val, minlength=4).tolist())))

    model_dir = ROOT / "models" / f"default_{args.freq}"
    model_dir.mkdir(parents=True, exist_ok=True)
    log_path = ROOT / "reports" / "experiments.jsonl"
    summary = {"freq": args.freq, "n_train": len(y_tr), "n_val": len(y_val), "baselines": baselines(data, classes), "models": {}}

    for arch in args.archs:
        hp = cfg["models"][arch]
        runs = []
        for s in range(tcfg["n_seeds"]):
            seed = cfg["seed"] + s
            torch.manual_seed(seed)   # weight init
            model = build_model(arch, n_features, len(classes), hp)
            fit = train_model(model, X_tr, y_tr, X_val, y_val, tcfg, len(classes), seed)
            metrics = classification_metrics(y_val, predict_proba(model, X_val).argmax(axis=1), classes)
            torch.save(model.state_dict(), model_dir / f"{arch}_seed{seed}.pt")
            run = {"time": datetime.now().isoformat(timespec="seconds"), "step": "04_default", "freq": args.freq,
                   "arch": arch, "seed": seed, "hyperparameters": hp, "training": tcfg,
                   "n_params": count_params(model), "split": "val", "val_metrics": metrics,
                   **{k: v for k, v in fit.items() if k != "history"}, "history": fit["history"]}
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(run) + "\n")
            runs.append(run)
            print(f"  {arch:16s} seed {seed}: acc {metrics['accuracy']:.3f}  macroF1 {metrics['macro_f1']:.3f}  "
                  f"best epoch {fit['best_epoch']:3d}/{fit['epochs_run']:3d}  {fit['train_seconds']}s")

        acc = [r["val_metrics"]["accuracy"] for r in runs]
        f1 = [r["val_metrics"]["macro_f1"] for r in runs]
        per_class = {c: float(np.mean([r["val_metrics"]["per_class"][c]["f1"] for r in runs])) for c in classes}
        best = int(np.argmax(f1))
        summary["models"][arch] = {
            "n_params": runs[0]["n_params"],
            "accuracy_mean": float(np.mean(acc)), "accuracy_std": float(np.std(acc)),
            "macro_f1_mean": float(np.mean(f1)), "macro_f1_std": float(np.std(f1)),
            "per_class_f1_mean": per_class,
            "confusion_matrix_best_seed": runs[best]["val_metrics"]["confusion_matrix"],
            "best_seed": runs[best]["seed"],
            "mean_train_seconds": float(np.mean([r["train_seconds"] for r in runs])),
        }

    out = ROOT / "reports" / f"04_default_{args.freq}.json"
    out.write_text(json.dumps(summary, indent=2))

    lines = [f"# Step 4 — default hyperparameters, {args.freq} (validation split, {len(y_val)} samples)", "",
             "| Model | Params | Accuracy | Macro-F1 | " + " | ".join(f"F1 {c}" for c in classes) + " |",
             "|---|---|---|---|" + "---|" * len(classes)]
    for arch, m in summary["models"].items():
        lines.append(f"| {arch} | {m['n_params']:,} | {m['accuracy_mean']:.3f} ± {m['accuracy_std']:.3f} | "
                     f"{m['macro_f1_mean']:.3f} ± {m['macro_f1_std']:.3f} | "
                     + " | ".join(f"{m['per_class_f1_mean'][c]:.2f}" for c in classes) + " |")
    for name, m in summary["baselines"].items():
        lines.append(f"| *{name}* | – | {m['accuracy']:.3f} | {m['macro_f1']:.3f} | "
                     + " | ".join(f"{m['per_class'][c]['f1']:.2f}" for c in classes) + " |")
    lines += ["", f"Mean ± std over {tcfg['n_seeds']} seeds. Confusion matrices (rows = true, cols = predicted, "
              f"order {classes}) for the best seed are in `04_default_{args.freq}.json`.",
              "*persistence_reference* uses the HMM label at t, which the models never see — it is an "
              "upper reference for how sticky the labels are, not a competitor."]
    (ROOT / "reports" / f"04_default_{args.freq}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
