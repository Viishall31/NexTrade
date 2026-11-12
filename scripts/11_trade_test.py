"""Step 11b (Experiment 2): trade the test year ONCE with the frozen rulebook, for all three models.

Requires reports/11_rulebook_frozen.json. Writes reports/11_rulebook_test.json/.md,
reports/11_trades_{arch}_{version}.csv (every trade with its reason and the model's probabilities)
and reports/11_rulebook_equity.png.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.models import ARCHITECTURES
from regime.rulebook import RuleBook, run_rulebook_on

NAMES = {"lstm": "LSTM", "cnn_bilstm_attn": "CNN-BiLSTM-Attention", "transformer": "Transformer"}
VERSIONS = {"default": "Default rules, ETF", "tuned_cash": "Tuned rules, ETF", "tuned_short": "Tuned rules, futures (idealized)"}


def rs(x: float) -> str:
    return f"Rs {x:,.0f}"


def main() -> None:
    cfg = load_config()
    tcfg, classes = cfg["trading"], cfg["sequence"]["classes"]
    rep, proc = ROOT / "reports", ROOT / cfg["data"]["processed_dir"]
    frozen = json.loads((rep / "11_rulebook_frozen.json").read_text())

    results, equity, trades_all = {}, {}, {}
    for arch in ARCHITECTURES:
        sig = pd.read_parquet(proc / f"signals_daily_{arch}.parquet")
        test = sig[sig["split"] == "test"].reset_index(drop=True)
        results[arch] = {}
        for version in VERSIONS:
            fz = frozen["architectures"][arch][version]
            rb = RuleBook(**{k: v for k, v in fz["rulebook"].items() if k != "name"})
            r = run_rulebook_on(test, rb, cfg, keep_log=True)
            trades = pd.DataFrame(r.pop("trades"))
            trades.to_csv(rep / f"11_trades_{arch}_{version}.csv", index=False)
            trades_all[(arch, version)] = trades
            equity[(arch, version)] = r.pop("equity")
            results[arch][version] = {**r, "validation_final_capital": fz["validation"]["final_capital"]}

    bh_sig = test.copy()
    for c in classes:
        bh_sig[f"p_{c}"] = 1.0 if c == "bull" else 0.0
    bh = run_rulebook_on(bh_sig, RuleBook(buy_threshold=0.5, confirm_days=1, sizing="full", stop_loss=None, cooldown_days=0), cfg, keep_log=True)
    bh.pop("trades")
    equity["buy_and_hold"] = bh.pop("equity")
    years = len(test) / cfg["backtest"]["periods_per_year"]["daily"]
    cash_final = tcfg["initial_capital"] * (1 + tcfg["cash_yield_annual"]) ** years
    period = [str(test["decision_time"].iloc[0].date()), str(test["next_time"].iloc[-1].date())]

    out = {"evaluated_at": datetime.now().isoformat(timespec="seconds"), "period": period, "results": results,
           "buy_and_hold": bh, "cash_only_final": cash_final}
    (rep / "11_rulebook_test.json").write_text(json.dumps(out, indent=2, default=str))
    with open(rep / "experiments.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": out["evaluated_at"], "step": "11_rulebook_test",
                            "final_capital": {f"{a}/{v}": results[a][v]["final_capital"] for a in results for v in results[a]},
                            "buy_and_hold_final": bh["final_capital"], "cash_final": cash_final}) + "\n")

    start = tcfg["initial_capital"]
    pct = lambda x: f"{100 * x:+.1f}%"
    L = [f"# Experiment 2 — rulebook trading on the test year ({period[0]} → {period[1]})", "",
         f"Rules: `11_rulebook.md` (frozen on validation). Start **{rs(start)}** for every model and version.", "",
         "| Model | Version | Parameters | Validation final | **Test: amount left** | **Profit / loss** | of which cash interest | Trading P&L (excl. interest) | Max DD | Trades | Costs | Invested |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for arch in ARCHITECTURES:
        for version, label in VERSIONS.items():
            r = results[arch][version]
            L.append(f"| {NAMES[arch]} | {label} | `{r['rulebook']['name']}` | {rs(r['validation_final_capital'])} | "
                     f"**{rs(r['final_capital'])}** | **{rs(r['net_profit'])} ({pct(r['total_return'])})** | {rs(r['interest_earned'])} | "
                     f"{rs(r['net_profit'] - r['interest_earned'])} | {100 * r['max_drawdown']:.1f}% | "
                     f"{r['n_trades']} | {rs(r['total_costs'])} | {100 * r['time_in_market']:.0f}% |")
    L.append(f"| *Buy & hold ETF* | | | | {rs(bh['final_capital'])} | {rs(bh['net_profit'])} ({pct(bh['total_return'])}) | "
             f"{rs(bh['interest_earned'])} | {rs(bh['net_profit'] - bh['interest_earned'])} | "
             f"{100 * bh['max_drawdown']:.1f}% | 1 | {rs(bh['total_costs'])} | 100% |")
    L.append(f"| *Cash at 6%* | | | | {rs(cash_final)} | {rs(cash_final - start)} ({pct(cash_final / start - 1)}) | {rs(cash_final - start)} | Rs 0 | 0.0% | 0 | – | 0% |")

    profitable = [f"{NAMES[a]} ({VERSIONS[v]})" for a in results for v in results[a] if results[a][v]["final_capital"] > start]
    beat_bh = [f"{NAMES[a]} ({VERSIONS[v]})" for a in results for v in results[a] if results[a][v]["final_capital"] > bh["final_capital"]]
    beat_cash = [f"{NAMES[a]} ({VERSIONS[v]})" for a in results for v in results[a] if results[a][v]["final_capital"] > cash_final]
    L += ["", "## Verdict", "",
          f"- Ended with a profit (above {rs(start)}): {', '.join(profitable) or 'none'}",
          f"- Beat buy & hold ({rs(bh['final_capital'])}): {', '.join(beat_bh) or 'none'}",
          f"- Beat cash at 6% ({rs(cash_final)}): {', '.join(beat_cash) or 'none'}"]

    for arch in ARCHITECTURES:
        t = trades_all[(arch, "default")]
        L += ["", f"## Trade log — {NAMES[arch]}, default rules (ETF)", ""]
        if t.empty:
            L.append("No trades: the BUY condition was never met.")
            continue
        L += ["| Date | Action | Nifty | Why | Portfolio before |", "|---|---|---|---|---|"]
        for _, row in t.iterrows():
            L.append(f"| {pd.Timestamp(row['time']).date()} | {row['action']} | {row['price']:,.0f} | {row['reason'].split(': ', 1)[-1]} | {rs(row['equity_before'])} |")
    (rep / "11_rulebook_test.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), sharey=True)
    for ax, arch in zip(axes, ARCHITECTURES):
        ax.plot(equity["buy_and_hold"].index, equity["buy_and_hold"] / 1e5, color="k", lw=1.3, label="buy & hold ETF")
        for version, color, ls in [("default", "#c0392b", "-"), ("tuned_cash", "#2471a3", "-"), ("tuned_short", "#27ae60", ":")]:
            e = equity[(arch, version)]
            ax.plot(e.index, e / 1e5, color=color, ls=ls, lw=1.6, label=VERSIONS[version])
        ax.axhline(start / 1e5, color="k", lw=0.6)
        ax.set_title(NAMES[arch])
        ax.grid(alpha=0.3)
        ax.tick_params(axis="x", rotation=30)
    axes[0].set_ylabel("Portfolio value (Rs lakh)")
    axes[0].legend(loc="lower left", fontsize=8)
    fig.suptitle(f"Experiment 2: rulebook trading, test year {period[0]} → {period[1]}, start Rs 10 lakh")
    fig.tight_layout()
    fig.savefig(rep / "11_rulebook_equity.png", dpi=110)


if __name__ == "__main__":
    main()
