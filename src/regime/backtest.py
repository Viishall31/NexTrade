"""Step 5: regime-conditioned backtester (FR-E3, spec section 9.2).

Timing: sample i has a window ending at bar t and a target bar t+1. The prediction is made
at the close of t, so the position it sets earns the return from close t to close t+1,
i.e. the return *at the target bar*. Nothing from t+1 is used to choose the position.
"""
import numpy as np
import pandas as pd


def exposures_from_predictions(pred_regimes: np.ndarray, exposure_map: dict, rebalance_every: int) -> np.ndarray:
    """Target exposure per sample; only updated every `rebalance_every` samples."""
    raw = np.array([exposure_map[r] for r in pred_regimes], dtype=float)
    held = raw[(np.arange(len(raw)) // rebalance_every) * rebalance_every]
    return held


def run_backtest(asset_returns: np.ndarray, exposure: np.ndarray, cfg: dict, freq: str) -> pd.DataFrame:
    """Per-period strategy returns. asset_returns[i] = simple return over the period sample i holds."""
    ppy = cfg["periods_per_year"][freq]
    rf = (1 + cfg["risk_free_annual"]) ** (1 / ppy) - 1
    turnover = np.abs(np.diff(exposure, prepend=0.0))   # entering the first position also costs
    cost = turnover * cfg["cost_bps"] / 1e4
    cash = (1 - exposure) * rf if cfg["cash_earns_risk_free"] else 0.0
    strat = exposure * asset_returns + cash - cost
    return pd.DataFrame({"asset_return": asset_returns, "exposure": exposure, "turnover": turnover,
                         "cost": cost, "strategy_return": strat, "rf": rf})


def performance(returns: np.ndarray, rf_per_period: float, periods_per_year: int) -> dict:
    returns = np.asarray(returns, dtype=float)
    excess = returns - rf_per_period
    ann_excess = excess.mean() * periods_per_year
    std = excess.std(ddof=1) * np.sqrt(periods_per_year)
    downside = np.sqrt(np.mean(np.minimum(excess, 0.0) ** 2)) * np.sqrt(periods_per_year)
    equity = np.cumprod(1 + returns)
    drawdown = equity / np.maximum.accumulate(np.concatenate([[1.0], equity]))[1:] - 1
    years = len(returns) / periods_per_year
    return {
        "sharpe": float(ann_excess / std) if std > 1e-12 else 0.0,
        "sortino": float(ann_excess / downside) if downside > 1e-12 else 0.0,
        "max_drawdown": float(drawdown.min()),
        "cumulative_return": float(equity[-1] - 1),
        "annualized_return": float(equity[-1] ** (1 / years) - 1),
        "annualized_volatility": float(returns.std(ddof=1) * np.sqrt(periods_per_year)),
    }


def evaluate_strategy(pred_regimes: np.ndarray, asset_returns: np.ndarray, cfg: dict, freq: str) -> tuple[dict, pd.DataFrame]:
    exposure = exposures_from_predictions(pred_regimes, cfg["exposure"], cfg["rebalance_every"][freq])
    bt = run_backtest(asset_returns, exposure, cfg, freq)
    perf = performance(bt["strategy_return"].to_numpy(), bt["rf"].iloc[0], cfg["periods_per_year"][freq])
    perf["avg_exposure"] = float(exposure.mean())
    perf["total_turnover"] = float(bt["turnover"].sum())
    perf["cost_drag"] = float(bt["cost"].sum())
    return perf, bt


def target_returns(close: pd.Series, target_time: pd.DatetimeIndex) -> np.ndarray:
    """Simple return from the bar before each target bar to the target bar."""
    r = close.pct_change()
    return r.reindex(target_time).to_numpy()
