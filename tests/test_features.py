"""Leakage tests for the feature pipeline (FR-F4, C-1)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.config import ROOT, load_config
from regime.features import TrainOnlyScaler, assign_split, compute_features

PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def daily():
    p = PROCESSED / "train_daily.parquet"
    if not p.exists():
        pytest.skip("run scripts/01_clean_data.py first")
    return pd.read_parquet(p)


def test_features_are_causal(daily, cfg):
    """No look-ahead: features up to a cut-off must not change when later bars are removed,
    and must not change when later bars are replaced by garbage."""
    full = compute_features(daily, cfg["features"], "daily")
    cut = daily.index[1200]
    truncated = compute_features(daily[daily.index <= cut], cfg["features"], "daily")
    pd.testing.assert_frame_equal(full.loc[:cut], truncated, check_exact=False, rtol=1e-10)

    tampered = daily.copy()
    after = tampered.index > cut
    tampered.loc[after, ["open", "high", "low", "close"]] *= np.random.default_rng(0).uniform(0.5, 1.5, (after.sum(), 1))
    pd.testing.assert_frame_equal(full.loc[:cut], compute_features(tampered, cfg["features"], "daily").loc[:cut],
                                  check_exact=False, rtol=1e-10)


def test_features_are_sensitive_to_data(daily, cfg):
    """FR-F4 guard: the leakage test above is meaningless if features ignore their inputs."""
    full = compute_features(daily, cfg["features"], "daily")
    cut = daily.index[1200]
    # Per-bar random noise on all OHLC (a constant multiplier would leave ratio features unchanged).
    tampered = daily.copy()
    after = tampered.index > cut
    tampered.loc[after, ["open", "high", "low", "close"]] *= np.random.default_rng(1).uniform(0.9, 1.1, (after.sum(), 1))
    changed = compute_features(tampered, cfg["features"], "daily")
    later = full.index > cut
    for col in cfg["features"]["model_columns"]:
        assert not np.allclose(full.loc[later, col], changed.loc[later, col]), col


def test_scaler_uses_train_only(daily, cfg):
    feats = compute_features(daily, cfg["features"], "daily")
    feats["split"] = assign_split(feats.index, cfg["split"])
    cols = cfg["features"]["model_columns"]
    s1 = TrainOnlyScaler(cols).fit(feats[feats["split"] == "train"])
    shifted = feats.copy()
    shifted.loc[shifted["split"] != "train", cols] += 1000
    s2 = TrainOnlyScaler(cols).fit(shifted[shifted["split"] == "train"])
    assert s1.mean_ == s2.mean_ and s1.std_ == s2.std_


def test_split_is_time_ordered(cfg):
    for freq in ["daily", "15min"]:
        p = PROCESSED / f"features_{freq}.parquet"
        if not p.exists():
            pytest.skip("run scripts/02_build_features.py first")
        f = pd.read_parquet(p)
        assert f.index[f["split"] == "train"].max() < f.index[f["split"] == "val"].min()
        assert set(f["split"]) <= {"train", "val"}
        assert len(cfg["features"]["model_columns"]) == 13
