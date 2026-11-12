import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.config import ROOT
from regime.hmm import RegimeHMM

PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def hmm_and_daily():
    m, f = ROOT / "models" / "hmm_daily.pkl", PROCESSED / "features_daily.parquet"
    if not (m.exists() and f.exists()):
        pytest.skip("run scripts/03_label_regimes.py first")
    return RegimeHMM.load(m), pd.read_parquet(f)


def test_labels_are_causal(hmm_and_daily):
    """A day's label must not change when later days are removed or altered."""
    hmm, daily = hmm_and_daily
    full = hmm.label(daily)
    cut = daily.index[1000]
    pd.testing.assert_frame_equal(full.loc[:cut], hmm.label(daily.loc[:cut]))
    tampered = daily.copy()
    tampered.loc[tampered.index > cut, hmm.emissions] *= -3
    pd.testing.assert_frame_equal(full.loc[:cut], hmm.label(tampered).loc[:cut])


def test_four_named_regimes(hmm_and_daily):
    hmm, daily = hmm_and_daily
    assert sorted(hmm.state_to_label.values()) == ["bear", "bull", "high_vol", "sideways"]
    post = hmm.label(daily).filter(like="p_")
    assert np.allclose(post.sum(axis=1), 1)


def test_hmm_statistics_from_train_only(hmm_and_daily):
    hmm, daily = hmm_and_daily
    train = daily.loc[daily["split"] == "train", hmm.emissions].to_numpy()
    assert np.allclose(hmm.emission_mean, train.mean(axis=0))


def test_15min_labels_match_day():
    p15, pd_ = PROCESSED / "labels_15min.parquet", PROCESSED / "labels_daily.parquet"
    if not (p15.exists() and pd_.exists()):
        pytest.skip("run scripts/03_label_regimes.py first")
    l15, ld = pd.read_parquet(p15), pd.read_parquet(pd_)
    assert (l15["regime"].to_numpy() == ld["regime"].reindex(l15.index.normalize()).to_numpy()).all()


def test_forward_step_matches_batch_filter(hmm_and_daily):
    """Live one-step updates must reproduce the batch filtered posterior exactly."""
    hmm, daily = hmm_and_daily
    batch = hmm.filtered_posterior(daily.iloc[:300])
    log_post = np.log(np.maximum(batch[199], 1e-300))
    for t in range(200, 300):
        log_post = hmm.forward_step(log_post, daily.iloc[[t]])
        assert np.allclose(np.exp(log_post), batch[t], atol=1e-9)
