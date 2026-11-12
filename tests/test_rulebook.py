import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.config import load_config
from regime.rulebook import RuleBook, rulebook_grid, simulate_rulebook

CLASSES = ["bull", "bear", "sideways", "high_vol"]


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def tc(cfg, costs=False, yield_=0.0):
    t = copy.deepcopy(cfg["trading"])
    if not costs:
        for inst in t["instruments"].values():
            inst.update(cost_rate=0.0, fixed_cost_per_sell=0.0, roll_cost_rate=0.0)
    t["cash_yield_annual"] = yield_
    return t


def P(bull=0.0, bear=0.0, sideways=0.0, high_vol=0.0):
    return [bull, bear, sideways, high_vol]


def run(t, probs, prices, rb):
    ts = pd.date_range("2024-01-01", periods=len(probs) + 1, freq="D")
    return simulate_rulebook(np.array(probs, float), np.array(prices[:-1], float), np.array(prices[1:], float),
                             ts[:-1], ts[1:], rb, t, CLASSES, 252, keep_log=True)


def actions(res):
    return [(t["time"].day, t["action"]) for t in res["trades"]]


def test_buy_needs_confirmation_and_sizes_by_probability(cfg):
    rb = RuleBook(buy_threshold=0.6, confirm_days=2, sizing="scaled", strong_margin=0.15, stop_loss=None, cooldown_days=0)
    probs = [P(bull=0.65, sideways=0.35), P(bull=0.65, sideways=0.35), P(bull=0.9, sideways=0.1), P(bull=0.9, sideways=0.1)]
    res = run(tc(cfg), probs, [100] * 5, rb)
    assert actions(res) == [(2, "BUY 50%"), (3, "ADD to 100%")]


def test_sideways_never_trades(cfg):
    rb = RuleBook(stop_loss=None, cooldown_days=0)
    res = run(tc(cfg), [P(sideways=0.9, bull=0.1)] * 10, [100] * 11, rb)
    assert res["n_trades"] == 0


def test_sell_to_cash_on_risk(cfg):
    rb = RuleBook(buy_threshold=0.6, sell_threshold=0.5, confirm_days=1, sizing="full", stop_loss=None, cooldown_days=0)
    probs = [P(bull=0.8, sideways=0.2), P(sideways=0.6, bull=0.4), P(bear=0.3, high_vol=0.25, sideways=0.45)]
    res = run(tc(cfg), probs, [100, 110, 120, 90], rb)
    assert actions(res) == [(1, "BUY 100%"), (3, "SELL")]
    assert np.isclose(res["final_capital"], 1_200_000)   # sold at 120 before the fall to 90


def test_short_and_cover(cfg):
    rb = RuleBook(buy_threshold=0.6, sell_threshold=0.5, confirm_days=1, sizing="full", stop_loss=None, cooldown_days=0, on_sell="short")
    probs = [P(bear=0.7, sideways=0.3), P(bear=0.7, sideways=0.3), P(bull=0.7, sideways=0.3)]
    res = run(tc(cfg), probs, [100, 90, 80, 80], rb)
    assert actions(res)[:2] == [(1, "SHORT 100%"), (3, "COVER SHORT")]
    assert np.isclose(res["final_capital"], 1_000_000 + 10_000 * 20)


def test_stop_loss_cooldown_and_fresh_signal(cfg):
    rb = RuleBook(buy_threshold=0.6, confirm_days=1, sizing="full", stop_loss=0.08, cooldown_days=2)
    bull = P(bull=0.8, sideways=0.2)
    probs = [bull, bull, bull, bull, bull, P(sideways=0.9, bull=0.1), bull, bull]
    prices = [100, 100, 90, 90, 95, 100, 100, 105, 110]
    res = run(tc(cfg), probs, prices, rb)
    # buy day 1; -10% on day 2 -> stop exit day 3; bull persists (no fresh signal) and cooldown runs;
    # day 6 bull drops below threshold -> fresh; day 7 bull again and cooldown over -> buy
    assert actions(res) == [(1, "BUY 100%"), (3, "STOP-LOSS"), (7, "BUY 100%")]


def test_cooldown_blocks_reentry(cfg):
    rb = RuleBook(buy_threshold=0.6, sell_threshold=0.5, confirm_days=1, sizing="full", stop_loss=None, cooldown_days=3)
    bull, risk = P(bull=0.8, sideways=0.2), P(bear=0.6, sideways=0.4)
    probs = [bull, risk, bull, bull, bull, bull]
    res = run(tc(cfg), probs, [100] * 7, rb)
    assert actions(res) == [(1, "BUY 100%"), (2, "SELL"), (6, "BUY 100%")]


def test_costs_and_cash_yield(cfg):
    t = tc(cfg, costs=True, yield_=0.06)
    res = run(t, [P(sideways=1.0)] * 252, [100] * 253, RuleBook())
    assert res["n_trades"] == 0 and np.isclose(res["final_capital"], 1_060_000)


def test_grid_size(cfg):
    g = cfg["rulebook"]["grid"]
    assert len(rulebook_grid(g, 0.15)) == 3 * 3 * 3 * 2 * 3 * 2 * 2
