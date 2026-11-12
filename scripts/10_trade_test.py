"""Step 10c: trade the held-out test year ONCE with the frozen rules, starting from Rs 10,00,000.

Requires reports/10_rules_{daily,15min}_{selected arch}.json (frozen on validation).
For the three-architecture comparison see 10_compare_architectures.py.
The recommended system is picked from the frozen long-only systems by VALIDATION final capital,
before looking at test results; long/short futures systems are reported as idealized comparisons.

Writes reports/10_test_trading.json/.md, reports/10_trades_{system}.csv, reports/10_test_equity.png
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.trading import Rule

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

design = import_module("10_design_rules")


def rs(x: float) -> str:
    return f"Rs {x:,.0f}"


def main() -> None:
    cfg = load_config()
    tcfg, classes = cfg["trading"], cfg["sequence"]["classes"]
    rep, proc = ROOT / "reports", ROOT / cfg["data"]["processed_dir"]

    arch = json.loads((rep / "07_selection.json").read_text())["selected"]
    frozen = {f: json.loads((rep / f"10_rules_{f}_{arch}.json").read_text()) for f in ["daily", "15min"]}
    systems = {}
    for freq, fz in frozen.items():
        for direction, d in fz["directions"].items():
            r = d["rule"]
            systems[f"{freq}_{direction}"] = {
                "freq": freq, "direction": direction, "instrument": d["instrument"],
                "rule": Rule(r["direction"], r["exposure_map"], r["confirm"], r["min_confidence"], r["stop_loss"]),
                "validation_final": d["validation"]["final_capital"], "validation_dd": d["validation"]["max_drawdown"]}
    recommended = max((k for k, s in systems.items() if s["direction"] == "long_only"), key=lambda k: systems[k]["validation_final"])

    sigs = {f: pd.read_parquet(proc / f"signals_{f}_{arch}.parquet") for f in frozen}
    test = {f: s[s["split"] == "test"].reset_index(drop=True) for f, s in sigs.items()}

    results, equity = {}, {}
    for name, s in systems.items():
        r = design.run_split(test[s["freq"]], s["rule"], cfg, s["freq"], keep_log=True)
        trades = pd.DataFrame(r.pop("trades"))
        trades.to_csv(rep / f"10_trades_{name}.csv", index=False)
        equity[name] = r.pop("equity")
        results[name] = {**r, "instrument": s["instrument"], "validation_final_capital": s["validation_final"],
                         "validation_max_drawdown": s["validation_dd"]}

    # Benchmarks on the daily test prices
    d = test["daily"]
    bh_sig = d.copy()
    for c in classes:
        bh_sig[f"p_{c}"] = 1.0 if c == "bull" else 0.0
    bh = design.run_split(bh_sig, design.buy_and_hold_rule(), cfg, "daily", keep_log=True)
    bh.pop("trades")
    equity["buy_and_hold"] = bh.pop("equity")
    spec = design.run_split(d, Rule("long_only", "spec", 1, 0.0, None), cfg, "daily", keep_log=True)
    spec.pop("trades")
    equity["spec_rule_daily"] = spec.pop("equity")
    years = len(d) / cfg["backtest"]["periods_per_year"]["daily"]
    cash_final = tcfg["initial_capital"] * (1 + tcfg["cash_yield_annual"]) ** years
    period = [str(d["decision_time"].iloc[0].date()), str(d["next_time"].iloc[-1].date())]

    rec = results[recommended]
    monthly = equity[recommended].resample("ME").last()
    monthly_tbl = pd.DataFrame({"equity": monthly, "month_pnl": monthly.diff().fillna(monthly.iloc[0] - tcfg["initial_capital"])})
    bh_monthly = equity["buy_and_hold"].resample("ME").last()

    out = {"evaluated_at": datetime.now().isoformat(timespec="seconds"), "period": period, "recommended": recommended,
           "recommendation_basis": "highest validation final capital among frozen long-only systems (decided before this run)",
           "systems": results, "benchmarks": {"buy_and_hold": bh, "spec_rule_daily": spec, "cash_only_final": cash_final}}
    (rep / "10_test_trading.json").write_text(json.dumps(out, indent=2, default=str))
    with open(rep / "experiments.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": out["evaluated_at"], "step": "10_test_trading", "recommended": recommended,
                            "final_capital": {k: v["final_capital"] for k, v in results.items()},
                            "buy_and_hold_final": bh["final_capital"]}) + "\n")

    pct = lambda x: f"{100 * x:+.1f}%"
    L = [f"# Step 10 — trading the held-out test year ({period[0]} → {period[1]})", "",
         f"Start: **{rs(tcfg['initial_capital'])}**. Rules and the recommended system were frozen on validation "
         f"(Jan 2022 – Apr 2024) before this run. Costs: long-only {100 * tcfg['instruments']['long_only']['cost_rate']:.2f}% per side "
         f"+ Rs {tcfg['instruments']['long_only']['fixed_cost_per_sell']} per sell; futures {100 * tcfg['instruments']['long_short']['cost_rate']:.2f}% per side "
         f"+ monthly roll. Idle cash earns {100 * tcfg['cash_yield_annual']:.0f}% p.a.", "",
         f"## Recommended system: {recommended.replace('_', ' ')} — `{rec['rule']['name']}`", "",
         f"- **Amount at the end: {rs(rec['final_capital'])}** (net {rs(rec['net_profit'])}, {pct(rec['total_return'])})",
         f"- Buy & hold the ETF instead: {rs(bh['final_capital'])} ({pct(bh['total_return'])}); cash at 6%: {rs(cash_final)}",
         f"- Max drawdown {100 * rec['max_drawdown']:.1f}% ({rs(rec['max_drawdown_rupees'])}) vs buy & hold {100 * bh['max_drawdown']:.1f}% ({rs(bh['max_drawdown_rupees'])})",
         f"- {rec['n_trades']} trades, costs {rs(rec['total_costs'])}, interest on idle cash {rs(rec['interest_earned'])}, "
         f"invested {100 * rec['time_in_market']:.0f}% of the time", "",
         "## All frozen systems vs benchmarks", "",
         "| System | Rule | Validation final | **Test final** | Test return | Max DD | Sharpe | Trades | Costs |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, r in results.items():
        tag = " (idealized)" if "long_short" in name else ""
        bold = "**" if name == recommended else ""
        L.append(f"| {bold}{name}{tag}{bold} | `{r['rule']['name']}` | {rs(r['validation_final_capital'])} | **{rs(r['final_capital'])}** | "
                 f"{pct(r['total_return'])} | {100 * r['max_drawdown']:.1f}% | {r['sharpe']:.2f} | {r['n_trades']} | {rs(r['total_costs'])} |")
    L.append(f"| *buy & hold ETF* | – | {rs(frozen['daily']['benchmarks_validation']['buy_and_hold']['final_capital'])} | {rs(bh['final_capital'])} | "
             f"{pct(bh['total_return'])} | {100 * bh['max_drawdown']:.1f}% | {bh['sharpe']:.2f} | {bh['n_trades']} | {rs(bh['total_costs'])} |")
    L.append(f"| *spec exposure rule (Step 7), daily* | `spec|confirm1|conf0|nostop` | – | {rs(spec['final_capital'])} | "
             f"{pct(spec['total_return'])} | {100 * spec['max_drawdown']:.1f}% | {spec['sharpe']:.2f} | {spec['n_trades']} | {rs(spec['total_costs'])} |")
    L.append(f"| *cash at 6%* | – | {rs(frozen['daily']['benchmarks_validation']['cash_only_final'])} | {rs(cash_final)} | "
             f"{pct(cash_final / tcfg['initial_capital'] - 1)} | 0.0% | – | 0 | – |")
    L += ["", f"## Month by month — {recommended}", "", "| Month end | Equity | Month P&L | Buy & hold equity |", "|---|---|---|---|"]
    for ts, row in monthly_tbl.iterrows():
        L.append(f"| {ts.strftime('%b %Y')} | {rs(row['equity'])} | {rs(row['month_pnl'])} | {rs(bh_monthly.get(ts, np.nan))} |")
    L += ["", f"Trade-by-trade logs: `reports/10_trades_<system>.csv`.",
          "Long/short systems are idealized: spot index prices instead of futures prices, fractional contracts "
          "(one real Nifty lot is worth more than Rs 10 lakh), no margin calls."]
    (rep / "10_test_trading.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))

    fig, ax = plt.subplots(figsize=(13, 6))
    styles = {"buy_and_hold": dict(color="k", lw=1.6, label="buy & hold ETF"),
              "spec_rule_daily": dict(color="#999", lw=1, ls="--", label="spec exposure rule (daily)")}
    palette = {"daily_long_only": "#c0392b", "15min_long_only": "#e67e22", "daily_long_short": "#2471a3", "15min_long_short": "#76d7c4"}
    for name, eq in equity.items():
        series = eq.resample("D").last().dropna() / 1e5
        if name in styles:
            kw = styles[name]
        else:
            kw = dict(color=palette[name], lw=2.2 if name == recommended else 1.2, ls="-" if "long_only" in name else ":",
                      label=name + (" (recommended)" if name == recommended else " (idealized)" if "long_short" in name else ""))
        ax.plot(series.index, series.to_numpy(), **kw)
    ax.axhline(tcfg["initial_capital"] / 1e5, color="k", lw=0.6)
    ax.set_ylabel("Portfolio value (Rs lakh)")
    ax.set_title(f"Test year trading from Rs 10 lakh ({period[0]} → {period[1]})")
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(rep / "10_test_equity.png", dpi=110)


if __name__ == "__main__":
    main()
