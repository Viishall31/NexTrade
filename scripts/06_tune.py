"""Step 6: Optuna TPE tuning for one architecture, then a 5-seed re-run of the top trials.

Usage: python scripts/06_tune.py --arch transformer [--freq daily] [--n-trials 50] [--quick]
--quick: 2 epochs, 2 seeds, separate "_quick" outputs, nothing logged -- a pipeline check only.
Run the three architectures as separate processes in parallel. Studies are stored in
models/tuning_{freq}/optuna_{arch}.db and resume if interrupted.

Writes:
  reports/06_tuning_{freq}_{arch}.json          every trial + top-k re-run + chosen config
  models/tuned_{freq}/{arch}_seed{s}.pt         weights of the chosen config, one per seed
  reports/experiments.jsonl                     one line per trial and per re-run (FR-H4)
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.backtest import target_returns
from regime.config import ROOT, load_config
from regime.dataset import load_windows
from regime.models import build_model, count_params
from regime.train import predict_proba, train_model
from regime.tuning import suggest_hparams, tuning_objective


QUICK = False


def log(entry: dict) -> None:
    if QUICK:
        return
    with open(ROOT / "reports" / "experiments.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True, choices=["lstm", "cnn_bilstm_attn", "transformer"])
    ap.add_argument("--freq", choices=["daily", "15min"], default="daily")
    ap.add_argument("--n-trials", type=int, default=None)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    global QUICK
    QUICK = args.quick
    cfg = load_config()
    tag = args.freq
    if args.quick:
        cfg["training"].update(max_epochs=2, n_seeds=2)
        cfg["tuning"].update(rerun_top_k=2)
        tag = f"{args.freq}_quick"
    tun, bt_cfg, classes = cfg["tuning"], cfg["backtest"], cfg["sequence"]["classes"]
    torch.set_num_threads(tun["threads_per_study"])
    n_trials = args.n_trials or tun["n_trials"]

    proc = ROOT / cfg["data"]["processed_dir"]
    data = load_windows(proc, args.freq, cfg)
    X_tr, y_tr = data.subset("train")
    X_val, y_val = data.subset("val")
    r_val = target_returns(pd.read_parquet(proc / f"features_{args.freq}.parquet")["close"],
                           data.target_time[data.split == "val"])
    n_features = X_tr.shape[2]

    def fit_and_score(hp, train_hp, seed, on_epoch=None):
        torch.manual_seed(seed)
        model = build_model(args.arch, n_features, len(classes), hp)
        fit = train_model(model, X_tr, y_tr, X_val, y_val, train_hp, len(classes), seed, on_epoch)
        pred = predict_proba(model, X_val).argmax(axis=1)
        return model, fit, tuning_objective(y_val, pred, r_val, classes, bt_cfg, tun["objective"], args.freq)

    # ---- Optuna study (validation split only; the test file is never touched here) ----
    def objective(trial):
        hp, train_hp = suggest_hparams(trial, args.arch, cfg["models"], cfg["training"], tun["search_space"])

        def on_epoch(epoch, val_pred):
            score = tuning_objective(y_val, val_pred, r_val, classes, bt_cfg, tun["objective"], args.freq)["objective"]
            trial.report(score, epoch)
            if trial.should_prune():
                raise optuna.TrialPruned()

        _, fit, res = fit_and_score(hp, train_hp, cfg["seed"], on_epoch)
        for k in ["macro_f1", "sharpe", "max_drawdown", "cumulative_return", "best_epoch"]:
            trial.set_user_attr(k, res.get(k, fit.get(k)))
        log({"time": datetime.now().isoformat(timespec="seconds"), "step": "06_trial", "freq": args.freq,
             "arch": args.arch, "trial": trial.number, "seed": cfg["seed"], "hyperparameters": hp,
             "training": train_hp, "val_objective": res, "best_epoch": fit["best_epoch"],
             "train_seconds": fit["train_seconds"]})
        print(f"[{args.arch}] trial {trial.number:2d}: obj {res['objective']:.4f}  F1 {res['macro_f1']:.3f}  "
              f"Sharpe {res['sharpe']:.2f}  {fit['train_seconds']}s  {trial.params}", flush=True)
        return res["objective"]

    study_dir = ROOT / "models" / f"tuning_{tag}"
    study_dir.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(
        study_name=f"{args.arch}_{tag}", direction="maximize",
        storage=f"sqlite:///{(study_dir / f'optuna_{args.arch}.db').as_posix()}", load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=tun["sampler_seed"]),
        pruner=optuna.pruners.MedianPruner(**tun["pruner"]))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    done = len([t for t in study.trials if t.state in (optuna.trial.TrialState.COMPLETE, optuna.trial.TrialState.PRUNED)])
    study.optimize(objective, n_trials=max(0, n_trials - done))

    # ---- Re-run the top-k trials with n_seeds seeds; best mean objective wins ----
    complete = sorted([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE],
                      key=lambda t: t.value, reverse=True)
    out_dir = ROOT / "models" / f"tuned_{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    reruns = []
    for t in complete[: tun["rerun_top_k"]]:
        hp, train_hp = suggest_hparams(optuna.trial.FixedTrial(t.params), args.arch, cfg["models"],
                                       cfg["training"], tun["search_space"])
        seeds, models = [], []
        for s in range(cfg["training"]["n_seeds"]):
            seed = cfg["seed"] + s
            model, fit, res = fit_and_score(hp, train_hp, seed)
            seeds.append({"seed": seed, "best_epoch": fit["best_epoch"], **res})
            models.append(model)
            log({"time": datetime.now().isoformat(timespec="seconds"), "step": "06_rerun", "freq": args.freq,
                 "arch": args.arch, "trial": t.number, "seed": seed, "hyperparameters": hp, "training": train_hp,
                 "val_objective": res, "best_epoch": fit["best_epoch"], "train_seconds": fit["train_seconds"]})
        mean = {k: float(np.mean([s[k] for s in seeds])) for k in ["objective", "macro_f1", "sharpe", "max_drawdown", "cumulative_return"]}
        std = {k: float(np.std([s[k] for s in seeds])) for k in ["objective", "macro_f1", "sharpe"]}
        reruns.append({"trial": t.number, "single_seed_objective": t.value, "params": t.params, "model_hp": hp,
                       "train_hp": train_hp, "n_params": count_params(models[0]), "mean": mean, "std": std,
                       "per_seed": seeds, "_models": models})
        print(f"[{args.arch}] re-run trial {t.number}: 5-seed objective {mean['objective']:.4f} ± {std['objective']:.4f} "
              f"(single seed {t.value:.4f})", flush=True)

    best = max(reruns, key=lambda r: r["mean"]["objective"])
    for old in out_dir.glob(f"{args.arch}_seed*.pt"):
        old.unlink()
    for s, model in zip(best["per_seed"], best["_models"]):
        torch.save(model.state_dict(), out_dir / f"{args.arch}_seed{s['seed']}.pt")
    for r in reruns:
        r.pop("_models")

    states = pd.Series([t.state.name for t in study.trials]).value_counts().to_dict()
    report = {
        "arch": args.arch, "freq": args.freq, "n_trials": len(study.trials), "trial_states": states,
        "trials": [{"number": t.number, "state": t.state.name, "value": t.value, "params": t.params,
                    **t.user_attrs} for t in study.trials],
        "reruns": reruns, "chosen_trial": best["trial"], "chosen": best,
    }
    (ROOT / "reports" / f"06_tuning_{tag}_{args.arch}.json").write_text(json.dumps(report, indent=2))
    print(f"[{args.arch}] DONE. chosen trial {best['trial']}: {best['params']}  "
          f"objective {best['mean']['objective']:.4f}, F1 {best['mean']['macro_f1']:.3f}, Sharpe {best['mean']['sharpe']:.2f}", flush=True)


if __name__ == "__main__":
    main()
