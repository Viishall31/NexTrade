"""Step 12b: forward test on fresh data (8 Apr 2025 -> latest) -- nothing changed, nothing re-selected.

For each daily architecture: classification vs the frozen HMM labels, then trading from Rs 10,00,000 with
  - Experiment 1 frozen rules  (reports/10_rules_daily_{arch}.json): ETF and futures
  - Experiment 2 frozen rulebook (reports/11_rulebook_frozen.json): default, tuned ETF, tuned futures
against buy & hold and cash. Test-year numbers are shown alongside for comparison.

Writes reports/12_fresh_results.json/.md, 12_fresh_equity.png, 12_fresh_regimes.png, 12_trades_fresh_*.csv
"""
import json
import sys
from datetime import datetime
from importlib import import_module
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.models import ARCHITECTURES
from regime.rulebook import RuleBook, run_rulebook_on
from regime.train import classification_metrics
from regime.trading import Rule

design = import_module("10_design_rules")
NAMES = {"lstm": "LSTM", "cnn_bilstm_attn": "CNN-BiLSTM-Attention", "transformer": "Transformer"}
COLORS = {"bull": "#2e9e5b", "bear": "#d6453d", "sideways": "#9aa0a6", "high_vol": "#e8a33d"}
SYSTEMS = {  # key -> (label, experiment)
    "exp1_long_only": ("Exp 1 rules, ETF", 1), "exp1_long_short": ("Exp 1 rules, futures*", 1),
    "exp2_default": ("Exp 2 rulebook default, ETF", 2), "exp2_tuned_cash": ("Exp 2 rulebook tuned, ETF", 2),
    "exp2_tuned_short": ("Exp 2 rulebook tuned, futures*", 2),
}


def rs(x: float) -> str:
    return f"Rs {x:,.0f}"


def avg_exposure(trades: pd.DataFrame, decision_times: pd.Series, col: str) -> float:
    """Average target exposure per day, from the trade log (position held until the next trade)."""
    if trades.empty:
        return 0.0
    pos = pd.Series(trades[col].to_numpy(), index=pd.DatetimeIndex(trades["time"]))
    return float(pos.reindex(pd.DatetimeIndex(decision_times)).ffill().fillna(0.0).abs().mean())


