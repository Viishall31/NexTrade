"""Step 1: clean the training CSV -> 15-min + daily parquet files and a cleaning report."""
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from regime.config import ROOT, load_config
from regime.data import clean_15min, resample_daily


def main() -> None:
    dcfg = load_config()["data"]
    out = ROOT / dcfg["processed_dir"]
    out.mkdir(parents=True, exist_ok=True)

    df15, rep = clean_15min(dcfg["train_csv"], dcfg)
    daily = resample_daily(df15)

    df15.to_parquet(out / "train_15min.parquet")
    daily.to_parquet(out / "train_daily.parquet")
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "01_data_cleaning.json").write_text(json.dumps(asdict(rep), indent=2))

    print(f"raw rows                 {rep.raw_rows}")
    print(f"duplicate rows dropped   {rep.duplicate_rows_dropped} ({rep.duplicate_days} days, {rep.conflicting_duplicate_bars} conflicting bars)")
    print(f"out-of-session dropped   {rep.out_of_session_rows_dropped} rows on {rep.out_of_session_dates}")
    print(f"single-bar gaps filled   {rep.single_bar_gaps_filled}")
    print(f"days dropped for gaps    {rep.days_dropped_for_gaps}")
    print(f"OHLC violations fixed    {rep.ohlc_violations_fixed}")
    print(f"|15m logret| flagged     {rep.return_outliers}")
    print(f"calendar gaps > 4 days   {rep.calendar_gaps}")
    print(f"final                    {rep.final_rows} bars, {rep.final_days} days, {rep.start} -> {rep.end}")
    print(f"daily bars               {len(daily)}")


if __name__ == "__main__":
    main()
