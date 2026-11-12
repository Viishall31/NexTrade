"""Step 10b: search trading rules on VALIDATION signals only, then freeze the winners.

For each direction (long_only, long_short) every rule in the grid is simulated from
Rs 10,00,000 over the validation period (Jan 2022 - Apr 2024). Winner = highest final capital
among rules whose max drawdown is no worse than buy & hold's. Frozen to
reports/10_rules_{freq}_{arch}.json (refuses to overwrite) before any test trading.

Usage: python scripts/10_design_rules.py --freq daily|15min [--arch ...]   (default arch = the selected one)
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.trading import Rule, rule_grid, simulate


def run_split(sig: pd.DataFrame, rule: Rule, cfg: dict, freq: str, keep_log: bool = False) -> dict:
    classes = cfg["sequence"]["classes"]
    return simulate(sig[[f"p_{c}" for c in classes]].to_numpy(), sig["price_now"].to_numpy(), sig["price_next"].to_numpy(),
                    pd.DatetimeIndex(sig["decision_time"]), pd.DatetimeIndex(sig["next_time"]), rule, cfg["trading"],
                    classes, cfg["backtest"]["periods_per_year"][freq], keep_log)


def buy_and_hold_rule() -> Rule:
    return Rule("long_only", "risk_off", 1, 0.0, None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freq", choices=["daily", "15min"], required=True)
    ap.add_argument("--arch", choices=["lstm", "cnn_bilstm_attn", "transformer"], default=None)
    args = ap.parse_args()
    cfg = load_config()
    tcfg, classes = cfg["trading"], cfg["sequence"]["classes"]
    rep = ROOT / "reports"
    arch = args.arch or json.loads((rep / "07_selection.json").read_text())["selected"]
    out = rep / f"10_rules_{args.freq}_{arch}.json"
    if out.exists():
        raise SystemExit(f"{out.name} already exists -- rules are frozen. Delete it deliberately to redo.")

    sig = pd.read_parquet(ROOT / cfg["data"]["processed_dir"] / f"signals_{args.freq}_{arch}.parquet")
    val = sig[sig["split"] == "val"].reset_index(drop=True)

    # Buy & hold: all-bull signal through the long-only simulator (one purchase, costs included).
    bh_sig = val.copy()
    for c in classes:
        bh_sig[f"p_{c}"] = 1.0 if c == "bull" else 0.0
    bh = run_split(bh_sig, buy_and_hold_rule(), cfg, args.freq)
    periods = len(val) / cfg["backtest"]["periods_per_year"][args.freq]
    cash_only = tcfg["initial_capital"] * (1 + tcfg["cash_yield_annual"]) ** periods

    decision = {"decided_at": datetime.now().isoformat(timespec="seconds"), "freq": args.freq, "arch": arch,
                "validation_period": [str(val["decision_time"].iloc[0]), str(val["next_time"].iloc[-1])],
                "selection_rule": "max final capital on validation, subject to max drawdown >= buy & hold's (i.e. no deeper)",
                "benchmarks_validation": {"buy_and_hold": {k: bh[k] for k in bh if k != "rule"}, "cash_only_final": cash_only},
                "directions": {}}
    L = [f"# Step 10 — trading rule search ({args.freq}, {arch}), validation {decision['validation_period'][0][:10]} → "
         f"{decision['validation_period'][1][:10]}", "",
         f"Start Rs {tcfg['initial_capital']:,.0f}. Buy & hold ends at Rs {bh['final_capital']:,.0f} "
         f"(max DD {100 * bh['max_drawdown']:.1f}%); cash at {100 * tcfg['cash_yield_annual']:.0f}% ends at Rs {cash_only:,.0f}."]

    for direction in ["long_only", "long_short"]:
        rows = []
        for rule in rule_grid(tcfg, args.freq, direction):
            r = run_split(val, rule, cfg, args.freq)
            rows.append({"rule": rule.name, **{k: v for k, v in r.items() if k != "rule"}, "_rule": rule})
        df = pd.DataFrame(rows).sort_values("final_capital", ascending=False)
        eligible = df[df["max_drawdown"] >= bh["max_drawdown"]]
        pool, constrained = (eligible, True) if len(eligible) else (df, False)
        best = pool.iloc[0]
        rule = best["_rule"]
        decision["directions"][direction] = {
            "instrument": tcfg["instruments"][direction]["label"],
            "rule": rule.to_dict(),
            "validation": {k: best[k] for k in df.columns if k not in ("rule", "_rule")},
            "drawdown_constraint_satisfied": constrained,
            "n_rules_searched": len(df), "n_rules_eligible": len(eligible),
            "beats_buy_and_hold_on_validation": bool(best["final_capital"] > bh["final_capital"]),
            "rank_of_spec_rule": int((df["rule"].reset_index(drop=True) ==
                                      ("spec|confirm1|conf0|nostop" if direction == "long_only" else "ls_spec|confirm1|conf0|nostop")).idxmax()) + 1,
        }
        L += ["", f"## {direction} — {tcfg['instruments'][direction]['label']}", "",
              f"{len(df)} rules searched, {len(eligible)} with drawdown no worse than buy & hold. "
              f"**Selected: `{rule.name}`**" + ("" if constrained else " (no rule met the drawdown constraint; best overall used)"), "",
              "| Rank | Rule | Final capital | Return | Max DD | Sharpe | Trades | Costs | Time in market |",
              "|---|---|---|---|---|---|---|---|---|"]
        for rank, (_, r) in enumerate(df.head(10).iterrows(), 1):
            mark = " ✅" if r["rule"] == rule.name else ""
            L.append(f"| {rank} | `{r['rule']}`{mark} | Rs {r['final_capital']:,.0f} | {100 * r['total_return']:.1f}% | "
                     f"{100 * r['max_drawdown']:.1f}% | {r['sharpe']:.2f} | {r['n_trades']} | Rs {r['total_costs']:,.0f} | "
                     f"{100 * r['time_in_market']:.0f}% |")
        L.append(f"| – | *buy & hold* | Rs {bh['final_capital']:,.0f} | {100 * bh['total_return']:.1f}% | {100 * bh['max_drawdown']:.1f}% | "
                 f"{bh['sharpe']:.2f} | {bh['n_trades']} | Rs {bh['total_costs']:,.0f} | 100% |")
        print(f"{arch} {direction}: selected {rule.name}  final Rs {best['final_capital']:,.0f}  DD {100 * best['max_drawdown']:.1f}%  "
              f"(buy & hold Rs {bh['final_capital']:,.0f}, DD {100 * bh['max_drawdown']:.1f}%)")

    out.write_text(json.dumps(decision, indent=2, default=str))
    (rep / f"10_rules_{args.freq}_{arch}.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
