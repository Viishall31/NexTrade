"""Step 2: indicators for the daily and 15-min series, time split, train-only scaler.

Writes, per frequency:
  data/processed/features_{freq}.parquet   raw (unscaled) features + split column
  data/processed/scaler_{freq}.json        mean/std fitted on the train split only
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from regime.config import ROOT, load_config
from regime.features import TrainOnlyScaler, assign_split, compute_features


def main() -> None:
    cfg = load_config()
    proc = ROOT / cfg["data"]["processed_dir"]
    fcfg = cfg["features"]
    cols = fcfg["model_columns"]
    summary = {}

    for freq, src in [("daily", "train_daily.parquet"), ("15min", "train_15min.parquet")]:
        feats = compute_features(pd.read_parquet(proc / src), fcfg, freq)
        feats["split"] = assign_split(feats.index, cfg["split"])
        scaler = TrainOnlyScaler(cols).fit(feats[feats["split"] == "train"])

        feats.to_parquet(proc / f"features_{freq}.parquet")
        scaler.save(proc / f"scaler_{freq}.json")

        scaled = scaler.transform(feats)
        counts = feats["split"].value_counts().to_dict()
        summary[freq] = {
            "rows": len(feats),
            "start": str(feats.index.min()),
            "end": str(feats.index.max()),
            "split_rows": counts,
            "val_mean_abs_z": round(float(scaled.loc[scaled["split"] == "val", cols].mean().abs().mean()), 3),
        }
        print(f"\n== {freq}: {len(feats)} rows {feats.index.min()} -> {feats.index.max()}  {counts}")
        print(feats[cols].describe().T[["mean", "std", "min", "max"]].round(4).to_string())

    (ROOT / "reports" / "02_features.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
