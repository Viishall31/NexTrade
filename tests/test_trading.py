import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.config import load_config
from regime.trading import Rule, rule_grid, simulate

CLASSES = ["bull", "bear", "sideways", "high_vol"]


@pytest.fixture(scope="module")
def tcfg():
    return load_config()["trading"]


def onehot(regimes):
    return np.array([[1.0 if c == r else 0.0 for c in CLASSES] for r in regimes])


def run(tcfg, regimes, prices, rule, **kw):
    n = len(regimes)
    ts = pd.date_range("2024-01-01", periods=n + 1, freq="D")
    probs = kw.pop("probs", onehot(regimes))
    return simulate(probs, np.asarray(prices[:-1], float), np.asarray(prices[1:], float), ts[:-1], ts[1:],
                    rule, tcfg, CLASSES, 252, keep_log=True)


def no_cost(tcfg, yield_=0.0):
    t = copy.deepcopy(tcfg)
    for inst in t["instruments"].values():
        inst.update(cost_rate=0.0, fixed_cost_per_sell=0.0, roll_cost_rate=0.0)
    t["cash_yield_annual"] = yield_
    return t


def test_always_bull_long_only_tracks_price(tcfg):
    prices = [100, 110, 99, 120, 130]
    res = run(no_cost(tcfg), ["bull"] * 4, prices, Rule("long_only", "risk_off", 1, 0.0, None))
    assert np.isclose(res["final_capital"], 1_000_000 * 130 / 100)
    assert res["n_trades"] == 1


def test_all_cash_earns_yield(tcfg):
    t = no_cost(tcfg, 0.06)
    res = run(t, ["bear"] * 252, np.linspace(100, 50, 253), Rule("long_only", "risk_off", 1, 0.0, None))
    assert np.isclose(res["final_capital"], 1_060_000, rtol=1e-9)
    assert res["n_trades"] == 0


def test_costs_charged(tcfg):
    prices = [100, 100, 100]
    res = run(tcfg, ["bull", "bear"], prices, Rule("long_only", "risk_off", 1, 0.0, None))
    t = tcfg["instruments"]["long_only"]
    buy_cost = t["cost_rate"] * 1_000_000                              # 10,000 units at 100
    sell_cost = t["cost_rate"] * 1_000_000 + t["fixed_cost_per_sell"]   # the same 10,000 units sold at 100
    yield_ = (1 + tcfg["cash_yield_annual"]) ** (1 / 252) - 1
    assert res["n_trades"] == 2
    assert np.isclose(res["total_costs"], buy_cost + sell_cost, rtol=1e-6)
    assert res["final_capital"] < 1_000_000 * (1 + yield_)


def test_short_profits_when_price_falls(tcfg):
    t = dict(no_cost(tcfg), min_trade=1.0)   # enter once, no re-sizing as the short gains
    res = run(t, ["bear"] * 3, [100, 90, 80, 70], Rule("long_short", "ls_spec", 1, 0.0, None))
    assert np.isclose(res["final_capital"], 1_000_000 + 1_000_000 / 100 * 30)


def test_confirmation_delays_entry(tcfg):
    prices = [100, 100, 100, 100, 100]
    res = run(no_cost(tcfg), ["bull"] * 4, prices, Rule("long_only", "risk_off", 3, 0.0, None))
    assert [t["time"] for t in res["trades"]] == [pd.Timestamp("2024-01-03")]


def test_low_confidence_does_not_count(tcfg):
    probs = np.array([[0.4, 0.3, 0.3, 0.0]] * 4)
    res = run(no_cost(tcfg), ["bull"] * 4, [100] * 5, Rule("long_only", "risk_off", 1, 0.6, None), probs=probs)
    assert res["n_trades"] == 0


def test_stop_loss_exits_and_waits_for_regime_change(tcfg):
    regimes = ["bull"] * 5 + ["sideways", "bull", "bull"]
    prices = [100, 100, 90, 95, 100, 105, 105, 110, 110]
    res = run(no_cost(tcfg), regimes, prices, Rule("long_only", "bull_only", 1, 0.0, 0.05))
    actions = [(t["time"].day, t["action"]) for t in res["trades"]]
    # buy day 1; 10% drop on day 2 triggers the stop -> sell at day 3 decision; stays out while still bull;
    # sideways (day 6) releases the stop but bull_only holds cash; bull again on day 7 -> buy
    assert actions == [(1, "BUY"), (3, "SELL"), (7, "BUY")]


def test_grid_sizes(tcfg):
    assert len(rule_grid(tcfg, "daily", "long_only")) == 3 * 3 * 2 * 2 + 3 * 2
    assert len(rule_grid(tcfg, "daily", "long_short")) == 2 * 3 * 2 * 2 + 3 * 2
