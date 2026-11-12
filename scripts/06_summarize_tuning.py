"""Step 6 summary: default vs tuned (both 5 seeds, validation split) + tuning history (AC-3).

Usage: python scripts/06_summarize_tuning.py [--freq daily]
Writes reports/06_tuning_{freq}.md and reports/06_tuning_history_{freq}.png
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import optuna

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.models import ARCHITECTURES
from regime.tuning import normalized_sharpe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freq", choices=["daily", "15min"], default="daily")
    args = ap.parse_args()
    cfg = load_config()
    obj = cfg["tuning"]["objective"]
    rep = ROOT / "reports"

    default_bt = json.loads((rep / f"05_backtest_{args.freq}.json").read_text())["models"]
    default_params = {a: m["n_params"] for a, m in json.loads((rep / f"04_default_{args.freq}.json").read_text())["models"].items()}
    lines = [f"# Step 6 — hyperparameter tuning, {args.freq}", "",
             f"Optuna TPE, {cfg['tuning']['n_trials']} trials per architecture, median pruner. Objective = "
             f"{obj['f1_weight']} × macro-F1 + {obj['sharpe_weight']} × clip((Sharpe + 1) / 3, 0, 1) on the validation split. "
             f"Top {cfg['tuning']['rerun_top_k']} trials re-run with {cfg['training']['n_seeds']} seeds; best mean wins. "
             "Default and tuned numbers below are both 5-seed means on the same validation split.", "",
             "| Model | Config | Objective | Macro-F1 | Sharpe | Max DD | Params |",
             "|---|---|---|---|---|---|---|"]
    chosen = {}
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for arch, color in zip(ARCHITECTURES, ["#4c72b0", "#8e5bb5", "#dd8452"]):
        path = rep / f"06_tuning_{args.freq}_{arch}.json"
        if not path.exists():
            lines.append(f"| {arch} | tuning not finished | | | | | |")
            continue
        d = json.loads(path.read_text())
        seeds = default_bt[arch]["per_seed"]
        default_obj = [obj["f1_weight"] * s["macro_f1"] + obj["sharpe_weight"] * normalized_sharpe(s["sharpe"], *obj["sharpe_range"])
                       for s in seeds]
        c = d["chosen"]
        chosen[arch] = c
        lines.append(f"| {arch} | default | {np.mean(default_obj):.4f} ± {np.std(default_obj):.4f} | "
                     f"{default_bt[arch]['macro_f1_mean']:.3f} | {default_bt[arch]['sharpe_mean']:.2f} | "
                     f"{100 * default_bt[arch]['max_drawdown_mean']:.1f}% | {default_params[arch]:,} |")
        lines.append(f"| {arch} | **tuned** (trial {d['chosen_trial']}) | **{c['mean']['objective']:.4f} ± {c['std']['objective']:.4f}** | "
                     f"{c['mean']['macro_f1']:.3f} | {c['mean']['sharpe']:.2f} | {100 * c['mean']['max_drawdown']:.1f}% | {c['n_params']:,} |")

        values = [t["value"] if t["state"] == "COMPLETE" else np.nan for t in d["trials"]]
        ax.scatter(range(len(values)), values, s=10, color=color, alpha=0.5)
        ax.plot(np.fmax.accumulate(np.nan_to_num(values, nan=-np.inf)), color=color, label=f"{arch} best so far")

    lines += ["", "## Chosen hyperparameters", ""]
    for arch, c in chosen.items():
        lines.append(f"- **{arch}**: " + ", ".join(f"{k}={v:.2e}" if k == "lr" else f"{k}={round(v, 3) if isinstance(v, float) else v}"
                                                    for k, v in c["params"].items()))

    lines += ["", "## Top-3 re-runs (single-seed trial score vs 5-seed mean)", "",
              "| Model | Trial | Single seed | 5-seed mean ± std |", "|---|---|---|---|"]
    for arch in chosen:
        d = json.loads((rep / f"06_tuning_{args.freq}_{arch}.json").read_text())
        for r in d["reruns"]:
            lines.append(f"| {arch} | {r['trial']} | {r['single_seed_objective']:.4f} | {r['mean']['objective']:.4f} ± {r['std']['objective']:.4f} |")

    lines += ["", "## Parameter importance (fANOVA over completed trials)", ""]
    for arch in chosen:
        study = optuna.load_study(study_name=f"{arch}_{args.freq}",
                                  storage=f"sqlite:///{(ROOT / 'models' / f'tuning_{args.freq}' / f'optuna_{arch}.db').as_posix()}")
        try:
            imp = optuna.importance.get_param_importances(study, evaluator=optuna.importance.FanovaImportanceEvaluator(seed=0))
            lines.append(f"- **{arch}**: " + ", ".join(f"{k} {v:.2f}" for k, v in imp.items()))
        except Exception as e:  # too few completed trials
            lines.append(f"- **{arch}**: not available ({e})")

    lines += ["", "Deviation from spec: CNN-BiLSTM-Attention's attention heads are not tuned — spec 6.2 defines "
              "additive (Bahdanau) attention, which has no heads. Its `layers` parameter controls the number of conv layers."]
    (rep / f"06_tuning_{args.freq}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    ax.set_xlabel("trial")
    ax.set_ylabel("validation objective (single seed)")
    ax.set_title(f"Optuna tuning history ({args.freq}) — dots = completed trials")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(rep / f"06_tuning_history_{args.freq}.png", dpi=110)


if __name__ == "__main__":
    main()
