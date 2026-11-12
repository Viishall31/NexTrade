import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.config import load_config
from regime.dataset import build_windows
from regime.features import TrainOnlyScaler
from regime.models import ARCHITECTURES, CausalConv1d, build_model


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_window_alignment(cfg):
    """Window ends at t, target is the label at t+1, split follows the target."""
    n, cols = 12, ["a", "b"]
    idx = pd.date_range("2021-12-25", periods=n, freq="D")
    feats = pd.DataFrame({"a": np.arange(n, dtype=float), "b": np.arange(n, dtype=float) * 10}, index=idx)
    feats["split"] = np.where(idx <= "2021-12-31", "train", "val")
    classes = ["bull", "bear", "sideways", "high_vol"]
    regimes = pd.Series([classes[i % 4] for i in range(n)], index=idx)
    scaler = TrainOnlyScaler(cols)
    scaler.mean_, scaler.std_ = {"a": 0.0, "b": 0.0}, {"a": 1.0, "b": 1.0}

    w = build_windows(feats, regimes, scaler, window=3, classes=classes)
    assert w.X.shape == (n - 3, 3, 2)
    for i in range(len(w.y)):
        t = i + 2
        assert list(w.X[i, :, 0]) == [t - 2, t - 1, t]          # only bars <= t
        assert w.y[i] == (t + 1) % 4                             # label of t+1
        assert w.target_time[i] == idx[t + 1]
        assert w.split[i] == feats["split"].iloc[t + 1]


@pytest.mark.parametrize("arch", list(ARCHITECTURES))
@pytest.mark.parametrize("window", [30, 48])
def test_output_shape(cfg, arch, window):
    model = build_model(arch, 13, 4, cfg["models"][arch])
    assert model(torch.randn(5, window, 13)).shape == (5, 4)


def test_causal_conv_ignores_future():
    torch.manual_seed(0)
    conv = CausalConv1d(3, 4, 3)
    x = torch.randn(1, 3, 10)
    y = x.clone()
    y[..., 6:] = torch.randn(1, 3, 4)
    assert torch.allclose(conv(x)[..., :6], conv(y)[..., :6])
