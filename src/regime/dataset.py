"""Step 4: sliding-window samples for the classifiers (spec section 5)."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from regime.features import TrainOnlyScaler


@dataclass
class WindowData:
    X: np.ndarray                  # (N, window, n_features) float32, train-scaled
    y: np.ndarray                  # (N,) int64 class index of the regime at t+1
    target_time: pd.DatetimeIndex  # timestamp of the target bar (t+1)
    split: np.ndarray              # split of the target bar
    classes: list

    def subset(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        m = self.split == name
        return self.X[m], self.y[m]


def build_windows(features: pd.DataFrame, regimes: pd.Series, scaler: TrainOnlyScaler,
                  window: int, classes: list) -> WindowData:
    """Window rows [t-window+1 .. t] of scaled features; target = regime at t+1.

    features and regimes must share the same index. Windows may reach back into an
    earlier split (that is past data); the sample's split is the target bar's split.
    """
    if not features.index.equals(regimes.index):
        raise ValueError("features and regimes must be aligned")
    feats = scaler.transform(features)[scaler.columns].to_numpy(np.float32)
    y_all = regimes.map({c: i for i, c in enumerate(classes)}).to_numpy()
    if np.isnan(y_all.astype(float)).any():
        raise ValueError("unknown regime label")

    ends = np.arange(window - 1, len(feats) - 1)          # t
    idx = ends[:, None] - np.arange(window)[::-1]          # rows t-window+1 .. t
    return WindowData(
        X=feats[idx],
        y=y_all[ends + 1].astype(np.int64),
        target_time=features.index[ends + 1],
        split=features["split"].to_numpy()[ends + 1],
        classes=classes,
    )


def load_windows(proc_dir, freq: str, cfg: dict, full: bool = False) -> WindowData:
    """full=False: train + val files. full=True: *_full files that also contain the test period."""
    suffix = "_full" if full else ""
    feats = pd.read_parquet(proc_dir / f"features_{freq}{suffix}.parquet")
    labels = pd.read_parquet(proc_dir / f"labels_{freq}{suffix}.parquet")
    feats = feats.loc[labels.index]   # 15-min bars before the first HMM-labelled day are dropped
    scaler = TrainOnlyScaler.load(proc_dir / f"scaler_{freq}.json")
    return build_windows(feats, labels["regime"], scaler, cfg["sequence"][freq]["window"], cfg["sequence"]["classes"])
