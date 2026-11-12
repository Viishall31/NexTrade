"""Read-only data layer for the dashboard (spec EI-5): reports, processed data, frozen models' signals.

Nothing is trained or re-selected here. Equity curves are re-simulated from the saved model signals and
the frozen rules (deterministic, a few milliseconds), because the reports store only summary numbers.
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from regime.config import load_config
from regime.rulebook import RuleBook, run_rulebook_on
from regime.trading import Rule, simulate

REPORTS, PROC = ROOT / "reports", ROOT / "data" / "processed"
ARCHS = ["lstm", "cnn_bilstm_attn", "transformer"]
NAMES = {"lstm": "LSTM", "cnn_bilstm_attn": "CNN-BiLSTM-Attention", "transformer": "Transformer"}
REGIMES = ["bull", "sideways", "bear", "high_vol"]          # display order (top to bottom)
REGIME_LABEL = {"bull": "Bull", "sideways": "Sideways", "bear": "Bear", "high_vol": "High volatility"}
PERIODS = {"test": "Test year (May 2024 – Apr 2025)", "fresh": "Fresh data (Apr 2025 – Sep 2026)"}
SYSTEMS = {
    "exp1_long_only": "Exp 1 rules · ETF",
    "exp2_default": "Exp 2 rulebook (default) · ETF",
    "exp2_tuned_cash": "Exp 2 rulebook (tuned) · ETF",
    "exp1_long_short": "Exp 1 rules · futures (idealized)",
    "exp2_tuned_short": "Exp 2 rulebook (tuned) · futures (idealized)",
}


@st.cache_data
def config() -> dict:
    return load_config()


@st.cache_data
def report(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


@st.cache_data
def report_text(name: str) -> str:
    return (REPORTS / name).read_text(encoding="utf-8")


@st.cache_data
def daily_regimes() -> pd.DataFrame:
    """Daily close + frozen-HMM regime, Feb 2016 – Sep 2026 (vendor data, then yfinance after 7 Apr 2025)."""
    feats = pd.read_parquet(PROC / "features_daily_fresh.parquet")[["close", "split"]]
    labels = pd.read_parquet(PROC / "labels_daily_fresh.parquet")[["regime", "p_bull", "p_bear", "p_sideways", "p_high_vol"]]
    return feats.join(labels)


@st.cache_data
def signals(arch: str, period: str) -> pd.DataFrame:
    """Seed-ensemble probabilities; one row per decision day. period: val | test | fresh."""
    if period == "fresh":
        s = pd.read_parquet(PROC / f"signals_daily_{arch}_fresh.parquet")
    else:
        s = pd.read_parquet(PROC / f"signals_daily_{arch}.parquet")
        s = s[s["split"] == period]
    s = s.reset_index(drop=True)
    classes = config()["sequence"]["classes"]
    p = s[[f"p_{c}" for c in classes]].to_numpy()
    s["predicted"] = np.asarray(classes)[p.argmax(axis=1)]
    s["confidence"] = p.max(axis=1)
    return s


@st.cache_data
def predictions(arch: str) -> pd.DataFrame:
    """Predicted regime indexed by the day it is a forecast FOR (validation, test and fresh periods)."""
    return pd.concat([signals(arch, p) for p in ["val", "test", "fresh"]]).set_index("next_time")


def _frozen_system(arch: str, system: str):
    if system.startswith("exp1"):
        d = report(f"10_rules_daily_{arch}.json")["directions"][system.replace("exp1_", "")]["rule"]
        return Rule(d["direction"], d["exposure_map"], d["confirm"], d["min_confidence"], d["stop_loss"])
    d = report("11_rulebook_frozen.json")["architectures"][arch][system.replace("exp2_", "")]["rulebook"]
    return RuleBook(**{k: v for k, v in d.items() if k != "name"})


@st.cache_data
def trade(arch: str, system: str, period: str) -> dict:
    cfg = config()
    sig, classes = signals(arch, period), cfg["sequence"]["classes"]
    rule = _frozen_system(arch, system)
    if isinstance(rule, Rule):
        res = simulate(sig[[f"p_{c}" for c in classes]].to_numpy(), sig["price_now"].to_numpy(), sig["price_next"].to_numpy(),
                       pd.DatetimeIndex(sig["decision_time"]), pd.DatetimeIndex(sig["next_time"]), rule, cfg["trading"],
                       classes, 252, keep_log=True)
    else:
        res = run_rulebook_on(sig, rule, cfg, keep_log=True)
    res["trades"] = pd.DataFrame(res["trades"])
    res["rule_name"] = (res.get("rule") or res.get("rulebook"))["name"]
    return res


@st.cache_data
def benchmarks(period: str) -> dict:
    cfg = config()
    sig = signals("transformer", period).copy()
    for c in cfg["sequence"]["classes"]:
        sig[f"p_{c}"] = 1.0 if c == "bull" else 0.0
    bh = run_rulebook_on(sig, RuleBook(buy_threshold=0.5, confirm_days=1, sizing="full", stop_loss=None, cooldown_days=0), cfg, keep_log=True)
    start, y = cfg["trading"]["initial_capital"], cfg["trading"]["cash_yield_annual"]
    days = np.arange(1, len(sig) + 1)
    cash = pd.Series(start * (1 + y) ** (days / 252), index=pd.DatetimeIndex(sig["next_time"]))
    return {"buy_and_hold": bh, "cash": cash}


@st.cache_data
def replay_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    db = ROOT / config()["replay"]["db"]
    with sqlite3.connect(db) as con:
        preds = pd.read_sql("select * from predictions_test", con, parse_dates=["timestamp"])
        days = pd.read_sql("select * from daily_labels_test", con, parse_dates=["date"])
    return preds, days
