"""Step 3: fit the HMM on daily train data, label daily + 15-min bars, sanity-check, plot.

Writes:
  models/hmm_daily.pkl                      frozen HMM
  data/processed/labels_daily.parquet       per-day filtered posteriors + regime
  data/processed/labels_15min.parquet       15-min bars with their day's regime
  reports/03_hmm.json, reports/03_regimes.png
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from regime.config import ROOT, load_config
from regime.hmm import bic_table, fit_regime_hmm

COLORS = {"bull": "#2e9e5b", "bear": "#d6453d", "sideways": "#9aa0a6", "high_vol": "#e8a33d"}


def share(labels: pd.Series, start: str, end: str) -> dict:
    return labels.loc[start:end].value_counts(normalize=True).round(3).to_dict()


def main() -> None:
    cfg = load_config()
    proc = ROOT / cfg["data"]["processed_dir"]
    hcfg = cfg["hmm"]
    (ROOT / "models").mkdir(exist_ok=True)

    daily = pd.read_parquet(proc / "features_daily.parquet")
    train = daily[daily["split"] == "train"]

    hmm, stats = fit_regime_hmm(train, hcfg, cfg["seed"])
    hmm.save(ROOT / "models" / "hmm_daily.pkl")
    bic = bic_table(train, hcfg, cfg["seed"])

    labels = hmm.label(daily)
    labels["split"] = daily["split"]
    labels.to_parquet(proc / "labels_daily.parquet")
    reg = labels["regime"]

    # 15-min bars inherit their day's label; bars before the first labelled day are dropped.
    f15 = pd.read_parquet(proc / "features_15min.parquet")
    day = f15.index.normalize()
    l15 = pd.DataFrame({"regime": reg.reindex(day).to_numpy(), "split": f15["split"]}, index=f15.index)
    l15 = l15.dropna(subset=["regime"])
    l15.to_parquet(proc / "labels_15min.parquet")

    runs = (reg != reg.shift()).cumsum()
    report = {
        "state_stats_train": stats.round(5).reset_index(names="state").to_dict(orient="records"),
        "transition_matrix": np.round(hmm.model.transmat_, 3).tolist(),
        "bic": bic.round(1).reset_index().to_dict(orient="records"),
        "bic_best_k": int(bic["bic"].idxmin()),
        "label_share": {s: reg[labels["split"] == s].value_counts(normalize=True).round(3).to_dict() for s in ["train", "val"]},
        "mean_regime_duration_days": reg.groupby(runs).size().groupby(reg.groupby(runs).first()).mean().round(1).to_dict(),
        "switches_per_year": round(float((reg != reg.shift()).sum() / (len(reg) / 252)), 1),
        "check_2020_feb_apr": share(reg, "2020-02-15", "2020-04-30"),
        "check_2021": share(reg, "2021-01-01", "2021-12-31"),
        "check_2022_h1": share(reg, "2022-01-01", "2022-06-30"),
        "check_2018_sep_oct": share(reg, "2018-09-01", "2018-10-31"),
        "check_2023": share(reg, "2023-01-01", "2023-12-31"),
        "rows_15min_labelled": len(l15),
    }
    (ROOT / "reports" / "03_hmm.json").write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    for name, color in COLORS.items():
        m = reg == name
        ax1.scatter(daily.index[m], daily["close"][m], s=4, color=color, label=name)
    ax1.axvline(pd.Timestamp(cfg["split"]["val_start"]), color="k", ls="--", lw=1)
    ax1.set_ylabel("Nifty 50 close")
    ax1.set_title("HMM regimes (filtered, frozen train-fit HMM) — dashed line = start of validation")
    ax1.legend(markerscale=4, loc="upper left")
    ax2.plot(daily.index, daily["ret20"], color="#555", lw=0.8)
    ax2.axhline(0, color="k", lw=0.5)
    ax2.set_ylabel("20d log return")
    fig.tight_layout()
    fig.savefig(ROOT / "reports" / "03_regimes.png", dpi=110)


if __name__ == "__main__":
    main()
