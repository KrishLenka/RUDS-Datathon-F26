"""Print a data-quality report for the processed tables.

    python scripts/validate.py

Run this after build_dataset.py and paste the output into docs/DATA_QUALITY.md
(or the event website) so participants know what they're walking into.
"""
from __future__ import annotations

import pandas as pd

from common import PROCESSED_DIR


def main() -> None:
    m = pd.read_parquet(PROCESSED_DIR / "model_table.parquet")
    print(f"model_table: {len(m):,} rows, {m['ba'].nunique()} BAs, "
          f"{m['ts_utc'].min()} -> {m['ts_utc'].max()}\n")

    flags = [c for c in m if c.startswith("flag_")]
    summary = m.groupby("ba").agg(
        rows=("ts_utc", "size"),
        demand_mean_mwh=("demand_mwh", "mean"),
        demand_peak_mwh=("demand_mwh", "max"),
        temp_mean_c=("temp_c", "mean"),
        weather_coverage=("temp_c", lambda s: s.notna().mean()),
        **{f: (f, "sum") for f in flags},
    )
    with pd.option_context("display.width", 200, "display.max_columns", 50):
        print(summary.round(2))

        # EIA's own day-ahead forecast is a ready-made baseline.
        bad = m["flag_demand_nonpositive"] | m["flag_demand_spike"]
        ok = m[~bad].dropna(subset=["demand_mwh", "forecast_mwh"])
        mape = (ok["forecast_error_mwh"].abs() / ok["demand_mwh"]).groupby(ok["ba"]).mean() * 100
        print("\nEIA day-ahead forecast MAPE by BA (%) — the baseline to beat:")
        print(mape.round(2).to_string())


if __name__ == "__main__":
    main()
