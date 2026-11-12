"""Step 9: bar-by-bar "live" pipeline used for the walk-forward replay (spec section 10).

Everything is incremental, exactly as a live feed would be processed:
- on_bar(bar):      append the 15-min bar, recompute features on a trailing buffer, predict the
                    regime with the frozen seed ensemble, return a log record.
- on_day_close():   aggregate the day to a daily bar, recompute daily features, advance the frozen
                    HMM by one forward step -> that day's ground-truth regime label.
No component places orders (constraint C-4); there is no broker code in this project.
"""
import time

import numpy as np
import pandas as pd
import torch

from regime.data import resample_daily
from regime.features import TrainOnlyScaler, compute_features
from regime.hmm import RegimeHMM
from regime.train import predict_proba

OHLC = ["open", "high", "low", "close"]


class LivePipeline:
    def __init__(self, cfg: dict, history_15m: pd.DataFrame, models: list, scaler: TrainOnlyScaler, hmm: RegimeHMM):
        self.cfg = cfg
        self.fcfg = cfg["features"]
        self.window = cfg["sequence"]["15min"]["window"]
        self.buffer_bars = cfg["replay"]["feature_buffer_bars"]
        self.classes = cfg["sequence"]["classes"]
        self.threshold = cfg["selection"]["low_confidence_threshold"]
        self.models = models
        self.scaler = scaler
        self.hmm = hmm
        self.bars = history_15m[OHLC].copy()

        # HMM state at the end of the history: run the frozen filter once over past daily data.
        daily_feats = compute_features(resample_daily(self.bars), self.fcfg, "daily")
        post = hmm.filtered_posterior(daily_feats)
        self.log_post = np.log(np.maximum(post[-1], 1e-300))

    def on_bar(self, ts: pd.Timestamp, bar: dict) -> dict:
        start = time.perf_counter()
        self.bars.loc[ts, OHLC] = [bar[c] for c in OHLC]
        recent = self.bars.iloc[-self.buffer_bars:]
        feats = compute_features(recent, self.fcfg, "15min")
        scaled = self.scaler.transform(feats.iloc[-self.window:])[self.scaler.columns].to_numpy(np.float32)
        X = scaled[None, :, :]
        prob = np.mean([predict_proba(m, X)[0] for m in self.models], axis=0)
        k = int(prob.argmax())
        return {
            "timestamp": ts, "close": bar["close"],
            **{f"f_{c}": float(feats[c].iloc[-1]) for c in self.scaler.columns},
            "predicted_regime": self.classes[k], "confidence": float(prob[k]),
            "low_confidence": bool(prob[k] < self.threshold),
            **{f"p_{c}": float(prob[i]) for i, c in enumerate(self.classes)},
            "latency_ms": (time.perf_counter() - start) * 1e3,
        }

    def on_day_close(self, day: pd.Timestamp) -> dict:
        daily = resample_daily(self.bars)
        feats = compute_features(daily, self.fcfg, "daily")
        if feats.index[-1] != day.normalize():
            raise ValueError(f"day close called for {day} but last daily bar is {feats.index[-1]}")
        self.log_post = self.hmm.forward_step(self.log_post, feats.iloc[[-1]])
        state = int(self.log_post.argmax())
        return {"date": day.normalize(), "regime": self.hmm.state_to_label[state],
                "posterior": float(np.exp(self.log_post[state]))}


def load_ensemble(arch: str, hp: dict, weights_dir, n_features: int, n_classes: int) -> list:
    from regime.models import build_model
    models = []
    for path in sorted(weights_dir.glob(f"{arch}_seed*.pt")):
        m = build_model(arch, n_features, n_classes, hp)
        m.load_state_dict(torch.load(path, map_location="cpu"))
        m.eval()
        models.append(m)
    if not models:
        raise FileNotFoundError(f"no {arch} weights in {weights_dir}")
    return models
