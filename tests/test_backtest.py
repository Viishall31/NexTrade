import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.backtest import evaluate_strategy, exposures_from_predictions, performance, run_backtest, target_returns
from regime.config import load_config


@pytest.fixture(scope="module")
def bcfg():
    return load_config()["backtest"]


def test_all_bull_without_cost_is_buy_and_hold(bcfg):
    r = np.random.default_rng(0).normal(0.0005, 0.01, 300)
    cfg = dict(bcfg, cost_bps=0)
    perf, bt = evaluate_strategy(np.array(["bull"] * 300), r, cfg, "daily")
    assert np.allclose(bt["strategy_return"], r)
    assert np.isclose(perf["cumulative_return"], np.prod(1 + r) - 1)


def test_all_bear_is_cash_with_zero_sharpe(bcfg):
    r = np.random.default_rng(1).normal(0, 0.01, 252)
    perf, bt = evaluate_strategy(np.array(["bear"] * 252), r, bcfg, "daily")
    assert np.allclose(bt["strategy_return"], bt["rf"])
    assert perf["sharpe"] == 0.0
    assert np.isclose(perf["cumulative_return"], bcfg["risk_free_annual"], atol=1e-9)


def test_costs_charged_on_exposure_changes(bcfg):
    preds = np.array(["bull", "bear", "sideways", "sideways", "high_vol"])
    exp = exposures_from_predictions(preds, bcfg["exposure"], 1)
    assert list(exp) == [1.0, 0.0, 0.5, 0.5, 0.25]
    bt = run_backtest(np.zeros(5), exp, dict(bcfg, cash_earns_risk_free=False), "daily")
    assert np.allclose(bt["turnover"], [1.0, 1.0, 0.5, 0.0, 0.25])
    assert np.allclose(bt["cost"], np.array([1.0, 1.0, 0.5, 0.0, 0.25]) * 5e-4)


def test_rebalance_every_holds_position(bcfg):
    preds = np.array(["bull", "bear", "bear", "bear", "sideways", "bull", "bull"])
    exp = exposures_from_predictions(preds, bcfg["exposure"], 3)
    assert list(exp) == [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0]


def test_max_drawdown_known_path():
    perf = performance(np.array([0.10, -0.50, 0.20]), 0.0, 252)
    assert np.isclose(perf["max_drawdown"], -0.5)
    assert np.isclose(perf["cumulative_return"], 1.1 * 0.5 * 1.2 - 1)


def test_target_returns_use_target_bar():
    idx = pd.date_range("2024-01-01", periods=4, freq="D")
    close = pd.Series([100.0, 110.0, 99.0, 99.0], index=idx)
    assert np.allclose(target_returns(close, idx[[1, 2]]), [0.10, -0.10])
