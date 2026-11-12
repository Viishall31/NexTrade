"""Step 12a: fresh out-of-sample data (Apr 2025 -> latest) from yfinance, run through the frozen pipeline.

Nothing is refit or re-selected: frozen scaler, frozen HMM, tuned 5-seed daily models for all three
architectures. Vendor daily bars are used up to the end of Nifty50_test.csv; yfinance daily bars after it.

Usage: python scripts/12_prepare_fresh.py [--refresh]
Writes data/raw/yfinance_nsei_daily.csv (cached download), data/processed/{features,labels}_daily_fresh.parquet,
data/processed/signals_daily_{arch}_fresh.parquet and reports/12_fresh_data.json
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.dataset import build_windows
from regime.features import TrainOnlyScaler, assign_split, compute_features
from regime.hmm import RegimeHMM
from regime.models import ARCHITECTURES
from regime.replay import load_ensemble
from regime.train import predict_proba

OHLC = ["open", "high", "low", "close"]


def download(fcfg: dict, path: Path, refresh: bool) -> pd.DataFrame:
    if path.exists() and not refresh:
        return pd.read_csv(path, index_col="date", parse_dates=["date"])
    import yfinance as yf
    end = (pd.Timestamp.now().normalize() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    y = yf.download(fcfg["ticker"], start=fcfg["history_start"], end=end, interval="1d", auto_adjust=False, progress=False)
    if isinstance(y.columns, pd.MultiIndex):
        y.columns = y.columns.get_level_values(0)
    y = y.rename(columns=str.lower)[OHLC + ["volume"]]
    y.index = pd.DatetimeIndex(y.index).tz_localize(None).normalize()
    y.index.name = "date"
    y["downloaded_at"] = datetime.now().isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    y.to_csv(path)
    return y


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="download again instead of using the cached CSV")
    args = ap.parse_args()
    cfg = load_config()
    fcfg, classes = cfg["fresh"], cfg["sequence"]["classes"]
    proc, rep = ROOT / cfg["data"]["processed_dir"], ROOT / "reports"
    test_end = pd.Timestamp(fcfg["test_end"])

    raw = download(fcfg, ROOT / fcfg["raw_csv"], args.refresh)
    y = raw.dropna(subset=["close"]).copy()
    incomplete = raw.index.difference(y.index)

    # Special sessions (Muhurat etc.) are dropped, as the vendor pipeline does. Low-volume days are only
    # reported: yfinance index volume has glitches on normal trading days.
    vol_med = y["volume"].rolling(20, min_periods=5).median().shift(1)
    low_volume = y.index[(y["volume"] < fcfg["low_volume_warning_ratio"] * vol_med) & (y.index > test_end)]
    special = y.index[y.index.isin(pd.DatetimeIndex(fcfg["special_sessions"])) | (y.index.dayofweek >= 5)]
    y = y.drop(index=special)
    bad = (y["high"] < y[["open", "close"]].max(axis=1)) | (y["low"] > y[["open", "close"]].min(axis=1)) | (y[OHLC] <= 0).any(axis=1)
    if bad.any():
        raise ValueError(f"invalid OHLC rows: {list(y.index[bad])}")

    vendor = pd.concat([pd.read_parquet(proc / "train_daily.parquet"), pd.read_parquet(proc / "test_daily.parquet")])[OHLC]
    fresh_bars = y.loc[y.index > test_end, OHLC]
    overlap = vendor.join(y[OHLC], rsuffix="_yf", how="inner")
    close_diff = (overlap["close"] / overlap["close_yf"] - 1).abs()
    ret_corr = float(np.log(overlap["close"]).diff().corr(np.log(overlap["close_yf"]).diff()))

    daily = pd.concat([vendor, fresh_bars])
    daily.index.name = "date"
    feats = compute_features(daily, cfg["features"], "daily")
    feats["split"] = assign_split(feats.index, cfg["split"]).where(feats.index <= test_end, "fresh")

    old = pd.read_parquet(proc / "features_daily_full.parquet")
    pd.testing.assert_frame_equal(feats.loc[old.index].drop(columns="split"), old.drop(columns="split"))
    hmm = RegimeHMM.load(ROOT / "models" / "hmm_daily.pkl")
    labels = hmm.label(feats)
    labels["split"] = feats["split"]
    old_l = pd.read_parquet(proc / "labels_daily_full.parquet")
    pd.testing.assert_series_equal(labels.loc[old_l.index, "regime"], old_l["regime"])
    feats.to_parquet(proc / "features_daily_fresh.parquet")
    labels.to_parquet(proc / "labels_daily_fresh.parquet")

    scaler = TrainOnlyScaler.load(proc / "scaler_daily.json")
    win = build_windows(feats, labels["regime"], scaler, cfg["sequence"]["daily"]["window"], classes)
    keep = win.split == "fresh"
    next_time = win.target_time[keep]
    decision_time = feats.index[feats.index.get_indexer(next_time) - 1]
    base = pd.DataFrame({"decision_time": decision_time, "next_time": next_time, "split": "fresh",
                         "price_now": feats["close"].reindex(decision_time).to_numpy(),
                         "price_next": feats["close"].reindex(next_time).to_numpy(),
                         "true_regime": np.asarray(classes)[win.y[keep]]})
    if not (base["next_time"].iloc[:-1].to_numpy() == base["decision_time"].iloc[1:].to_numpy()).all():
        raise ValueError("non-contiguous fresh decision bars")
    for arch in ARCHITECTURES:
        hp = json.loads((rep / f"06_tuning_daily_{arch}.json").read_text())["chosen"]["model_hp"]
        models = load_ensemble(arch, hp, ROOT / "models" / "tuned_daily", win.X.shape[2], len(classes))
        prob = np.mean([predict_proba(m, win.X[keep]) for m in models], axis=0)
        base.assign(**{f"p_{c}": prob[:, i] for i, c in enumerate(classes)}).to_parquet(proc / f"signals_daily_{arch}_fresh.parquet")

    fresh_labels = labels.loc[labels["split"] == "fresh", "regime"]
    summary = {
        "prepared_at": datetime.now().isoformat(timespec="seconds"), "source": f"{fcfg['source']} {fcfg['ticker']}",
        "downloaded_at": str(raw["downloaded_at"].iloc[0]) if "downloaded_at" in raw else None,
        "fresh_period": [str(fresh_bars.index.min().date()), str(fresh_bars.index.max().date())],
        "fresh_days": int(len(fresh_bars)), "fresh_decisions": int(keep.sum()),
        "dropped_incomplete_rows": [str(d.date()) for d in incomplete],
        "dropped_special_sessions_fresh": [str(d.date()) for d in special if d > test_end],
        "low_volume_days_kept": [str(d.date()) for d in low_volume if d not in special],
        "overlap_check": {"days": int(len(overlap)), "close_median_abs_diff_pct": float(100 * close_diff.median()),
                          "close_p95_abs_diff_pct": float(100 * close_diff.quantile(0.95)), "daily_return_corr": ret_corr},
        "integrity": "features and HMM labels up to 2025-04-07 identical to the Step 7 files",
        "fresh_label_counts": fresh_labels.value_counts().to_dict(),
        "fresh_label_by_month": fresh_labels.groupby(fresh_labels.index.to_period("M"))
                                            .agg(lambda s: s.value_counts().idxmax()).rename(lambda p: str(p)).to_dict(),
        "nifty_first_last": [float(fresh_bars["close"].iloc[0]), float(fresh_bars["close"].iloc[-1])],
    }
    (rep / "12_fresh_data.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
