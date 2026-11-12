"""Step 7b: preprocess Nifty50_test.csv with the frozen training pipeline. Nothing is refit.

- Cleaning: same rules as Step 1.
- Features: computed on [cleaned train bars + cleaned test bars] so indicators at the start of
  the test period have real history (all indicators are causal, so this uses only past data).
- Scaling: frozen train scaler (applied later when windows are built).
- Labels: frozen HMM, filtered forward pass run over the whole series so the state belief
  carries over into the test period exactly as it would live.

Writes data/processed/test_{15min,daily}.parquet, features_{freq}_full.parquet,
labels_{freq}_full.parquet, and reports/07_test_data.json.
"""
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT, load_config
from regime.data import clean_15min, resample_daily
from regime.features import assign_split, compute_features
from regime.hmm import RegimeHMM


def main() -> None:
    cfg = load_config()
    dcfg = cfg["data"]
    proc = ROOT / dcfg["processed_dir"]

    test15, rep = clean_15min(dcfg["test_csv"], dcfg)
    train15 = pd.read_parquet(proc / "train_15min.parquet")
    if test15.index.min() <= train15.index.max():
        raise ValueError("test data overlaps the training data")
    test15.to_parquet(proc / "test_15min.parquet")
    resample_daily(test15).to_parquet(proc / "test_daily.parquet")

    hmm = RegimeHMM.load(ROOT / "models" / "hmm_daily.pkl")
    full15 = pd.concat([train15, test15])
    daily_full = resample_daily(full15)
    summary = {"cleaning": asdict(rep)}

    # Daily features + frozen-HMM labels over the whole history.
    feats_d = compute_features(daily_full, cfg["features"], "daily")
    feats_d["split"] = assign_split(feats_d.index, cfg["split"])
    labels_d = hmm.label(feats_d)
    labels_d["split"] = feats_d["split"]

    # Integrity: the pre-test part must match what training used exactly.
    old_f = pd.read_parquet(proc / "features_daily.parquet")
    old_l = pd.read_parquet(proc / "labels_daily.parquet")
    pd.testing.assert_frame_equal(feats_d.loc[old_f.index], old_f)
    pd.testing.assert_series_equal(labels_d.loc[old_l.index, "regime"], old_l["regime"])

    feats_d.to_parquet(proc / "features_daily_full.parquet")
    labels_d.to_parquet(proc / "labels_daily_full.parquet")

    # 15-min features; bars inherit their day's regime (Step 3, option A).
    feats_15 = compute_features(full15, cfg["features"], "15min")
    feats_15["split"] = assign_split(feats_15.index, cfg["split"])
    old_f15 = pd.read_parquet(proc / "features_15min.parquet")
    pd.testing.assert_frame_equal(feats_15.loc[old_f15.index], old_f15)
    labels_15 = pd.DataFrame({"regime": labels_d["regime"].reindex(feats_15.index.normalize()).to_numpy(),
                              "split": feats_15["split"]}, index=feats_15.index).dropna(subset=["regime"])
    feats_15.to_parquet(proc / "features_15min_full.parquet")
    labels_15.to_parquet(proc / "labels_15min_full.parquet")

    test_reg = labels_d.loc[labels_d["split"] == "test", "regime"]
    summary.update({
        "test_days": int(len(test_reg)), "test_15min_bars": int((labels_15["split"] == "test").sum()),
        "test_period": [str(test_reg.index.min().date()), str(test_reg.index.max().date())],
        "test_regime_share": test_reg.value_counts(normalize=True).round(3).to_dict(),
        "test_regime_days": test_reg.value_counts().to_dict(),
        "by_month": test_reg.groupby(test_reg.index.to_period("M")).agg(lambda s: s.value_counts().idxmax()).astype(str)
                    .rename(lambda p: str(p)).to_dict(),
        "integrity": "pre-test features and labels identical to training files",
    })
    (ROOT / "reports" / "07_test_data.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != "cleaning"}, indent=2, default=str))
    print("cleaning:", {k: v for k, v in summary["cleaning"].items() if k in
                        ["raw_rows", "duplicate_rows_dropped", "out_of_session_rows_dropped", "days_dropped_for_gaps",
                         "single_bar_gaps_filled", "return_outliers", "final_rows", "final_days", "start", "end"]})


if __name__ == "__main__":
    main()
