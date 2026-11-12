"""Step 5: trading performance of the Step 4 models on the validation split.

Usage: python scripts/05_backtest_default_models.py --freq daily

Writes reports/05_backtest_{freq}.json/.md and reports/05_equity_{freq}.png
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")  # Windows console default is cp1252

from regime.backtest import evaluate_strategy, target_returns
from regime.config import ROOT, load_config
from regime.dataset import load_windows
from regime.models import ARCHITECTURES, build_model
from regime.train import classification_metrics, predict_proba

METRICS = ["sharpe", "sortino", "max_drawdown", "cumulative_return", "annualized_return", "avg_exposure", "total_turnover"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freq", choices=["daily", "15min"], default="daily")
    args = ap.parse_args()

    cfg = load_config()
    bcfg, classes = cfg["backtest"], np.array(cfg["sequence"]["classes"])
    proc = ROOT / cfg["data"]["processed_dir"]
    data = load_windows(proc, args.freq, cfg)
    val = data.split == "val"
    X_val, y_val, t_val = data.X[val], data.y[val], data.target_time[val]
    close = pd.read_parquet(proc / f"features_{args.freq}.parquet")["close"]
    r_val = target_returns(close, t_val)
    if np.isnan(r_val).any():
        raise ValueError("missing returns for validation targets")

    results, curves = {"freq": args.freq, "period": [str(t_val[0]), str(t_val[-1])], "references": {}, "models": {}}, {}

    # References: buy & hold, and the strategy driven by the true (HMM) labels.
    refs = {
        "buy_and_hold": np.array(["bull"] * len(y_val)),
        "hmm_label_oracle": classes[y_val],                                   # knows the t+1 label
        "hmm_label_lagged": classes[np.concatenate([[data.y[val.argmax() - 1]], y_val[:-1]])],  # label at t
    }
    for name, preds in refs.items():
        perf, bt = evaluate_strategy(preds, r_val, bcfg, args.freq)
        results["references"][name] = perf
        curves[name] = np.cumprod(1 + bt["strategy_return"].to_numpy())

    n_features = data.X.shape[2]
    for arch in ARCHITECTURES:
        per_seed = []
        for path in sorted((ROOT / "models" / f"default_{args.freq}").glob(f"{arch}_seed*.pt")):
            model = build_model(arch, n_features, len(classes), cfg["models"][arch])
            model.load_state_dict(torch.load(path))
            pred = predict_proba(model, X_val).argmax(axis=1)
            perf, bt = evaluate_strategy(classes[pred], r_val, bcfg, args.freq)
            perf["macro_f1"] = classification_metrics(y_val, pred, list(classes))["macro_f1"]
            perf["seed"] = int(path.stem.split("seed")[1])
            per_seed.append(perf)
            curves.setdefault(arch, []).append(np.cumprod(1 + bt["strategy_return"].to_numpy()))
        results["models"][arch] = {
            "per_seed": per_seed,
            **{f"{m}_mean": float(np.mean([p[m] for p in per_seed])) for m in METRICS + ["macro_f1"]},
            **{f"{m}_std": float(np.std([p[m] for p in per_seed])) for m in METRICS + ["macro_f1"]},
        }
        print(f"{arch}: Sharpe per seed {[round(p['sharpe'], 2) for p in per_seed]}")

    (ROOT / "reports" / f"05_backtest_{args.freq}.json").write_text(json.dumps(results, indent=2))

    def pct(x):
        return f"{100 * x:.1f}%"

    lines = [f"# Step 5 — regime-conditioned backtest, {args.freq}, validation {results['period'][0][:10]} → {results['period'][1][:10]}",
             "", "Exposure bull 100% / sideways 50% / high_vol 25% / bear 0%; 5 bps per unit exposure change; "
             "uninvested cash earns 6% p.a.; Sharpe/Sortino on excess return over 6%.", "",
             "| Strategy | Sharpe | Sortino | Max DD | Cum. return | Ann. return | Avg exposure | Macro-F1 |",
             "|---|---|---|---|---|---|---|---|"]
    for arch, m in results["models"].items():
        lines.append(f"| {arch} (5 seeds) | {m['sharpe_mean']:.2f} ± {m['sharpe_std']:.2f} | {m['sortino_mean']:.2f} | "
                     f"{pct(m['max_drawdown_mean'])} | {pct(m['cumulative_return_mean'])} | {pct(m['annualized_return_mean'])} | "
                     f"{pct(m['avg_exposure_mean'])} | {m['macro_f1_mean']:.3f} |")
    for name, p in results["references"].items():
        lines.append(f"| *{name}* | {p['sharpe']:.2f} | {p['sortino']:.2f} | {pct(p['max_drawdown'])} | "
                     f"{pct(p['cumulative_return'])} | {pct(p['annualized_return'])} | {pct(p['avg_exposure'])} | – |")
    lines += ["", "*hmm_label_oracle* trades on the true next-day HMM label (unattainable upper reference); "
              "*hmm_label_lagged* trades on the HMM label known at the close of t."]
    (ROOT / "reports" / f"05_backtest_{args.freq}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.plot(t_val, curves["buy_and_hold"], color="k", lw=1.5, label="buy & hold")
    ax.plot(t_val, curves["hmm_label_oracle"], color="k", lw=1, ls=":", label="HMM label oracle")
    for arch, color in zip(ARCHITECTURES, ["#4c72b0", "#8e5bb5", "#dd8452"]):
        stack = np.vstack(curves[arch])
        ax.plot(t_val, stack.mean(axis=0), color=color, lw=1.5, label=f"{arch} (mean of 5 seeds)")
        ax.fill_between(t_val, stack.min(axis=0), stack.max(axis=0), color=color, alpha=0.15)
    ax.set_ylabel("Growth of 1")
    ax.set_title(f"Validation equity curves ({args.freq}) — shaded = range across seeds")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ROOT / "reports" / f"05_equity_{args.freq}.png", dpi=110)


if __name__ == "__main__":
    main()
