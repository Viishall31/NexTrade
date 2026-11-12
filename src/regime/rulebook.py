"""Step 11: probability-based trading rulebook (Experiment 2).

Every trading day, at the close, the model gives the probability of each regime for the next day.
With  P_bull = P(bull)  and  P_risk = P(bear) + P(high_vol):

  BUY    P_bull >= buy_threshold for `confirm_days` consecutive days
         -> 100% invested if P_bull >= buy_threshold + strong_margin (sizing=scaled), else 50%
  SELL   P_risk >= sell_threshold for `confirm_days` consecutive days
         -> move to cash (on_sell=cash) or go short (on_sell=short, futures, idealized)
         SELL has priority if both signals fire on the same day.
  HOLD   neither signal -> keep the current position (a sideways forecast never triggers a trade)
  STOP   trailing stop: the portfolio falls `stop_loss` below its peak since entry -> exit at the next close
  WAIT   after any exit: no new entry for `cooldown_days`; after a stop, the stopped side also needs a
         fresh signal (its probability must first drop below the threshold, then confirm again)

Execution, costs and cash interest are the same as Step 10 (regime.trading).
"""
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from regime.trading import roll_days, summarize


@dataclass(frozen=True)
class RuleBook:
    buy_threshold: float = 0.6
    sell_threshold: float = 0.5
    confirm_days: int = 2
    sizing: str = "scaled"
    strong_margin: float = 0.15
    stop_loss: float | None = 0.08
    cooldown_days: int = 5
    on_sell: str = "cash"

    @property
    def name(self) -> str:
        stop = f"stop{int(round(self.stop_loss * 100))}" if self.stop_loss else "nostop"
        return (f"buy{self.buy_threshold:g}|sell{self.sell_threshold:g}|confirm{self.confirm_days}|{self.sizing}|"
                f"{stop}|cool{self.cooldown_days}|{self.on_sell}")

    @property
    def instrument(self) -> str:
        return "long_only" if self.on_sell == "cash" else "long_short"

    def to_dict(self) -> dict:
        return {**asdict(self), "name": self.name}


def rulebook_grid(grid: dict, strong_margin: float) -> list[RuleBook]:
    out = []
    for b in grid["buy_threshold"]:
        for s in grid["sell_threshold"]:
            for c in grid["confirm_days"]:
                for z in grid["sizing"]:
                    for sl in grid["stop_loss"]:
                        for cd in grid["cooldown_days"]:
                            for o in grid["on_sell"]:
                                out.append(RuleBook(float(b), float(s), int(c), z, strong_margin, sl, int(cd), o))
    return out


