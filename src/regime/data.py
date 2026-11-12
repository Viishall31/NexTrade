"""Step 1: load, clean and validate Nifty 50 15-minute OHLC data (FR-D4, FR-D5)."""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

OHLC = ["open", "high", "low", "close"]


@dataclass
class CleaningReport:
    source: str
    raw_rows: int = 0
    duplicate_rows_dropped: int = 0
    duplicate_days: int = 0
    conflicting_duplicate_bars: int = 0
    out_of_session_rows_dropped: int = 0
    out_of_session_dates: list = field(default_factory=list)
    single_bar_gaps_filled: int = 0
    days_dropped_for_gaps: dict = field(default_factory=dict)
    ohlc_violations_fixed: int = 0
    return_outliers: list = field(default_factory=list)
    calendar_gaps: list = field(default_factory=list)
    final_rows: int = 0
    final_days: int = 0
    start: str = ""
    end: str = ""


def read_raw(path: str) -> pd.DataFrame:
    """Read the vendor CSV, keeping file order (needed to resolve duplicates)."""
    df = pd.read_csv(path)
    # time looks like '09:15:00+05:30' -> every row is IST; store tz-naive IST timestamps.
    df["timestamp"] = pd.to_datetime(df["date"] + " " + df["time"].str[:8], format="%d-%m-%Y %H:%M:%S")
    return df


def session_slots(cfg: dict) -> list[pd.Timedelta]:
    start = pd.Timedelta(cfg["session_start"] + ":00")
    last = pd.Timedelta(cfg["session_last_bar"] + ":00")
    step = pd.Timedelta(minutes=cfg["bar_minutes"])
    n = int((last - start) / step) + 1
    return [start + i * step for i in range(n)]


def clean_15min(path: str, cfg: dict) -> tuple[pd.DataFrame, CleaningReport]:
    rep = CleaningReport(source=str(path))
    df = read_raw(path)
    rep.raw_rows = len(df)

    df = df.drop(columns=[c for c in cfg["drop_columns"] if c in df.columns] + ["date", "time"])

    # Duplicates: the export repeats whole days at chunk boundaries. Copies agree except
    # the 09:15 bar of the later copy, whose open/high are corrupted (open ~55 pts from the
    # prior close vs <1 pt for the first copy). Keep the first copy in file order.
    dups = df[df["timestamp"].duplicated(keep=False)]
    dup_mask = df["timestamp"].duplicated(keep="first")
    rep.duplicate_rows_dropped = int(dup_mask.sum())
    rep.duplicate_days = int(dups["timestamp"].dt.date.nunique())
    rep.conflicting_duplicate_bars = int((dups.groupby("timestamp")[OHLC].nunique().max(axis=1) > 1).sum())
    df = df[~dup_mask].sort_values("timestamp").set_index("timestamp")

    # Session filter: drop bars outside the regular 09:15-15:15 grid (Muhurat evening
    # sessions, the 2021-02-24 extended session). Full weekend sessions such as Budget day
    # 2020-02-01 are real trading days and survive; partial ones are removed by the gap rule.
    slots = session_slots(cfg)
    tod = df.index - df.index.normalize()
    in_session = tod.isin(slots)
    rep.out_of_session_rows_dropped = int((~in_session).sum())
    rep.out_of_session_dates = sorted({str(d) for d in df.index[~in_session].date})
    df = df[in_session]

    # Gaps: reindex each day to the full slot grid. Runs of at most `max_ffill_gap` missing
    # bars become flat bars at the previous close; any longer run drops the whole day.
    kept = []
    for day, g in df.groupby(df.index.normalize()):
        g = g.reindex(pd.DatetimeIndex([day + s for s in slots]))
        missing = g["close"].isna()
        if missing.any():
            longest = int(missing.groupby((missing != missing.shift()).cumsum()).sum().max())
            if longest > cfg["max_ffill_gap"] or missing.iloc[0]:
                rep.days_dropped_for_gaps[str(day.date())] = int(missing.sum())
                continue
            prev_close = g["close"].ffill()
            for c in OHLC:
                g[c] = g[c].fillna(prev_close)
            rep.single_bar_gaps_filled += int(missing.sum())
        kept.append(g)
    df = pd.concat(kept)
    df.index.name = "timestamp"

    # OHLC consistency: high/low must bound open and close.
    hi, lo = df[OHLC].max(axis=1), df[OHLC].min(axis=1)
    rep.ohlc_violations_fixed = int(((df["high"] < hi) | (df["low"] > lo)).sum())
    df["high"], df["low"] = hi, lo
    if (df[OHLC] <= 0).any().any():
        raise ValueError("Non-positive prices after cleaning")

    # Flags only: real events such as the 2020-03-23 crash must not be removed.
    r = np.log(df["close"]).diff()
    rep.return_outliers = [(str(t), round(float(v), 4)) for t, v in r[r.abs() > cfg["return_outlier_flag"]].items()]
    days = pd.Series(df.index.normalize().unique())
    gaps = days.diff().dt.days
    rep.calendar_gaps = [(str(days[i - 1].date()), str(days[i].date()), int(gaps[i])) for i in gaps[gaps > 4].index]

    df["source"] = "vendor_csv"  # FR-D5 auditability
    df["ingested_at"] = pd.Timestamp.now().floor("s")
    rep.final_rows, rep.final_days = len(df), len(days)
    rep.start, rep.end = str(df.index.min()), str(df.index.max())
    return df, rep


def resample_daily(df15: pd.DataFrame) -> pd.DataFrame:
    """Daily OHLC bars from the cleaned 15-minute bars (daily model + HMM)."""
    g = df15.groupby(df15.index.normalize())
    daily = pd.DataFrame({
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "n_bars": g.size(),
    })
    daily.index.name = "date"
    return daily
