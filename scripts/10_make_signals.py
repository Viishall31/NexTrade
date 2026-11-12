"""Step 10a: model signals for trading -- seed-ensemble probabilities on validation and test.

Usage: python scripts/10_make_signals.py --freq daily|15min [--arch lstm|cnn_bilstm_attn|transformer]
(default arch = the selected one). Writes data/processed/signals_{freq}_{arch}.parquet with one row per decision bar:
  decision_time, next_time, split, price_now, price_next, p_bull..p_high_vol, true_regime (t+1)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.dataset import load_windows
from regime.replay import load_ensemble
from regime.train import predict_proba


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freq", choices=["daily", "15min"], required=True)
    ap.add_argument("--arch", choices=["lstm", "cnn_bilstm_attn", "transformer"], default=None)
    args = ap.parse_args()
    cfg = load_config()
    proc, rep = ROOT / cfg["data"]["processed_dir"], ROOT / "reports"
    classes = cfg["sequence"]["classes"]
    arch = args.arch or json.loads((rep / "07_selection.json").read_text())["selected"]
    hp = json.loads((rep / f"06_tuning_daily_{arch}.json").read_text())["chosen"]["model_hp"]

    data = load_windows(proc, args.freq, cfg, full=True)
    keep = np.isin(data.split, ["val", "test"])
    models = load_ensemble(arch, hp, ROOT / "models" / f"tuned_{args.freq}", data.X.shape[2], len(classes))
    prob = np.mean([predict_proba(m, data.X[keep]) for m in models], axis=0)

    close = pd.read_parquet(proc / f"features_{args.freq}_full.parquet")["close"]
    next_time = data.target_time[keep]
    decision_time = close.index[close.index.get_indexer(next_time) - 1]
    out = pd.DataFrame({
        "decision_time": decision_time, "next_time": next_time, "split": data.split[keep],
        "price_now": close.reindex(decision_time).to_numpy(), "price_next": close.reindex(next_time).to_numpy(),
        **{f"p_{c}": prob[:, i] for i, c in enumerate(classes)},
        "true_regime": np.asarray(classes)[data.y[keep]],
    })
    # decision bars must be consecutive: each position is marked at the next decision bar
    within = out.groupby("split")
    for split, g in within:
        if not (g["next_time"].iloc[:-1].to_numpy() == g["decision_time"].iloc[1:].to_numpy()).all():
            raise ValueError(f"non-contiguous decision bars in {split}")
    out.to_parquet(proc / f"signals_{args.freq}_{arch}.parquet")
    print(f"{args.freq} {arch}: {len(models)} models | " + ", ".join(f"{s}: {n} bars" for s, n in out["split"].value_counts().items()))


if __name__ == "__main__":
    main()
