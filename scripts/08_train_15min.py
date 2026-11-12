"""Step 8: train the selected architecture on 15-minute bars (spec section 5, 48-bar window).

Hyperparameters = the architecture's tuned daily config (reports/06_tuning_daily_{arch}.json);
no separate 15-min tuning (decision: option C). Early stopping on validation macro-F1.
Validation only -- the test period is used in Step 9 (walk-forward replay).

Designed for Colab: each seed is saved as soon as it finishes and skipped on re-run, so a
disconnected runtime resumes where it stopped.

Usage: python scripts/08_train_15min.py [--device auto|cuda|cpu] [--quick]
--quick: small slice, 1 epoch, 1 seed, "_quick" outputs -- a pipeline check only.

Writes models/tuned_15min/{arch}_seed{s}.pt + .json and reports/08_15min_validation.json/.md
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.backtest import evaluate_strategy, target_returns
from regime.config import ROOT, load_config
from regime.dataset import load_windows
from regime.models import build_model, count_params
from regime.train import classification_metrics, predict_proba, train_model

FREQ = "15min"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    device = torch.device("cuda" if args.device == "auto" and torch.cuda.is_available() else
                          ("cpu" if args.device == "auto" else args.device))

    cfg = load_config()
    rep = ROOT / "reports"
    arch = json.loads((rep / "07_selection.json").read_text())["selected"]
    tuned = json.loads((rep / f"06_tuning_daily_{arch}.json").read_text())["chosen"]
    hp, train_hp = tuned["model_hp"], tuned["train_hp"]
    classes = cfg["sequence"]["classes"]
    n_seeds, tag = cfg["training"]["n_seeds"], FREQ
    if args.quick:
        train_hp = dict(train_hp, max_epochs=1)
        n_seeds, tag = 1, f"{FREQ}_quick"

    proc = ROOT / cfg["data"]["processed_dir"]
    data = load_windows(proc, FREQ, cfg, full=True)
    X_tr, y_tr = data.subset("train")
    X_val, y_val = data.subset("val")
    t_val = data.target_time[data.split == "val"]
    if args.quick:
        # every 10th train / 7th val sample so all regimes stay present (backtest numbers meaningless here)
        X_tr, y_tr, X_val, y_val, t_val = X_tr[::10], y_tr[::10], X_val[::7], y_val[::7], t_val[::7]
    close = pd.read_parquet(proc / f"features_{FREQ}_full.parquet")["close"]
    r_val = target_returns(close, t_val)
    print(f"device {device} | arch {arch} | X_train {X_tr.shape} X_val {X_val.shape} | hp {hp} | lr {train_hp['lr']:.2e} "
          f"batch {train_hp['batch_size']}", flush=True)
    print("train class counts", dict(zip(classes, np.bincount(y_tr, minlength=4).tolist())),
          "| val", dict(zip(classes, np.bincount(y_val, minlength=4).tolist())), flush=True)

    out_dir = ROOT / "models" / f"tuned_{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    probs, seeds = [], []
    for s in range(n_seeds):
        seed = cfg["seed"] + s
        weights, meta = out_dir / f"{arch}_seed{seed}.pt", out_dir / f"{arch}_seed{seed}.json"
        torch.manual_seed(seed)
        model = build_model(arch, data.X.shape[2], len(classes), hp).to(device)
        if weights.exists() and meta.exists():
            model.load_state_dict(torch.load(weights, map_location=device))
            info = json.loads(meta.read_text())
            print(f"seed {seed}: already trained, loaded", flush=True)
        else:
            start = time.time()
            fit = train_model(model, X_tr, y_tr, X_val, y_val, train_hp, len(classes), seed)
            torch.save(model.state_dict(), weights)
            info = {"seed": seed, "device": str(device), "best_epoch": fit["best_epoch"], "epochs_run": fit["epochs_run"],
                    "train_seconds": round(time.time() - start, 1), "history": fit["history"]}
            meta.write_text(json.dumps(info, indent=2))
        p = predict_proba(model, X_val)
        pred = p.argmax(axis=1)
        cls = classification_metrics(y_val, pred, classes)
        perf, _ = evaluate_strategy(np.asarray(classes)[pred], r_val, cfg["backtest"], FREQ)
        probs.append(p)
        seeds.append({"seed": seed, "best_epoch": info["best_epoch"], "epochs_run": info["epochs_run"],
                      "train_seconds": info["train_seconds"], **cls, **perf})
        print(f"seed {seed}: acc {cls['accuracy']:.3f}  macroF1 {cls['macro_f1']:.3f}  Sharpe {perf['sharpe']:.2f}  "
              f"best epoch {info['best_epoch']}/{info['epochs_run']}  {info['train_seconds']}s", flush=True)

    ens_prob = np.mean(probs, axis=0)
    ens_pred = ens_prob.argmax(axis=1)
    ens = {**classification_metrics(y_val, ens_pred, classes),
           **evaluate_strategy(np.asarray(classes)[ens_pred], r_val, cfg["backtest"], FREQ)[0],
           "low_confidence_share": float((ens_prob.max(axis=1) < cfg["selection"]["low_confidence_threshold"]).mean())}
    bh = evaluate_strategy(np.array(["bull"] * len(y_val)), r_val, cfg["backtest"], FREQ)[0]
    keys = ["accuracy", "macro_f1", "sharpe", "max_drawdown", "cumulative_return", "avg_exposure"]
    summary = {"time": datetime.now().isoformat(timespec="seconds"), "arch": arch, "device": str(device), "quick": args.quick,
               "model_hp": hp, "train_hp": train_hp, "n_params": count_params(model),
               "n_train": len(y_tr), "n_val": len(y_val), "per_seed": seeds,
               "mean": {k: float(np.mean([s[k] for s in seeds])) for k in keys},
               "std": {k: float(np.std([s[k] for s in seeds])) for k in keys},
               "seed_ensemble": ens, "buy_and_hold": bh}
    (rep / f"08_{tag}_validation.json").write_text(json.dumps(summary, indent=2))

    pct = lambda x: f"{100 * x:.1f}%"
    L = [f"# Step 8 — {arch} on 15-minute bars, validation ({len(y_val):,} bars)", "",
         f"Window 48 bars, tuned daily hyperparameters, rebalance every 48 bars, device {device}.", "",
         "| Model | Accuracy | Macro-F1 | Sharpe | Max DD | Cum. return | Avg exposure |", "|---|---|---|---|---|---|---|"]
    m, sd = summary["mean"], summary["std"]
    L.append(f"| {arch} ({len(seeds)} seeds) | {m['accuracy']:.3f} ± {sd['accuracy']:.3f} | {m['macro_f1']:.3f} ± {sd['macro_f1']:.3f} | "
             f"{m['sharpe']:.2f} ± {sd['sharpe']:.2f} | {pct(m['max_drawdown'])} | {pct(m['cumulative_return'])} | {pct(m['avg_exposure'])} |")
    L.append(f"| {arch} seed ensemble | {ens['accuracy']:.3f} | {ens['macro_f1']:.3f} | {ens['sharpe']:.2f} | {pct(ens['max_drawdown'])} | "
             f"{pct(ens['cumulative_return'])} | {pct(ens['avg_exposure'])} |")
    L.append(f"| *buy & hold* | – | – | {bh['sharpe']:.2f} | {pct(bh['max_drawdown'])} | {pct(bh['cumulative_return'])} | 100.0% |")
    L += ["", f"Ensemble confusion matrix (rows true, cols predicted, {classes}): {ens['confusion_matrix']}"]
    (rep / f"08_{tag}_validation.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