def main() -> None:
    cfg = load_config()
    tcfg, classes = cfg["trading"], cfg["sequence"]["classes"]
    rep, proc = ROOT / "reports", ROOT / cfg["data"]["processed_dir"]
    rulebook = json.loads((rep / "11_rulebook_frozen.json").read_text())
    test_exp1 = json.loads((rep / "10_architectures_test.json").read_text())["architectures"]
    test_exp2 = json.loads((rep / "11_rulebook_test.json").read_text())["results"]
    start = tcfg["initial_capital"]

    out = {"evaluated_at": datetime.now().isoformat(timespec="seconds"), "architectures": {}}
    equity, preds = {}, {}
    for arch in ARCHITECTURES:
        sig = pd.read_parquet(proc / f"signals_daily_{arch}_fresh.parquet")
        old = pd.read_parquet(proc / f"signals_daily_{arch}.parquet")
        pcols = [f"p_{c}" for c in classes]
        idx = {c: i for i, c in enumerate(classes)}
        y_true, y_pred = sig["true_regime"].map(idx).to_numpy(), sig[pcols].to_numpy().argmax(axis=1)
        told = old[old["split"] == "test"]
        cls_fresh = classification_metrics(y_true, y_pred, classes)
        cls_test = classification_metrics(told["true_regime"].map(idx).to_numpy(), told[pcols].to_numpy().argmax(axis=1), classes)
        preds[arch] = np.asarray(classes)[y_pred]

        fz1 = json.loads((rep / f"10_rules_daily_{arch}.json").read_text())["directions"]
        runs = {}
        for d in ["long_only", "long_short"]:
            r = fz1[d]["rule"]
            res = design.run_split(sig, Rule(r["direction"], r["exposure_map"], r["confirm"], r["min_confidence"], r["stop_loss"]),
                                   cfg, "daily", keep_log=True)
            runs[f"exp1_{d}"] = (res, "target_exposure", test_exp1[arch]["own_rules"][d]["final_capital"])
        for v in ["default", "tuned_cash", "tuned_short"]:
            rb = RuleBook(**{k: x for k, x in rulebook["architectures"][arch][v]["rulebook"].items() if k != "name"})
            res = run_rulebook_on(sig, rb, cfg, keep_log=True)
            runs[f"exp2_{v}"] = (res, "position_after", test_exp2[arch][v]["final_capital"])

        entry = {"classification_fresh": {k: cls_fresh[k] for k in ["accuracy", "macro_f1_present", "confusion_matrix"]},
                 "classification_test": {k: cls_test[k] for k in ["accuracy", "macro_f1_present"]},
                 "predicted_counts": pd.Series(preds[arch]).value_counts().to_dict(), "systems": {}}
        for key, (res, col, test_final) in runs.items():
            trades = pd.DataFrame(res.pop("trades"))
            trades.to_csv(rep / f"12_trades_fresh_{arch}_{key}.csv", index=False)
            equity[(arch, key)] = res.pop("equity")
            expo = avg_exposure(trades, sig["decision_time"], col)
            ret = (sig["price_next"] / sig["price_now"] - 1).to_numpy()
            rf = (1 + tcfg["cash_yield_annual"]) ** (1 / 252) - 1
            same_expo = start * np.prod(1 + expo * ret + (1 - expo) * rf)
            entry["systems"][key] = {**{k: res[k] for k in ["final_capital", "net_profit", "total_return", "max_drawdown", "sharpe",
                                                            "n_trades", "total_costs", "interest_earned", "time_in_market"]},
                                     "rule": (res.get("rule") or res.get("rulebook"))["name"],
                                     "trading_pnl_excl_interest": res["net_profit"] - res["interest_earned"],
                                     "avg_exposure": expo, "same_exposure_no_signals_final": float(same_expo),
                                     "test_year_final": test_final}
        out["architectures"][arch] = entry

    bh_sig = sig.copy()
    for c in classes:
        bh_sig[f"p_{c}"] = 1.0 if c == "bull" else 0.0
    bh = run_rulebook_on(bh_sig, RuleBook(buy_threshold=0.5, confirm_days=1, sizing="full", stop_loss=None, cooldown_days=0), cfg, keep_log=True)
    bh.pop("trades")
    equity["buy_and_hold"] = bh.pop("equity")
    cash_final = start * (1 + tcfg["cash_yield_annual"]) ** (len(sig) / 252)
    period = [str(sig["decision_time"].iloc[0].date()), str(sig["next_time"].iloc[-1].date())]
    out.update(period=period, n_days=len(sig), buy_and_hold=bh, cash_only_final=cash_final,
               true_label_counts=sig["true_regime"].value_counts().to_dict())
    (rep / "12_fresh_results.json").write_text(json.dumps(out, indent=2, default=str))
    with open(rep / "experiments.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": out["evaluated_at"], "step": "12_fresh_forward_test", "period": period,
                            "final_capital": {f"{a}/{k}": v["final_capital"] for a, e in out["architectures"].items() for k, v in e["systems"].items()},
                            "buy_and_hold_final": bh["final_capital"], "cash_final": cash_final}) + "\n")

    pct = lambda x: f"{100 * x:+.1f}%"
    L = [f"# Step 12 — forward test on fresh data ({period[0]} → {period[1]}, {len(sig)} trading days)", "",
         "Data that did not exist in the project files (yfinance ^NSEI, after Nifty50_test.csv ends). **Nothing was changed**: "
         "frozen scaler, frozen HMM, tuned daily models, frozen Experiment 1 rules and frozen Experiment 2 rulebook. "
         f"Frozen-HMM labels in this period: {out['true_label_counts']}. Nifty {sig['price_now'].iloc[0]:,.0f} → {sig['price_next'].iloc[-1]:,.0f}.", "",
         "## Classification", "", "| Model | Test year accuracy | Test year macro-F1 | **Fresh accuracy** | **Fresh macro-F1** | Predicted (fresh) |",
         "|---|---|---|---|---|---|"]
    for a, e in out["architectures"].items():
        L.append(f"| {NAMES[a]} | {e['classification_test']['accuracy']:.3f} | {e['classification_test']['macro_f1_present']:.3f} | "
                 f"**{e['classification_fresh']['accuracy']:.3f}** | **{e['classification_fresh']['macro_f1_present']:.3f}** | {e['predicted_counts']} |")

    L += ["", f"## Trading from {rs(start)}", "",
          f"Benchmarks on fresh data: **buy & hold {rs(bh['final_capital'])} ({pct(bh['total_return'])}, max DD {100 * bh['max_drawdown']:.1f}%)**, "
          f"**cash at 6% {rs(cash_final)} ({pct(cash_final / start - 1)})**. *futures = idealized.", "",
          "| Model | System | Test year final | **Fresh: amount left** | Profit | of which interest | **Trading P&L** | Max DD | Trades | Avg exposure | Same exposure, no signals |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a, e in out["architectures"].items():
        for key, s in e["systems"].items():
            L.append(f"| {NAMES[a]} | {SYSTEMS[key][0]} | {rs(s['test_year_final'])} | **{rs(s['final_capital'])}** | {rs(s['net_profit'])} ({pct(s['total_return'])}) | "
                     f"{rs(s['interest_earned'])} | **{rs(s['trading_pnl_excl_interest'])}** | {100 * s['max_drawdown']:.1f}% | {s['n_trades']} | "
                     f"{100 * s['avg_exposure']:.0f}% | {rs(s['same_exposure_no_signals_final'])} |")

    allsys = [(a, k, s) for a, e in out["architectures"].items() for k, s in e["systems"].items()]
    n = len(allsys)
    count = lambda cond: sum(1 for a, k, s in allsys if cond(s))
    realistic = [(a, k, s) for a, k, s in allsys if "futures" not in SYSTEMS[k][0]]
    L += ["", "## Scorecard", "",
          f"| Question | All {n} systems | Realistic (ETF) {len(realistic)} systems |", "|---|---|---|",
          f"| Ended with a profit | {count(lambda s: s['final_capital'] > start)} | {sum(1 for _, _, s in realistic if s['final_capital'] > start)} |",
          f"| Beat buy & hold ({rs(bh['final_capital'])}) | {count(lambda s: s['final_capital'] > bh['final_capital'])} | {sum(1 for _, _, s in realistic if s['final_capital'] > bh['final_capital'])} |",
          f"| Beat cash at 6% ({rs(cash_final)}) | {count(lambda s: s['final_capital'] > cash_final)} | {sum(1 for _, _, s in realistic if s['final_capital'] > cash_final)} |",
          f"| Positive trading P&L (excl. interest) | {count(lambda s: s['trading_pnl_excl_interest'] > 0)} | {sum(1 for _, _, s in realistic if s['trading_pnl_excl_interest'] > 0)} |",
          f"| Timing beat same exposure without signals | {count(lambda s: s['final_capital'] > s['same_exposure_no_signals_final'])} | {sum(1 for _, _, s in realistic if s['final_capital'] > s['same_exposure_no_signals_final'])} |",
          f"| Smaller drawdown than buy & hold ({100 * bh['max_drawdown']:.1f}%) | {count(lambda s: s['max_drawdown'] > bh['max_drawdown'])} | {sum(1 for _, _, s in realistic if s['max_drawdown'] > bh['max_drawdown'])} |",
          "", "'Same exposure, no signals' holds the system's average exposure every day with no timing (costs ignored) — "
          "it separates the value of buy/sell timing from simply being less invested.",
          "Trade logs: `reports/12_trades_fresh_<arch>_<system>.csv`."]
    (rep / "12_fresh_results.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), sharey=True)
    for ax, a in zip(axes, ARCHITECTURES):
        ax.plot(equity["buy_and_hold"].index, equity["buy_and_hold"] / 1e5, color="k", lw=1.4, label="buy & hold ETF")
        for key, color, ls in [("exp1_long_only", "#999999", "--"), ("exp2_default", "#c0392b", "-"), ("exp2_tuned_cash", "#2471a3", "-")]:
            ax.plot(equity[(a, key)].index, equity[(a, key)] / 1e5, color=color, ls=ls, lw=1.6, label=SYSTEMS[key][0])
        ax.axhline(start / 1e5, color="k", lw=0.6)
        ax.set_title(NAMES[a])
        ax.grid(alpha=0.3)
        ax.tick_params(axis="x", rotation=30)
    axes[0].set_ylabel("Portfolio value (Rs lakh)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle(f"Forward test on fresh data {period[0]} → {period[1]}, start Rs 10 lakh (all rules frozen)")
    fig.tight_layout()
    fig.savefig(rep / "12_fresh_equity.png", dpi=110)

    fig, axes = plt.subplots(4, 1, figsize=(14, 9), sharex=True)
    t, px = pd.DatetimeIndex(sig["next_time"]), sig["price_next"].to_numpy()
    rows = [("Frozen HMM label", sig["true_regime"].to_numpy())] + [(f"{NAMES[a]} prediction", preds[a]) for a in ARCHITECTURES]
    for ax, (title, lab) in zip(axes, rows):
        for c in classes:
            m = lab == c
            ax.scatter(t[m], px[m], s=7, color=COLORS[c], label=c)
        ax.set_title(title, fontsize=10)
        ax.grid(alpha=0.3)
    axes[0].legend(loc="upper left", markerscale=2, ncol=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(rep / "12_fresh_regimes.png", dpi=110)


if __name__ == "__main__":
    main()
