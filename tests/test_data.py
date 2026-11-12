import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.config import ROOT, load_config

PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def df15():
    p = PROCESSED / "train_15min.parquet"
    if not p.exists():
        pytest.skip("run scripts/01_clean_data.py first")
    return pd.read_parquet(p)


def test_unique_sorted(df15):
    assert df15.index.is_unique and df15.index.is_monotonic_increasing


def test_every_day_has_full_session(df15):
    cfg = load_config()["data"]
    assert (df15.groupby(df15.index.normalize()).size() == 25).all()
    tod = df15.index - df15.index.normalize()
    assert tod.min() == pd.Timedelta(cfg["session_start"] + ":00")
    assert tod.max() == pd.Timedelta(cfg["session_last_bar"] + ":00")


def test_ohlc_valid(df15):
    assert (df15[["open", "high", "low", "close"]] > 0).all().all()
    assert (df15["high"] >= df15[["open", "close"]].max(axis=1)).all()
    assert (df15["low"] <= df15[["open", "close"]].min(axis=1)).all()


def test_no_muhurat_or_partial_sessions(df15):
    days = set(df15.index.normalize().date.astype(str))
    assert not {"2016-10-30", "2023-11-12", "2024-03-02", "2021-02-24"} & days
    assert "2020-02-01" in days  # full Budget-day Saturday session is kept


def test_vendor_indicators_dropped(df15):
    assert not {"200_EMA", "pivot"} & set(df15.columns)
