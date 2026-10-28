"""Generate SYNTHETIC raw files that mimic the EIA API and GHCNh formats.

This exists so the pipeline (and starter code) can be tested offline. The
numbers are fake — never use them for analysis. Known problems are injected on
purpose (missing hours, a zero, a spike, a fuel-category switch) so the
cleaning flags have something to catch.

    DATATHON_DATA_DIR=/tmp/sample python tests/make_sample_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from common import RAW_DIR, ensure_dirs, load_config  # noqa: E402

rng = np.random.default_rng(7)
BASE_LOAD = {"PJM": 90000, "ERCO": 50000, "CISO": 27000, "NYIS": 18000, "ISNE": 14000}
START, END = "2024-05-01", "2024-09-30"


def synth_temp(idx: pd.DatetimeIndex, offset: float) -> np.ndarray:
    doy = idx.dayofyear.values
    hr = idx.hour.values
    seasonal = 12 - 14 * np.cos(2 * np.pi * (doy - 15) / 365)
    diurnal = 5 * np.sin(2 * np.pi * (hr - 15) / 24)
    return seasonal + diurnal + offset + rng.normal(0, 1.5, len(idx))


def main() -> None:
    cfg = load_config()
    ensure_dirs()
    idx = pd.date_range(START, f"{END} 23:00", freq="h", tz="UTC")
    periods = idx.strftime("%Y-%m-%dT%H")

    for ba, region in cfg["regions"].items():
        offset = {"ERCO": 6, "CISO": 2}.get(ba, 0)
        temp = synth_temp(idx, offset)
        demand = BASE_LOAD[ba] * (1 + 0.025 * np.clip(temp - 18, 0, None)
                                  + 0.012 * np.clip(18 - temp, 0, None)
                                  + 0.15 * np.sin(2 * np.pi * (idx.hour.values - 6) / 24))
        demand = demand + rng.normal(0, BASE_LOAD[ba] * 0.01, len(idx))
        forecast = demand * (1 + rng.normal(0, 0.03, len(idx)))
        demand[100] = 0                 # bad zero
        demand[200] = demand[200] * 3   # spike
        keep = np.ones(len(idx), bool)
        keep[300:305] = False           # 5-hour reporting gap

        rows = []
        for code, vals in (("D", demand), ("DF", forecast), ("NG", demand * 0.97), ("TI", demand * -0.03)):
            for p, v, k in zip(periods, vals, keep):
                if k:
                    rows.append({"period": p, "respondent": ba, "type": code,
                                 "type-name": code, "value": str(round(v)), "value-units": "megawatthours"})
        pd.DataFrame(rows).to_parquet(RAW_DIR / "eia" / f"region_data_{ba}.parquet", index=False)

        solar = np.clip(np.sin(np.pi * (idx.hour.values - 11) / 14), 0, None) * BASE_LOAD[ba] * 0.15
        wind = np.abs(rng.normal(0.08, 0.04, len(idx))) * BASE_LOAD[ba]
        switch = idx >= pd.Timestamp("2024-07-01", tz="UTC")  # mimic EIA's category split
        rows = []
        for i, p in enumerate(periods):
            if switch[i]:
                fuels = [("SNB", "Solar with integrated battery storage", solar[i] * 0.3),
                         ("SUN", "Solar without integrated battery storage", solar[i] * 0.7),
                         ("WND", "Wind without integrated battery storage", wind[i])]
            else:
                fuels = [("SUN", "Solar", solar[i]), ("WND", "Wind", wind[i])]
            fuels += [("NG", "Natural Gas", demand[i] * 0.4), ("NUC", "Nuclear", BASE_LOAD[ba] * 0.2)]
            for code, name, v in fuels:
                rows.append({"period": p, "respondent": ba, "fueltype": code,
                             "type-name": name, "value": str(round(v)), "value-units": "megawatthours"})
        pd.DataFrame(rows).to_parquet(RAW_DIR / "eia" / f"fuel_type_{ba}.parquet", index=False)

        for j, st in enumerate(region["stations"]):
            t = temp + rng.normal(0, 1, len(idx)) + j
            obs_time = idx + pd.Timedelta(minutes=51) - pd.Timedelta(hours=1)  # METAR-style :51 obs
            df = pd.DataFrame({
                "Station_ID": st["id"],
                "DATE": obs_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "temperature": t.round(1),
                "dew_point_temperature": (t - rng.uniform(2, 10, len(idx))).round(1),
                "relative_humidity": rng.uniform(30, 95, len(idx)).round(0),
                "wind_speed": rng.uniform(0, 10, len(idx)).round(1),
                "precipitation": np.where(rng.random(len(idx)) < 0.05, rng.uniform(0, 5, len(idx)), 0).round(1),
            })
            df.loc[50, "temperature"] = 999.9  # sentinel-style bad value
            df.to_parquet(RAW_DIR / "noaa" / f"GHCNh_{st['id']}_2024.parquet", index=False)

    print(f"synthetic raw data written to {RAW_DIR}")


if __name__ == "__main__":
    main()
