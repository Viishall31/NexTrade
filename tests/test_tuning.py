import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from optuna.trial import FixedTrial

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from regime.config import load_config
from regime.models import build_model
from regime.tuning import normalized_sharpe, suggest_hparams, tuning_objective


@pytest.fixture(scope="module")
def cfg():
    return load_config()


EXTREMES = [
    {"lr": 1e-4, "batch_size": 16, "dropout": 0.1, "hidden": 32, "layers": 1, "heads": 8, "ff_dim": 64},
    {"lr": 1e-2, "batch_size": 128, "dropout": 0.5, "hidden": 256, "layers": 3, "heads": 2, "ff_dim": 256},
]


@pytest.mark.parametrize("arch", ["lstm", "cnn_bilstm_attn", "transformer"])
@pytest.mark.parametrize("params", EXTREMES)
def test_search_space_corners_build(cfg, arch, params):
    space = cfg["tuning"]["search_space"]
    used = {k: v for k, v in params.items() if arch == "transformer" or k not in ("heads", "ff_dim")}
    if arch == "transformer":
        used.pop("layers")
    hp, train_hp = suggest_hparams(FixedTrial(used), arch, cfg["models"], cfg["training"], space)
    assert train_hp["lr"] == params["lr"] and train_hp["max_epochs"] == cfg["training"]["max_epochs"]
    model = build_model(arch, 13, 4, hp)
    assert model(torch.randn(2, 30, 13)).shape == (2, 4)


def test_normalized_sharpe():
    assert normalized_sharpe(-5, -1, 2) == 0.0
    assert normalized_sharpe(0.5, -1, 2) == 0.5
    assert normalized_sharpe(9, -1, 2) == 1.0


def test_objective_weights(cfg):
    classes = cfg["sequence"]["classes"]
    y = np.array([0, 1, 2, 3] * 20)
    r = np.zeros(len(y))
    res = tuning_objective(y, y, r, classes, cfg["backtest"], cfg["tuning"]["objective"], "daily")
    assert res["macro_f1"] == 1.0
    lo, hi = cfg["tuning"]["objective"]["sharpe_range"]
    expected = 0.6 * 1.0 + 0.4 * normalized_sharpe(res["sharpe"], lo, hi)
    assert np.isclose(res["objective"], expected)
