"""Step 11a (Experiment 2): write the rulebook and freeze its parameters on VALIDATION only.

For each daily architecture (5-seed ensemble probabilities from 10_make_signals.py):
  - "default": the a-priori parameters from config (no tuning)
  - "tuned_cash" / "tuned_short": best of the grid on validation (max final capital, drawdown no
    worse than buy & hold), separately for the ETF (cash) and futures (short) versions
Frozen to reports/11_rulebook_frozen.json (refuses to overwrite); rulebook text to reports/11_rulebook.md.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.models import ARCHITECTURES
from regime.rulebook import RuleBook, rulebook_grid, run_rulebook_on

NAMES = {"lstm": "LSTM", "cnn_bilstm_attn": "CNN-BiLSTM-Attention", "transformer": "Transformer"}


def describe(rb: RuleBook) -> str:
    size = (f"100% if P(bull) ≥ {rb.buy_threshold + rb.strong_margin:.2f}, else 50%" if rb.sizing == "scaled" else "always 100%")
    stop = f"{100 * rb.stop_loss:g}% trailing stop" if rb.stop_loss else "no stop-loss"
    sell = "move to cash" if rb.on_sell == "cash" else "go short (futures)"
    return (f"BUY when P(bull) ≥ {rb.buy_threshold:g} for {rb.confirm_days} day(s) [{size}]; "
            f"SELL ({sell}) when P(bear)+P(high-vol) ≥ {rb.sell_threshold:g} for {rb.confirm_days} day(s); "
            f"{stop}; wait {rb.cooldown_days} day(s) after an exit")


def main() -> None:
    cfg = load_config()
    rcfg, tcfg, classes = cfg["rulebook"], cfg["trading"], cfg["sequence"]["classes"]
    rep, proc = ROOT / "reports", ROOT / cfg["data"]["processed_dir"]
    out = rep / "11_rulebook_frozen.json"
    if out.exists():
        raise SystemExit(f"{out.name} already exists -- the rulebook is frozen. Delete it deliberately to redo.")

    default = RuleBook(**rcfg["default"])
    grid = rulebook_grid(rcfg["grid"], rcfg["default"]["strong_margin"])
    frozen = {"decided_at": datetime.now().isoformat(timespec="seconds"),
              "note": "Experiment 2, designed after the Step 10 test results were seen; parameters chosen on validation only.",
              "selection_rule": "max validation final capital, max drawdown no worse than buy & hold",
              "default": default.to_dict(), "grid_size": len(grid), "architectures": {}}
    tables = []
    for arch in ARCHITECTURES:
        sig = pd.read_parquet(proc / f"signals_daily_{arch}.parquet")
        val = sig[sig["split"] == "val"].reset_index(drop=True)
        bh_sig = val.copy()
        for c in classes:
            bh_sig[f"p_{c}"] = 1.0 if c == "bull" else 0.0
        bh = run_rulebook_on(bh_sig, RuleBook(buy_threshold=0.5, confirm_days=1, sizing="full", stop_loss=None, cooldown_days=0), cfg)

        rows = [{"rb": rb, **{k: v for k, v in run_rulebook_on(val, rb, cfg).items() if k != "rulebook"}} for rb in grid]
        df = pd.DataFrame(rows)
        entry = {"validation_buy_and_hold": {k: bh[k] for k in ["final_capital", "max_drawdown"]},
                 "default": {"rulebook": default.to_dict(),
                             "validation": {k: v for k, v in run_rulebook_on(val, default, cfg).items() if k != "rulebook"}}}
        for on_sell in ["cash", "short"]:
            sub = df[df["rb"].map(lambda r: r.on_sell == on_sell)].sort_values("final_capital", ascending=False)
            ok = sub[sub["max_drawdown"] >= bh["max_drawdown"]]
            best = (ok if len(ok) else sub).iloc[0]
            entry[f"tuned_{on_sell}"] = {"rulebook": best["rb"].to_dict(), "drawdown_constraint_satisfied": bool(len(ok)),
                                         "validation": {k: best[k] for k in df.columns if k != "rb"}}
        frozen["architectures"][arch] = entry
        d, tc, ts = entry["default"]["validation"], entry["tuned_cash"]["validation"], entry["tuned_short"]["validation"]
        print(f"{NAMES[arch]:22s} validation: default Rs {d['final_capital']:,.0f} | tuned ETF Rs {tc['final_capital']:,.0f} "
              f"({entry['tuned_cash']['rulebook']['name']}) | tuned futures Rs {ts['final_capital']:,.0f} | buy&hold Rs {bh['final_capital']:,.0f}")
        tables.append((arch, entry))
    out.write_text(json.dumps(frozen, indent=2, default=str))

    r = rcfg["default"]
    L = ["# Trading rulebook (Experiment 2)", "",
         "Signals come from each trained model (LSTM, CNN-BiLSTM-Attention, Transformer; daily, 5-seed ensemble). "
         "At every trading day's close the model outputs the probability of each regime for the **next** day: "
         "P(bull), P(sideways), P(bear), P(high-vol). They sum to 1.", "",
         "## The rules", "",
         "| # | Rule | Condition | Action |", "|---|---|---|---|",
         f"| 1 | **BUY** | P(bull) ≥ {r['buy_threshold']} on {r['confirm_days']} consecutive days, you hold no position, and no cooldown is active | "
         f"Buy the Nifty 50 ETF: **100%** of capital if P(bull) ≥ {r['buy_threshold'] + r['strong_margin']:.2f}, otherwise **50%** |",
         f"| 2 | **ADD / REDUCE** | Already holding and BUY condition still true | Move to 100% when P(bull) ≥ {r['buy_threshold'] + r['strong_margin']:.2f}, to 50% when it falls below |",
         f"| 3 | **SELL** | P(bear) + P(high-vol) ≥ {r['sell_threshold']} on {r['confirm_days']} consecutive days | Sell everything, move to cash (SELL beats BUY if both fire) |",
         "| 4 | **HOLD** | Neither BUY nor SELL condition | Do nothing. A sideways forecast alone never causes a trade |",
         f"| 5 | **STOP-LOSS** | Portfolio value falls {int(100 * r['stop_loss'])}% below its highest value since the position was opened | Sell everything at the next close |",
         f"| 6 | **COOLDOWN** | After any sell | No new BUY for {r['cooldown_days']} trading days |",
         "| 7 | **FRESH SIGNAL** | After a stop-loss | No new BUY until P(bull) first drops below the threshold and then meets rule 1 again |",
         "", "Futures version (idealized): rule 3 opens a **short** instead of moving to cash (50%/100% by the same margin), "
         "and a BUY signal first **covers** the short.", "",
         "## Execution and costs", "",
         f"- Start with Rs {tcfg['initial_capital']:,.0f}. Decisions and trades at the day's close. One action per day.",
         f"- ETF: {100 * tcfg['instruments']['long_only']['cost_rate']:.2f}% of traded value per buy/sell + Rs {tcfg['instruments']['long_only']['fixed_cost_per_sell']} per sell.",
         f"- Futures: {100 * tcfg['instruments']['long_short']['cost_rate']:.2f}% per side + {100 * tcfg['instruments']['long_short']['roll_cost_rate']:.2f}% monthly roll.",
         f"- Uninvested cash earns {100 * tcfg['cash_yield_annual']:.0f}% p.a. (liquid fund).", "",
         "## Parameters", "",
         f"**Default (fixed in advance, not tuned):** {describe(default)}.", "",
         f"**Tuned:** {len(grid)} combinations searched on validation (Jan 2022 – Apr 2024) per model: "
         + ", ".join(f"{k} {v}" for k, v in rcfg["grid"].items())
         + ". Chosen = most money at the end of validation with drawdown no worse than buy & hold. Frozen before the test year.", "",
         "| Model | Version | Parameters | Validation: final capital | Validation: max DD |", "|---|---|---|---|---|"]
    for arch, e in tables:
        for key, label in [("default", "default"), ("tuned_cash", "tuned, ETF"), ("tuned_short", "tuned, futures")]:
            rb = RuleBook(**{k: v for k, v in e[key]["rulebook"].items() if k != "name"})
            v = e[key]["validation"]
            L.append(f"| {NAMES[arch]} | {label} | {describe(rb)} | Rs {v['final_capital']:,.0f} | {100 * v['max_drawdown']:.1f}% |")
        L.append(f"| {NAMES[arch]} | *buy & hold* | – | Rs {e['validation_buy_and_hold']['final_capital']:,.0f} | "
                 f"{100 * e['validation_buy_and_hold']['max_drawdown']:.1f}% |")
    L += ["", "Experiment 2 was designed after the Step 10 test-year results were seen (rules 4, 6 and 7 address the whipsaw found "
          "there). Parameters were chosen on validation only and the test year is traded once (`11_rulebook_test.md`)."]
    (rep / "11_rulebook.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
