"""Step 10d: trade the held-out test year with ALL three daily architectures.

Same procedure for every architecture:
  signals (10_make_signals.py --arch A) -> rules searched and frozen on validation
  (10_design_rules.py --arch A) -> traded once here.
Two views:
  A. each architecture with its OWN frozen rules (long-only ETF and idealized long/short)
  B. all architectures with the SAME fixed rules (spec exposure rule; the Transformer's frozen
     long-only rule), so differences come from the models alone.

Writes reports/10_architectures_test.json/.md, 10_architectures_equity.png, 10_trades_daily_{arch}_long_only.csv
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
from regime.train import classification_metrics
from regime.trading import Rule

design = import_module("10_design_rules")
FREQ = "daily"


def rule_from(d: dict) -> Rule:
    return Rule(d["direction"], d["exposure_map"], d["confirm"], d["min_confidence"], d["stop_loss"])


def rs(x: float) -> str:
    return f"Rs {x:,.0f}"


def main() -> None:
    cfg = load_config()
    tcfg, classes = cfg["trading"], cfg["sequence"]["classes"]
    rep, proc = ROOT / "reports", ROOT / cfg["data"]["processed_dir"]
    selected = json.loads((rep / "07_selection.json").read_text())["selected"]

    frozen = {a: json.loads((rep / f"10_rules_{FREQ}_{a}.json").read_text()) for a in ARCHITECTURES}
    signals = {a: pd.read_parquet(proc / f"signals_{FREQ}_{a}.parquet") for a in ARCHITECTURES}
    test = {a: s[s["split"] == "test"].reset_index(drop=True) for a, s in signals.items()}
    ref = test[selected]
    for a, t in test.items():   # identical decision bars and prices for every architecture
        assert (t["decision_time"].to_numpy() == ref["decision_time"].to_numpy()).all()
        assert np.allclose(t["price_next"], ref["price_next"])

    common_rules = {"spec rule": Rule("long_only", "spec", 1, 0.0, None),
                    f"{selected}'s frozen long-only rule": rule_from(frozen[selected]["directions"]["long_only"]["rule"])}

    out = {"evaluated_at": datetime.now().isoformat(timespec="seconds"), "freq": FREQ,
           "period": [str(ref["decision_time"].iloc[0].date()), str(ref["next_time"].iloc[-1].date())],
           "architectures": {}, "common_rules": {}, "benchmarks": {}}
    equity = {}
    for a in ARCHITECTURES:
        t = test[a]
        y_true = t["true_regime"].map({c: i for i, c in enumerate(classes)}).to_numpy()
        y_pred = t[[f"p_{c}" for c in classes]].to_numpy().argmax(axis=1)
        cls = classification_metrics(y_true, y_pred, classes)
        entry = {"classification": {k: cls[k] for k in ["accuracy", "macro_f1_present"]}, "own_rules": {}}
        for direction, d in frozen[a]["directions"].items():
            r = design.run_split(t, rule_from(d["rule"]), cfg, FREQ, keep_log=True)
            trades = pd.DataFrame(r.pop("trades"))
            eq = r.pop("equity")
            if direction == "long_only":
                trades.to_csv(rep / f"10_trades_{FREQ}_{a}_long_only.csv", index=False)
                equity[a] = eq
            entry["own_rules"][direction] = {**r, "validation_final_capital": d["validation"]["final_capital"],
                                             "validation_max_drawdown": d["validation"]["max_drawdown"]}
        out["architectures"][a] = entry
        for label, rule in common_rules.items():
            r = design.run_split(t, rule, cfg, FREQ)
            out["common_rules"].setdefault(label, {})[a] = r

    bh_sig = ref.copy()
    for c in classes:
        bh_sig[f"p_{c}"] = 1.0 if c == "bull" else 0.0
    bh = design.run_split(bh_sig, design.buy_and_hold_rule(), cfg, FREQ, keep_log=True)
    bh.pop("trades")
    equity["buy_and_hold"] = bh.pop("equity")
    cash_final = tcfg["initial_capital"] * (1 + tcfg["cash_yield_annual"]) ** (len(ref) / cfg["backtest"]["periods_per_year"][FREQ])
    out["benchmarks"] = {"buy_and_hold": bh, "cash_only_final": cash_final}
    (rep / "10_architectures_test.json").write_text(json.dumps(out, indent=2, default=str))
    with open(rep / "experiments.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": out["evaluated_at"], "step": "10_architectures_test",
                            "final_capital_own_long_only": {a: e["own_rules"]["long_only"]["final_capital"] for a, e in out["architectures"].items()},
                            "buy_and_hold_final": bh["final_capital"]}) + "\n")

    pct = lambda x: f"{100 * x:+.1f}%"
    names = {"lstm": "LSTM", "cnn_bilstm_attn": "CNN-BiLSTM-Attention", "transformer": "Transformer"}
    L = [f"# Step 10 — all three architectures trade the test year ({out['period'][0]} → {out['period'][1]})", "",
         f"Daily models, tuned, 5-seed ensembles. Start **{rs(tcfg['initial_capital'])}**. Same costs, same cash yield, same "
         "rule search on validation for every architecture; the test year is traded once.", "",
         "## A. Each architecture with its own validation-selected rules", "",
         "| Model | Test accuracy | Test macro-F1 | Instrument | Frozen rule | Validation final | **Test final** | Test return | Max DD | Trades | Costs |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a, e in out["architectures"].items():
        for direction, r in e["own_rules"].items():
            inst = "ETF + cash" if direction == "long_only" else "futures (idealized)"
            L.append(f"| {names[a]} | {e['classification']['accuracy']:.3f} | {e['classification']['macro_f1_present']:.3f} | {inst} | "
                     f"`{r['rule']['name']}` | {rs(r['validation_final_capital'])} | **{rs(r['final_capital'])}** | {pct(r['total_return'])} | "
                     f"{100 * r['max_drawdown']:.1f}% | {r['n_trades']} | {rs(r['total_costs'])} |")
    L.append(f"| *Buy & hold ETF* | – | – | ETF | – | {rs(frozen[selected]['benchmarks_validation']['buy_and_hold']['final_capital'])} | "
             f"{rs(bh['final_capital'])} | {pct(bh['total_return'])} | {100 * bh['max_drawdown']:.1f}% | 1 | {rs(bh['total_costs'])} |")
    L.append(f"| *Cash at 6%* | – | – | liquid fund | – | {rs(frozen[selected]['benchmarks_validation']['cash_only_final'])} | "
             f"{rs(cash_final)} | {pct(cash_final / tcfg['initial_capital'] - 1)} | 0.0% | 0 | – |")

    L += ["", "## B. Same rules for every architecture (differences come from the models only)", "",
          "| Rule | " + " | ".join(names[a] for a in ARCHITECTURES) + " |", "|---|" + "---|" * len(ARCHITECTURES)]
    for label, per in out["common_rules"].items():
        L.append(f"| {label} (`{common_rules[label].name}`) | " +
                 " | ".join(f"{rs(per[a]['final_capital'])} ({pct(per[a]['total_return'])}, DD {100 * per[a]['max_drawdown']:.1f}%)" for a in ARCHITECTURES) + " |")

    best = max(ARCHITECTURES, key=lambda a: out["architectures"][a]["own_rules"]["long_only"]["final_capital"])
    b = out["architectures"][best]["own_rules"]["long_only"]
    L += ["", "## Summary", "",
          f"- Most money left (own rules, ETF): **{names[best]} — {rs(b['final_capital'])}** ({pct(b['total_return'])}).",
          f"- Buy & hold: {rs(bh['final_capital'])}; cash at 6%: {rs(cash_final)}.",
          "- Profitable (ended above Rs 10,00,000): " + (", ".join(
              f"{names[a]} {d.replace('_', ' ')}" for a, e in out["architectures"].items() for d, r in e["own_rules"].items()
              if r["final_capital"] > tcfg["initial_capital"]) or "none") + ".",
          "- Beat buy & hold: " + (", ".join(
              f"{names[a]} {d.replace('_', ' ')}" for a, e in out["architectures"].items() for d, r in e["own_rules"].items()
              if r["final_capital"] > bh["final_capital"]) or "none") + ".",
          "", "Trade logs: `reports/10_trades_daily_<arch>_long_only.csv`. Long/short is idealized (spot prices, fractional contracts)."]
    (rep / "10_architectures_test.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))

    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.plot(equity["buy_and_hold"].index, equity["buy_and_hold"] / 1e5, color="k", lw=1.6, label="buy & hold ETF")
    for a, color in zip(ARCHITECTURES, ["#4c72b0", "#8e5bb5", "#dd8452"]):
        rule = out["architectures"][a]["own_rules"]["long_only"]["rule"]["name"]
        ax.plot(equity[a].index, equity[a] / 1e5, color=color, lw=1.8, label=f"{names[a]} — {rule}")
    ax.axhline(tcfg["initial_capital"] / 1e5, color="k", lw=0.6)
    ax.set_ylabel("Portfolio value (Rs lakh)")
    ax.set_title("Test year, Rs 10 lakh, long-only ETF with each model's own frozen rule")
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(rep / "10_architectures_equity.png", dpi=110)


if __name__ == "__main__":
    main()
