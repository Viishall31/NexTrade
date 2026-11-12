"""Step 10: rule-based trading simulator in rupees.

Timing (same as the backtester): sample i is decided at the close of bar t_i using the model's
probabilities from the window ending at t_i; the resulting position is held until the close of
the next bar. Trades execute at the decision bar's close (approximates the closing session).
"""
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Rule:
    direction: str               # long_only | long_short
    exposure_map: str            # key under trading.exposure_maps[direction]
    confirm: int                 # consecutive identical predictions (regime maps) / EMA span (probability maps)
    min_confidence: float
    stop_loss: float | None

    @property
    def name(self) -> str:
        stop = f"stop{int(self.stop_loss * 100)}" if self.stop_loss else "nostop"
        return f"{self.exposure_map}|confirm{self.confirm}|conf{self.min_confidence:g}|{stop}"

    def to_dict(self) -> dict:
        return {**asdict(self), "name": self.name}


def rule_grid(tcfg: dict, freq: str, direction: str) -> list[Rule]:
    rules = []
    for map_name, spec in tcfg["exposure_maps"][direction].items():
        prob = spec.get("probability_weighted", False)
        for n in tcfg["confirm"][freq]:
            for c in ([0.0] if prob else tcfg["min_confidence"]):
                for s in tcfg["stop_loss"]:
                    rules.append(Rule(direction, map_name, int(n), float(c), s))
    return rules


def roll_days(timestamps: pd.DatetimeIndex) -> np.ndarray:
    """True at the last bar of each calendar month (proxy for the monthly futures expiry roll)."""
    ts = pd.Series(timestamps)
    month = ts.dt.to_period("M")
    return (month != month.shift(-1)).to_numpy() & (np.arange(len(ts)) < len(ts) - 1)


def simulate(prob: np.ndarray, price_now: np.ndarray, price_next: np.ndarray, timestamps: pd.DatetimeIndex,
             next_timestamps: pd.DatetimeIndex, rule: Rule, tcfg: dict, classes: list, periods_per_year: int,
             keep_log: bool = False) -> dict:
    """timestamps = decision bars (t_i); next_timestamps = the bars each position is marked at (t_i + 1)."""
    inst = tcfg["instruments"][rule.direction]
    spec = tcfg["exposure_maps"][rule.direction][rule.exposure_map]
    w = np.array([spec["weights"][c] for c in classes])
    prob_map = spec.get("probability_weighted", False)
    rf = (1 + tcfg["cash_yield_annual"]) ** (1 / periods_per_year) - 1
    rolls = roll_days(timestamps) if inst["roll_cost_rate"] > 0 else np.zeros(len(prob), bool)
    alpha = 2 / (rule.confirm + 1)

    n = len(prob)
    capital = float(tcfg["initial_capital"])
    cash, units = capital, 0.0
    confirmed, run_regime, run_len, ema_p = None, None, 0, None
    stopped, stop_regime, peak, entry_equity = False, None, None, None
    equity_path = np.empty(n)
    in_market = np.zeros(n, bool)
    total_cost = total_interest = 0.0
    n_trades = 0
    trades, round_trips = [], []

    def equity_at(price):
        return cash + units * price if inst["funded"] else cash

    for i in range(n):
        price = price_now[i]
        equity = equity_at(price)

        # ---- signal -> confirmed regime -> target exposure ----
        p = prob[i]
        if prob_map:
            ema_p = p if ema_p is None else alpha * p + (1 - alpha) * ema_p
            confirmed = int(ema_p.argmax())
            target = float(ema_p @ w)
        else:
            k = int(p.argmax())
            if p[k] >= rule.min_confidence:
                run_len = run_len + 1 if k == run_regime else 1
                run_regime = k
            if run_len >= rule.confirm:
                confirmed = run_regime
            target = float(w[confirmed]) if confirmed is not None else 0.0
        if stopped:
            if confirmed != stop_regime:
                stopped = False
            else:
                target = 0.0

        # ---- rebalance ----
        current = units * price / equity if equity > 0 else 0.0
        if abs(target - current) >= tcfg["min_trade"] or (target == 0.0 and units != 0.0):
            new_units = target * equity / price
            delta = new_units - units
            value = abs(delta) * price
            cost = inst["cost_rate"] * value + (inst["fixed_cost_per_sell"] if delta < 0 and inst["funded"] else 0.0)
            was_flat, flipped = units == 0.0, units * new_units < 0
            if (units != 0.0 and new_units == 0.0) or flipped:
                round_trips.append(equity - cost - entry_equity)
            if inst["funded"]:
                cash -= delta * price
            cash -= cost
            total_cost += cost
            n_trades += 1
            units = new_units
            if new_units != 0.0 and (was_flat or flipped):
                entry_equity = peak = equity - cost
            if keep_log:
                trades.append({"time": timestamps[i], "action": "BUY" if delta > 0 else "SELL", "price": price,
                               "units": delta, "value": value, "cost": cost, "target_exposure": target,
                               "regime": classes[confirmed] if confirmed is not None else None,
                               "equity_before": equity})
        if units != 0.0 and rolls[i]:
            cost = inst["roll_cost_rate"] * abs(units) * price
            cash -= cost
            total_cost += cost

        # ---- hold until the next bar ----
        interest = cash * rf   # funded: uninvested cash; futures: the whole collateral
        cash += interest
        total_interest += interest
        if not inst["funded"]:
            cash += units * (price_next[i] - price)
        equity_next = equity_at(price_next[i])
        equity_path[i] = equity_next
        in_market[i] = units != 0.0

        if units != 0.0 and rule.stop_loss:
            peak = max(peak, equity_next)
            if equity_next < peak * (1 - rule.stop_loss) and not stopped:
                stopped, stop_regime = True, confirmed

    if units != 0.0:
        round_trips.append(equity_path[-1] - entry_equity)   # open position marked at the end

    result = {"rule": rule.to_dict(),
              **summarize(equity_path, capital, rf, periods_per_year, n_trades, round_trips, total_cost, total_interest, in_market)}
    if keep_log:
        result["trades"] = trades
        result["equity"] = pd.Series(equity_path, index=next_timestamps, name="equity")
    return result


def summarize(equity_path: np.ndarray, capital: float, rf: float, periods_per_year: int, n_trades: int,
              round_trips: list, total_cost: float, total_interest: float, in_market: np.ndarray) -> dict:
    """Rupee performance summary shared by all simulators."""
    n = len(equity_path)
    rets = np.diff(np.concatenate([[capital], equity_path])) / np.concatenate([[capital], equity_path[:-1]])
    excess = rets - rf
    peak_path = np.maximum.accumulate(np.concatenate([[capital], equity_path]))[1:]
    dd = equity_path / peak_path - 1
    years = n / periods_per_year
    return {
        "initial_capital": capital,
        "final_capital": float(equity_path[-1]),
        "net_profit": float(equity_path[-1] - capital),
        "total_return": float(equity_path[-1] / capital - 1),
        "cagr": float((equity_path[-1] / capital) ** (1 / years) - 1),
        "max_drawdown": float(dd.min()),
        "max_drawdown_rupees": float((equity_path - peak_path).min()),
        "sharpe": float(excess.mean() / excess.std(ddof=1) * np.sqrt(periods_per_year)) if excess.std() > 0 else 0.0,
        "n_trades": n_trades,
        "n_round_trips": len(round_trips),
        "win_rate": float(np.mean(np.array(round_trips) > 0)) if round_trips else None,
        "total_costs": float(total_cost),
        "interest_earned": float(total_interest),
        "time_in_market": float(in_market.mean()),
    }
