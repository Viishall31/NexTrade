"""Step 7c: one-time evaluation on the held-out test period (Nifty50_test.csv, daily).

Requires reports/07_selection.json (selection frozen on validation). Evaluates every frozen
model -- default and tuned, all three architectures, 5 seeds each -- plus the deployed
seed-ensemble of the selected architecture, simple baselines and trading references.

Writes reports/07_test_results.json/.md, 07_test_equity.png, 07_test_regimes.png
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.backtest import evaluate_strategy, target_returns
from regime.config import ROOT, load_config
from regime.dataset import load_windows
from regime.models import ARCHITECTURES, build_model
from regime.train import classification_metrics, predict_proba

FREQ = "daily"
COLORS = {"bull": "#2e9e5b", "bear": "#d6453d", "sideways": "#9aa0a6", "high_vol": "#e8a33d"}


def load_seed_models(arch: str, variant: str, cfg: dict, n_features: int, n_classes: int) -> list:
    if variant == "default":
        hp = cfg["models"][arch]
    else:
        hp = json.loads((ROOT / "reports" / f"06_tuning_{FREQ}_{arch}.json").read_text())["chosen"]["model_hp"]
    models = []
    for path in sorted((ROOT / "models" / f"{variant}_{FREQ}").glob(f"{arch}_seed*.pt")):
        m = build_model(arch, n_features, n_classes, hp)
        m.load_state_dict(torch.load(path))
        models.append((int(path.stem.split("seed")[1]), m))
    if len(models) != cfg["training"]["n_seeds"]:
        raise ValueError(f"expected {cfg['training']['n_seeds']} seeds for {variant}/{arch}, found {len(models)}")
    return models


def score(pred, y, r, classes, cfg) -> dict:
    cls = classification_metrics(y, pred, classes)
    perf, _ = evaluate_strategy(np.asarray(classes)[pred], r, cfg["backtest"], FREQ)
    return {**cls, **perf}


def main() -> None:
    cfg = load_config()
    rep = ROOT / "reports"
    selection = json.loads((rep / "07_selection.json").read_text())
    selected = selection["selected"]
    classes = cfg["sequence"]["classes"]
    proc = ROOT / cfg["data"]["processed_dir"]

    data = load_windows(proc, FREQ, cfg, full=True)
    test = data.split == "test"
    X_te, y_te, t_te = data.X[test], data.y[test], data.target_time[test]
    close = pd.read_parquet(proc / f"features_{FREQ}_full.parquet")["close"]
    r_te = target_returns(close, t_te)
    if np.isnan(r_te).any():
        raise ValueError("missing test returns")
    n_features = data.X.shape[2]
    print(f"test samples {len(y_te)}  {t_te[0].date()} -> {t_te[-1].date()}  classes present "
          f"{[classes[i] for i in sorted(set(y_te))]}")

    results = {"evaluated_at": datetime.now().isoformat(timespec="seconds"), "selected": selected,
               "period": [str(t_te[0].date()), str(t_te[-1].date())], "n_test": int(len(y_te)),
               "test_label_counts": {c: int((y_te == i).sum()) for i, c in enumerate(classes)},
               "models": {}, "references": {}}
    keys = ["accuracy", "macro_f1", "macro_f1_present", "sharpe", "sortino", "max_drawdown", "cumulative_return", "avg_exposure"]
    curves = {}

    for variant in ["default", "tuned"]:
        for arch in ARCHITECTURES:
            per_seed, probs = [], []
            for seed, model in load_seed_models(arch, variant, cfg, n_features, len(classes)):
                p = predict_proba(model, X_te)
                probs.append(p)
                per_seed.append({"seed": seed, **score(p.argmax(axis=1), y_te, r_te, classes, cfg)})
            name = f"{arch}/{variant}"
            results["models"][name] = {
                "per_seed": per_seed,
                "mean": {k: float(np.mean([s[k] for s in per_seed])) for k in keys},
                "std": {k: float(np.std([s[k] for s in per_seed])) for k in keys},
            }
            if variant == "tuned":
                curves[arch] = np.vstack([np.cumprod(1 + evaluate_strategy(np.asarray(classes)[p.argmax(axis=1)], r_te,
                                                                           cfg["backtest"], FREQ)[1]["strategy_return"])
                                          for p in probs])
            if variant == "tuned" and arch == selected:
                ens_prob = np.mean(probs, axis=0)

    # ---- Deployed model: seed ensemble of the selected architecture ----
    ens_pred = ens_prob.argmax(axis=1)
    ens = score(ens_pred, y_te, r_te, classes, cfg)
    conf = ens_prob.max(axis=1)
    low = conf < cfg["selection"]["low_confidence_threshold"]
    ens["confidence"] = {
        "mean_confidence": float(conf.mean()),
        "low_confidence_share": float(low.mean()),
        "accuracy_high_confidence": float((ens_pred[~low] == y_te[~low]).mean()) if (~low).any() else None,
        "accuracy_low_confidence": float((ens_pred[low] == y_te[low]).mean()) if low.any() else None,
    }
    # FR-E2: regime-stratified performance (by true HMM regime on the target day)
    _, bt = evaluate_strategy(np.asarray(classes)[ens_pred], r_te, cfg["backtest"], FREQ)
    ens["by_true_regime"] = {
        c: {"days": int((y_te == i).sum()),
            "recall": float((ens_pred[y_te == i] == i).mean()),
            "predicted_as": {classes[j]: int((ens_pred[y_te == i] == j).sum()) for j in range(len(classes))},
            "strategy_mean_daily_return_bps": float(1e4 * bt["strategy_return"][y_te == i].mean()),
            "buy_hold_mean_daily_return_bps": float(1e4 * r_te[y_te == i].mean())}
        for i, c in enumerate(classes) if (y_te == i).any()}
    results["deployed_seed_ensemble"] = ens
    curves["deployed"] = np.cumprod(1 + bt["strategy_return"].to_numpy())

    # ---- Validation -> test gap for the selected model (the key generalisation number) ----
    val = json.loads((rep / f"06_tuning_{FREQ}_{selected}.json").read_text())["chosen"]["mean"]
    tst = results["models"][f"{selected}/tuned"]["mean"]
    # Validation has all 4 regimes; test may not, so compare against the present-class macro-F1.
    test_key = {"macro_f1": "macro_f1_present"}
    results["selected_val_vs_test"] = {k: {"validation": val[k], "test": tst[test_key.get(k, k)], "gap": tst[test_key.get(k, k)] - val[k]}
                                       for k in ["macro_f1", "sharpe", "max_drawdown", "cumulative_return"]}

    # ---- Baselines and references ----
    X_tr, y_tr = data.subset("train")
    lr = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X_tr[:, -1], y_tr)
    results["references"]["logistic_regression_last_bar"] = score(lr.predict(X_te[:, -1]), y_te, r_te, classes, cfg)
    for name, preds in {"buy_and_hold": np.array(["bull"] * len(y_te)),
                        "hmm_label_oracle": np.asarray(classes)[y_te],
                        "hmm_label_lagged": np.asarray(classes)[data.y[np.where(test)[0] - 1]]}.items():
        perf, bt_ref = evaluate_strategy(preds, r_te, cfg["backtest"], FREQ)
        results["references"][name] = perf
        curves[name] = np.cumprod(1 + bt_ref["strategy_return"].to_numpy())

    (rep / "07_test_results.json").write_text(json.dumps(results, indent=2))
    with open(rep / "experiments.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": results["evaluated_at"], "step": "07_test", "freq": FREQ, "selected": selected,
                            "deployed": {k: ens[k] for k in keys}, "models": {k: v["mean"] for k, v in results["models"].items()}}) + "\n")

    # ---- Markdown report ----
    pct = lambda x: f"{100 * x:.1f}%"
    L = [f"# Step 7 — held-out test, {FREQ}, {results['period'][0]} → {results['period'][1]} ({len(y_te)} days)", "",
         f"Selection frozen on validation before this run (`07_selection.json`): **{selected}**. "
         f"Test labels (frozen HMM): {results['test_label_counts']}. "
         "Macro-F1 (3) = over the regimes present in the test labels; Macro-F1 (4) counts absent high_vol as 0.", "",
         "| Model | Accuracy | Macro-F1 (3) | Macro-F1 (4) | Sharpe | Max DD | Cum. return | Avg exposure |",
         "|---|---|---|---|---|---|---|---|"]
    for name, m in results["models"].items():
        mu, sd = m["mean"], m["std"]
        bold = "**" if name == f"{selected}/tuned" else ""
        L.append(f"| {bold}{name}{bold} | {mu['accuracy']:.3f} ± {sd['accuracy']:.3f} | {mu['macro_f1_present']:.3f} ± {sd['macro_f1_present']:.3f} | "
                 f"{mu['macro_f1']:.3f} | {mu['sharpe']:.2f} ± {sd['sharpe']:.2f} | {pct(mu['max_drawdown'])} | {pct(mu['cumulative_return'])} | {pct(mu['avg_exposure'])} |")
    L.append(f"| **deployed: {selected} 5-seed ensemble** | {ens['accuracy']:.3f} | {ens['macro_f1_present']:.3f} | {ens['macro_f1']:.3f} | "
             f"{ens['sharpe']:.2f} | {pct(ens['max_drawdown'])} | {pct(ens['cumulative_return'])} | {pct(ens['avg_exposure'])} |")
    lrm = results["references"]["logistic_regression_last_bar"]
    L.append(f"| *logistic regression (last bar)* | {lrm['accuracy']:.3f} | {lrm['macro_f1_present']:.3f} | {lrm['macro_f1']:.3f} | "
             f"{lrm['sharpe']:.2f} | {pct(lrm['max_drawdown'])} | {pct(lrm['cumulative_return'])} | {pct(lrm['avg_exposure'])} |")
    for name in ["buy_and_hold", "hmm_label_oracle", "hmm_label_lagged"]:
        p = results["references"][name]
        L.append(f"| *{name}* | – | – | – | {p['sharpe']:.2f} | {pct(p['max_drawdown'])} | {pct(p['cumulative_return'])} | {pct(p['avg_exposure'])} |")

    L += ["", f"## Validation → test gap ({selected}, tuned, 5-seed mean)", "", "| Metric | Validation | Test | Gap |", "|---|---|---|---|"]
    for k, v in results["selected_val_vs_test"].items():
        L.append(f"| {k} | {v['validation']:.3f} | {v['test']:.3f} | {v['gap']:+.3f} |")

    L += ["", "## Deployed model by true regime (FR-E2)", "",
          "| True regime | Days | Recall | Predicted as | Strategy bps/day | Buy & hold bps/day |", "|---|---|---|---|---|---|"]
    for c, s in ens["by_true_regime"].items():
        L.append(f"| {c} | {s['days']} | {s['recall']:.2f} | {s['predicted_as']} | {s['strategy_mean_daily_return_bps']:.1f} | {s['buy_hold_mean_daily_return_bps']:.1f} |")
    cf = ens["confidence"]
    L += ["", f"Confidence: mean {cf['mean_confidence']:.2f}; {pct(cf['low_confidence_share'])} of predictions below "
          f"{cfg['selection']['low_confidence_threshold']} (flagged). Accuracy high-confidence {cf['accuracy_high_confidence']}, "
          f"low-confidence {cf['accuracy_low_confidence']}.",
          "", f"Confusion matrix, deployed model (rows true, cols predicted, {classes}): {ens['confusion_matrix']}"]
    (rep / "07_test_results.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))

    # ---- Plots ----
    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.plot(t_te, curves["buy_and_hold"], color="k", lw=1.5, label="buy & hold")
    ax.plot(t_te, curves["hmm_label_oracle"], color="k", lw=1, ls=":", label="HMM label oracle")
    for arch, color in zip(ARCHITECTURES, ["#4c72b0", "#8e5bb5", "#dd8452"]):
        ax.plot(t_te, curves[arch].mean(axis=0), color=color, lw=1.2, label=f"{arch} tuned (mean of 5 seeds)")
        ax.fill_between(t_te, curves[arch].min(axis=0), curves[arch].max(axis=0), color=color, alpha=0.12)
    ax.plot(t_te, curves["deployed"], color="#c0392b", lw=2, label=f"deployed: {selected} ensemble")
    ax.set_ylabel("Growth of 1")
    ax.set_title("Held-out test period — equity curves")
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(rep / "07_test_equity.png", dpi=110)

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(13, 6.5), sharex=True)
    px = close.reindex(t_te).to_numpy()
    for ax_, lab, title in [(a1, y_te, "HMM label (frozen HMM)"), (a2, ens_pred, f"Deployed {selected} prediction")]:
        for i, c in enumerate(classes):
            m = lab == i
            ax_.scatter(t_te[m], px[m], s=9, color=COLORS[c], label=c)
        ax_.set_title(title)
        ax_.set_ylabel("Nifty 50")
        ax_.grid(alpha=0.3)
    a2.scatter(t_te[low], px[low], s=40, facecolors="none", edgecolors="k", lw=0.8, label="low confidence")
    a1.legend(loc="lower left", markerscale=2)
    a2.legend(loc="lower left", markerscale=2)
    fig.tight_layout()
    fig.savefig(rep / "07_test_regimes.png", dpi=110)


if __name__ == "__main__":
    main()