def simulate_rulebook(prob: np.ndarray, price_now: np.ndarray, price_next: np.ndarray, timestamps: pd.DatetimeIndex,
                      next_timestamps: pd.DatetimeIndex, rb: RuleBook, tcfg: dict, classes: list,
                      periods_per_year: int, keep_log: bool = False) -> dict:
    inst = tcfg["instruments"][rb.instrument]
    ib, ibear, ihv = classes.index("bull"), classes.index("bear"), classes.index("high_vol")
    rf = (1 + tcfg["cash_yield_annual"]) ** (1 / periods_per_year) - 1
    rolls = roll_days(timestamps) if inst["roll_cost_rate"] > 0 else np.zeros(len(prob), bool)

    n = len(prob)
    capital = float(tcfg["initial_capital"])
    cash, units = capital, 0.0
    buy_streak = sell_streak = cooldown = 0
    blocked_side = 0            # side (+1/-1) that was stopped out and needs a fresh signal
    stop_pending = False
    peak = entry_equity = None
    equity_path, in_market = np.empty(n), np.zeros(n, bool)
    total_cost = total_interest = 0.0
    n_trades, trades, round_trips = 0, [], []

    def equity_at(price):
        return cash + units * price if inst["funded"] else cash

    for i in range(n):
        price = price_now[i]
        equity = equity_at(price)
        p_bull, p_risk = prob[i, ib], prob[i, ibear] + prob[i, ihv]

        buy_streak = buy_streak + 1 if p_bull >= rb.buy_threshold else 0
        sell_streak = sell_streak + 1 if p_risk >= rb.sell_threshold else 0
        if blocked_side == 1 and p_bull < rb.buy_threshold:
            blocked_side = 0
        if blocked_side == -1 and p_risk < rb.sell_threshold:
            blocked_side = 0
        buy_signal = buy_streak >= rb.confirm_days
        sell_signal = sell_streak >= rb.confirm_days

        side = int(np.sign(units))
        current = units * price / equity if equity > 0 else 0.0
        target, reason = current, None

        if stop_pending and side != 0:
            target, reason = 0.0, f"STOP-LOSS: portfolio {100 * rb.stop_loss:g}% below its peak since entry"
            blocked_side, cooldown = side, rb.cooldown_days
        elif sell_signal:
            if rb.on_sell == "cash":
                if side > 0:
                    target, reason = 0.0, f"SELL: P(bear)+P(high_vol) = {p_risk:.2f} >= {rb.sell_threshold:g} for {rb.confirm_days} day(s)"
            else:
                size = 1.0 if rb.sizing == "full" or p_risk >= rb.sell_threshold + rb.strong_margin else 0.5
                if side > 0:   # close the long first; a short needs cooldown/fresh-signal clearance like any entry
                    target, reason = 0.0, f"SELL (close long): P(bear)+P(high_vol) = {p_risk:.2f} >= {rb.sell_threshold:g}"
                elif cooldown == 0 and blocked_side != -1 and not np.isclose(current, -size) and (side == 0 or abs(-size - current) >= tcfg["min_trade"]):
                    target, reason = -size, f"SHORT {int(size * 100)}%: P(bear)+P(high_vol) = {p_risk:.2f} >= {rb.sell_threshold:g} for {rb.confirm_days} day(s)"
        elif buy_signal:
            size = 1.0 if rb.sizing == "full" or p_bull >= rb.buy_threshold + rb.strong_margin else 0.5
            if side < 0:
                target, reason = 0.0, f"COVER SHORT: P(bull) = {p_bull:.2f} >= {rb.buy_threshold:g}"
            elif cooldown == 0 and blocked_side != 1 and not np.isclose(current, size) and (side == 0 or abs(size - current) >= tcfg["min_trade"]):
                strong = rb.buy_threshold + rb.strong_margin
                if side == 0:
                    target, reason = size, f"BUY {int(size * 100)}%: P(bull) = {p_bull:.2f} >= {rb.buy_threshold:g} for {rb.confirm_days} day(s)"
                elif size > current:
                    target, reason = size, f"ADD to {int(size * 100)}%: P(bull) = {p_bull:.2f} rose to >= {strong:.2f}"
                else:
                    target, reason = size, f"REDUCE to {int(size * 100)}%: P(bull) = {p_bull:.2f} fell below {strong:.2f}"
        stop_pending = False

        if reason is not None:
            new_units = target * equity / price
            delta = new_units - units
            value = abs(delta) * price
            cost = inst["cost_rate"] * value + (inst["fixed_cost_per_sell"] if delta < 0 and inst["funded"] else 0.0)
            closing = units != 0.0 and (new_units == 0.0 or units * new_units < 0)
            if closing:
                round_trips.append(equity - cost - entry_equity)
                cooldown = max(cooldown, rb.cooldown_days)
            if inst["funded"]:
                cash -= delta * price
            cash -= cost
            total_cost += cost
            n_trades += 1
            if new_units != 0.0 and (units == 0.0 or units * new_units < 0):
                entry_equity = peak = equity - cost
            units = new_units
            if keep_log:
                trades.append({"time": timestamps[i], "action": reason.split(":")[0], "reason": reason, "price": price,
                               "units": delta, "value": value, "cost": cost, "position_after": target,
                               "p_bull": p_bull, "p_sideways": prob[i, classes.index("sideways")],
                               "p_bear": prob[i, ibear], "p_high_vol": prob[i, ihv], "equity_before": equity})
        elif cooldown > 0:
            cooldown -= 1

        if units != 0.0 and rolls[i]:
            cost = inst["roll_cost_rate"] * abs(units) * price
            cash -= cost
            total_cost += cost

        interest = cash * rf
        cash += interest
        total_interest += interest
        if not inst["funded"]:
            cash += units * (price_next[i] - price)
        equity_path[i] = equity_at(price_next[i])
        in_market[i] = units != 0.0
        if units != 0.0 and rb.stop_loss:
            peak = max(peak, equity_path[i])
            stop_pending = equity_path[i] <= peak * (1 - rb.stop_loss)

    if units != 0.0:
        round_trips.append(equity_path[-1] - entry_equity)
    result = {"rulebook": rb.to_dict(),
              **summarize(equity_path, capital, rf, periods_per_year, n_trades, round_trips, total_cost, total_interest, in_market)}
    if keep_log:
        result["trades"] = trades
        result["equity"] = pd.Series(equity_path, index=next_timestamps, name="equity")
    return result


def run_rulebook_on(sig: pd.DataFrame, rb: RuleBook, cfg: dict, freq: str = "daily", keep_log: bool = False) -> dict:
    classes = cfg["sequence"]["classes"]
    return simulate_rulebook(sig[[f"p_{c}" for c in classes]].to_numpy(), sig["price_now"].to_numpy(),
                             sig["price_next"].to_numpy(), pd.DatetimeIndex(sig["decision_time"]),
                             pd.DatetimeIndex(sig["next_time"]), rb, cfg["trading"], classes,
                             cfg["backtest"]["periods_per_year"][freq], keep_log)
