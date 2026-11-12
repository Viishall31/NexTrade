"""Step 2: technical-indicator features (FR-F1) and train-only normalisation (FR-F3).

Every indicator here is causal: the value at bar t uses only bars <= t. That is what
tests/test_features.py checks, so features can be computed once over the whole series
and the only thing that must respect the split is the scaler.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _wilder(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(alpha=1 / n, adjust=False).mean()


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _safe_div(a: pd.Series, b: pd.Series, fill: float) -> pd.Series:
    return (a / b.replace(0, np.nan)).fillna(fill)


def rsi(close: pd.Series, n: int) -> pd.Series:
    d = close.diff()
    gain = _wilder(d.clip(lower=0), n)
    loss = _wilder(-d.clip(upper=0), n)
    rs = _safe_div(gain, loss, np.inf)
    return 100 - 100 / (1 + rs)


def true_range(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift()
    return pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)


def adx(df: pd.DataFrame, n: int) -> pd.Series:
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    atr = _wilder(true_range(df), n)
    plus_di = 100 * _safe_div(_wilder(plus_dm, n), atr, 0)
    minus_di = 100 * _safe_div(_wilder(minus_dm, n), atr, 0)
    dx = 100 * _safe_div((plus_di - minus_di).abs(), plus_di + minus_di, 0)
    return _wilder(dx, n)


def compute_features(df: pd.DataFrame, cfg: dict, freq: str) -> pd.DataFrame:
    """OHLC frame -> feature frame (model features + HMM inputs), warm-up rows removed."""
    c = df["close"]
    out = pd.DataFrame(index=df.index)
    out["close"] = c
    out["log_return"] = np.log(c).diff()

    out["rsi"] = rsi(c, cfg["rsi_period"])

    m = cfg["macd"]
    out["macd"] = _ema(c, m["fast"]) - _ema(c, m["slow"])
    out["macd_signal"] = _ema(out["macd"], m["signal"])
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    # MACD is in index points; express it relative to price so 2015 and 2024 are comparable.
    for col in ["macd", "macd_signal", "macd_hist"]:
        out[col] = out[col] / c

    for p in cfg["ema_periods"]:
        out[f"close_ema{p}"] = c / _ema(c, p)

    out["atr_norm"] = _wilder(true_range(df), cfg["atr_period"]) / c
    out["adx"] = adx(df, cfg["adx_period"])

    b = cfg["bollinger"]
    mid = c.rolling(b["period"]).mean()
    sd = c.rolling(b["period"]).std(ddof=0)
    upper, lower = mid + b["std"] * sd, mid - b["std"] * sd
    out["bb_pctb"] = _safe_div(c - lower, upper - lower, 0.5)
    out["bb_width"] = (upper - lower) / mid

    s = cfg["stoch_rsi"]
    lo = out["rsi"].rolling(s["period"]).min()
    hi = out["rsi"].rolling(s["period"]).max()
    stoch = 100 * _safe_div(out["rsi"] - lo, hi - lo, 0.5)
    out["stochrsi_k"] = stoch.rolling(s["smooth_k"]).mean()
    out["stochrsi_d"] = out["stochrsi_k"].rolling(s["smooth_d"]).mean()

    ann = np.sqrt(cfg["periods_per_year"][freq])
    out[f"ret{cfg['hmm_return_window']}"] = np.log(c).diff(cfg["hmm_return_window"])
    for w in cfg["realized_vol_windows"]:
        out[f"rv{w}"] = out["log_return"].rolling(w).std() * ann

    out = out.iloc[cfg["warmup_bars"]:]
    if out.isna().any().any() or np.isinf(out.drop(columns="close")).any().any():
        bad = out.columns[out.isna().any() | np.isinf(out).any()].tolist()
        raise ValueError(f"NaN/inf left after warm-up in {bad}")
    return out


def assign_split(index: pd.DatetimeIndex, split: dict) -> pd.Series:
    """train <= train_end < val <= val_end < test (the held-out Nifty50_test.csv period)."""
    day = index.normalize()
    lbl = np.where(day <= pd.Timestamp(split["train_end"]), "train",
                   np.where(day <= pd.Timestamp(split["val_end"]), "val", "test"))
    return pd.Series(lbl, index=index, name="split")


class TrainOnlyScaler:
    """z-score scaler whose statistics come only from the training split (C-1). Frozen afterwards."""

    def __init__(self, columns: list[str]):
        self.columns = columns
        self.mean_: dict | None = None
        self.std_: dict | None = None

    def fit(self, train: pd.DataFrame) -> "TrainOnlyScaler":
        self.mean_ = train[self.columns].mean().to_dict()
        self.std_ = train[self.columns].std(ddof=0).replace(0, 1.0).to_dict()
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in self.columns:
            out[col] = (df[col] - self.mean_[col]) / self.std_[col]
        return out

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"columns": self.columns, "mean": self.mean_, "std": self.std_}, indent=2))

    @classmethod
    def load(cls, path: Path) -> "TrainOnlyScaler":
        d = json.loads(path.read_text())
        s = cls(d["columns"])
        s.mean_, s.std_ = d["mean"], d["std"]
        return s
