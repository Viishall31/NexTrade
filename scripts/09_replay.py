"""Step 9: walk-forward replay of the held-out 15-min test data as a simulated live feed.

Replaces Kite Connect live validation (decision: no broker/API account). Bars are fed one at a
time to regime.replay.LivePipeline; predictions and daily HMM labels are logged to SQLite and
then evaluated (spec section 10 / FR-L2..L4).

Usage:
  python scripts/09_replay.py                              # full test period with models/tuned_15min
  python scripts/09_replay.py --start 2024-04-22 --end 2024-04-30 --weights-dir models/tuned_15min_quick --tag check
                                                           # pipeline check on validation dates

Writes the SQLite log (config replay.db), reports/09_replay_{tag}.json/.md and plots.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.backtest import evaluate_strategy
from regime.config import ROOT, load_config
from regime.dataset import load_windows
from regime.features import TrainOnlyScaler
from regime.hmm import RegimeHMM
from regime.replay import LivePipeline, load_ensemble
from regime.train import classification_metrics, predict_proba

FREQ = "15min"
COLORS = {"bull": "#2e9e5b", "bear": "#d6453d", "sideways": "#9aa0a6", "high_vol": "#e8a33d"}


def main() -> None:
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=str((pd.Timestamp(cfg["split"]["val_end"]) + pd.Timedelta(days=1)).date()))
    ap.add_argument("--end", default="2100-01-01")
    ap.add_argument("--weights-dir", default="models/tuned_15min")
    ap.add_argument("--tag", default="test")
    args = ap.parse_args()

    rep, proc = ROOT / "reports", ROOT / cfg["data"]["processed_dir"]
    classes = cfg["sequence"]["classes"]
    arch = json.loads((rep / "07_selection.json").read_text())["selected"]
    hp = json.loads((rep / f"06_tuning_daily_{arch}.json").read_text())["chosen"]["model_hp"]
    scaler = TrainOnlyScaler.load(proc / "scaler_15min.json")
    models = load_ensemble(arch, hp, ROOT / args.weights_dir, len(scaler.columns), len(classes))
    hmm = RegimeHMM.load(ROOT / "models" / "hmm_daily.pkl")

    bars = pd.concat([pd.read_parquet(proc / "train_15min.parquet"), pd.read_parquet(proc / "test_15min.parquet")])
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end) + pd.Timedelta(days=1)
    history, stream = bars[bars.index < start], bars[(bars.index >= start) & (bars.index < end)]
    print(f"{arch} ensemble of {len(models)} | history {len(history)} bars up to {history.index[-1]} | "
          f"replaying {len(stream)} bars {stream.index[0]} -> {stream.index[-1]}", flush=True)

    # ---------------- replay ----------------
    live = LivePipeline(cfg, history, models, scaler, hmm)
    preds, labels = [], []
    days = stream.groupby(stream.index.normalize())
    for i, (day, g) in enumerate(days):
        for ts, row in g.iterrows():
            preds.append(live.on_bar(ts, row.to_dict()))
        labels.append(live.on_day_close(day))
        if (i + 1) % 20 == 0 or i + 1 == len(days):
            print(f"  day {i + 1}/{len(days)} {day.date()}  label {labels[-1]['regime']}  "
                  f"last prediction {preds[-1]['predicted_regime']} ({preds[-1]['confidence']:.2f})", flush=True)
    P = pd.DataFrame(preds).set_index("timestamp")
    D = pd.DataFrame(labels).set_index("date")

    db = ROOT / cfg["replay"]["db"]
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as con:
        P.assign(run=args.tag).reset_index().to_sql(f"predictions_{args.tag}", con, if_exists="replace", index=False)
        D.assign(run=args.tag).reset_index().to_sql(f"daily_labels_{args.tag}", con, if_exists="replace", index=False)

    # ---------------- evaluation ----------------
    # Prediction made at bar t targets bar t+1; its ground truth is the HMM label of t+1's day.
    E = P.copy()
    E["next_ts"] = E.index.to_series().shift(-1)
    E = E.dropna(subset=["next_ts"])
    E["true_regime"] = D["regime"].reindex(pd.DatetimeIndex(E["next_ts"]).normalize()).to_numpy()
    E["asset_return"] = P["close"].pct_change().shift(-1).loc[E.index]
    idx = {c: i for i, c in enumerate(classes)}
    y_true, y_pred = E["true_regime"].map(idx).to_numpy(), E["predicted_regime"].map(idx).to_numpy()
    cls = classification_metrics(y_true, y_pred, classes)
    perf, bt = evaluate_strategy(E["predicted_regime"].to_numpy(), E["asset_return"].to_numpy(), cfg["backtest"], FREQ)
    bh, _ = evaluate_strategy(np.array(["bull"] * len(E)), E["asset_return"].to_numpy(), cfg["backtest"], FREQ)
    low = E["low_confidence"].to_numpy()

    # Consistency with the batch pipeline (same frozen models, windows built from full-history features)
    data = load_windows(proc, FREQ, cfg, full=True)
    tpos = pd.Index(data.target_time).get_indexer(pd.DatetimeIndex(E["next_ts"]))
    batch_prob = np.mean([predict_proba(m, data.X[tpos]) for m in models], axis=0)
    batch_labels = pd.read_parquet(proc / "labels_daily_full.parquet")["regime"].reindex(D.index)
    consistency = {
        "prediction_agreement": float((batch_prob.argmax(axis=1) == y_pred).mean()),
        "max_abs_probability_diff": float(np.abs(batch_prob - E[[f"p_{c}" for c in classes]].to_numpy()).max()),
        "daily_label_agreement": float((batch_labels.to_numpy() == D["regime"].to_numpy()).mean()),
        "bar_target_label_agreement": float((data.y[tpos] == y_true).mean()),
    }

    bars_per_day = P.groupby(P.index.normalize()).size()
    expected = len(days) * 25
    lat = P["latency_ms"]
    result = {
        "tag": args.tag, "arch": arch, "n_models": len(models), "weights_dir": args.weights_dir,
        "period": [str(P.index[0]), str(P.index[-1])], "days": len(days), "bars": len(P), "evaluated_predictions": len(E),
        "true_label_counts": E["true_regime"].value_counts().to_dict(),
        "predicted_counts": E["predicted_regime"].value_counts().to_dict(),
        "classification": cls,
        "confidence": {"mean": float(E["confidence"].mean()), "low_confidence_share": float(low.mean()),
                       "accuracy_high_confidence": float((y_pred[~low] == y_true[~low]).mean()) if (~low).any() else None,
                       "accuracy_low_confidence": float((y_pred[low] == y_true[low]).mean()) if low.any() else None,
                       "macro_f1_high_confidence": classification_metrics(y_true[~low], y_pred[~low], classes)["macro_f1_present"] if (~low).any() else None},
        "trading": perf, "buy_and_hold": bh,
        "uptime": {"bars_received": len(P), "bars_expected": expected, "share": len(P) / expected,
                   "incomplete_days": {str(k.date()): int(v) for k, v in bars_per_day[bars_per_day != 25].items()}},
        "latency_ms": {"p50": float(lat.quantile(0.5)), "p95": float(lat.quantile(0.95)), "max": float(lat.max()),
                       "requirement_ms": 2000},
        "consistency_with_batch_pipeline": consistency,
        "orders_placed": 0,
    }

    val_path = rep / "08_15min_validation.json"
    if val_path.exists():
        v = json.loads(val_path.read_text())["seed_ensemble"]
        result["replay_vs_validation"] = {
            "macro_f1": {"validation": v["macro_f1"], "replay": cls["macro_f1_present"]},
            "accuracy": {"validation": v["accuracy"], "replay": cls["accuracy"]},
            "sharpe": {"validation": v["sharpe"], "replay": perf["sharpe"]},
            "max_drawdown": {"validation": v["max_drawdown"], "replay": perf["max_drawdown"]},
            "cumulative_return": {"validation": v["cumulative_return"], "replay": perf["cumulative_return"]},
        }
        for m in result["replay_vs_validation"].values():
            m["gap"] = m["replay"] - m["validation"]
    (rep / f"09_replay_{args.tag}.json").write_text(json.dumps(result, indent=2, default=str))

    pct = lambda x: f"{100 * x:.1f}%"
    L = [f"# Step 9 — walk-forward replay ({args.tag}): {arch} 15-min, {result['period'][0][:10]} → {result['period'][1][:10]}", "",
         f"{len(P):,} bars fed one at a time over {len(days)} trading days to a frozen {len(models)}-seed ensemble; "
         "ground truth = frozen HMM advanced one step at each day close. No orders placed (C-4).", "",
         "## Classification", "",
         f"- Accuracy **{cls['accuracy']:.3f}**, macro-F1 (regimes present) **{cls['macro_f1_present']:.3f}**, macro-F1 (all 4) {cls['macro_f1']:.3f}",
         f"- True labels: {result['true_label_counts']}; predicted: {result['predicted_counts']}",
         f"- Confidence: mean {result['confidence']['mean']:.2f}; {pct(result['confidence']['low_confidence_share'])} flagged low (< 0.5); "
         f"accuracy high-confidence {result['confidence']['accuracy_high_confidence']}, low-confidence {result['confidence']['accuracy_low_confidence']}",
         f"- Confusion matrix (rows true, cols predicted, {classes}): {cls['confusion_matrix']}", "",
         "## Trading (rebalance every 48 bars)", "",
         "| | Sharpe | Sortino | Max DD | Cum. return | Avg exposure |", "|---|---|---|---|---|---|",
         f"| Regime strategy | {perf['sharpe']:.2f} | {perf['sortino']:.2f} | {pct(perf['max_drawdown'])} | {pct(perf['cumulative_return'])} | {pct(perf['avg_exposure'])} |",
         f"| Buy & hold | {bh['sharpe']:.2f} | {bh['sortino']:.2f} | {pct(bh['max_drawdown'])} | {pct(bh['cumulative_return'])} | 100.0% |"]
    if "replay_vs_validation" in result:
        L += ["", "## Replay vs validation backtest (FR-L4)", "", "| Metric | Validation (Step 8) | Replay | Gap |", "|---|---|---|---|"]
        for k, m in result["replay_vs_validation"].items():
            L.append(f"| {k} | {m['validation']:.3f} | {m['replay']:.3f} | {m['gap']:+.3f} |")
    c = consistency
    L += ["", "## Operational checks", "",
          f"- Uptime: {result['uptime']['bars_received']}/{result['uptime']['bars_expected']} bars ({pct(result['uptime']['share'])}); incomplete days {result['uptime']['incomplete_days'] or 'none'}",
          f"- Latency per bar (features + {len(models)}-model inference, CPU): p50 {result['latency_ms']['p50']:.0f} ms, p95 {result['latency_ms']['p95']:.0f} ms, max {result['latency_ms']['max']:.0f} ms (requirement < 2000 ms)",
          f"- Replay vs batch pipeline: prediction agreement {pct(c['prediction_agreement'])}, max probability difference {c['max_abs_probability_diff']:.1e}, "
          f"daily label agreement {pct(c['daily_label_agreement'])}, bar target agreement {pct(c['bar_target_label_agreement'])}",
          f"- SQLite log: `{cfg['replay']['db']}` tables `predictions_{args.tag}`, `daily_labels_{args.tag}`"]
    (rep / f"09_replay_{args.tag}.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)

    # ---------------- plots ----------------
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(14, 8.5), sharex=True, gridspec_kw={"height_ratios": [3, 0.5, 1.4]})
    for c_ in classes:
        m = E["predicted_regime"] == c_
        a1.scatter(E.index[m], E["close"][m], s=2, color=COLORS[c_], label=f"predicted {c_}")
    a1.set_ylabel("Nifty 50")
    a1.set_title(f"Replay ({args.tag}): predicted regime per 15-min bar")
    a1.legend(loc="lower left", markerscale=6)
    for c_ in classes:
        m = E["true_regime"] == c_
        a2.scatter(E.index[m], np.zeros(m.sum()), s=12, marker="|", color=COLORS[c_])
    a2.set_yticks([])
    a2.set_ylabel("HMM\nlabel")
    a3.plot(E.index, E["confidence"], lw=0.4, color="#888", label="confidence")
    a3.plot(E.index, pd.Series(y_pred == y_true, index=E.index).rolling(250, min_periods=25).mean(), color="#c0392b",
            lw=1.2, label="rolling accuracy (250 bars)")
    a3.axhline(cfg["selection"]["low_confidence_threshold"], color="k", ls="--", lw=0.8)
    a3.set_ylim(0, 1.02)
    a3.legend(loc="lower left")
    a3.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(rep / f"09_replay_{args.tag}.png", dpi=110)

    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.plot(E.index, np.cumprod(1 + E["asset_return"].to_numpy()), color="k", lw=1, label="buy & hold")
    ax.plot(E.index, np.cumprod(1 + bt["strategy_return"].to_numpy()), color="#c0392b", lw=1.3, label="regime strategy")
    ax.set_title(f"Replay ({args.tag}) equity, 15-min bars")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(rep / f"09_replay_equity_{args.tag}.png", dpi=110)


if __name__ == "__main__":
    main()
