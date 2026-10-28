"""Five-minute orientation: load the joined table and look around.

    python starter/quickstart.py
"""
import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("DATATHON_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
m = pd.read_parquet(DATA_DIR / "processed" / "model_table.parquet")

print(m.shape)
print(m.groupby("ba")[["demand_mwh", "temp_c", "renewable_share"]].mean().round(2))

# Demand vs temperature: the classic U-shape (heating on the left, cooling on the right).
m["temp_bin"] = m["temp_c"].round(-1)
print(m.pivot_table(index="temp_bin", columns="ba", values="demand_mwh", aggfunc="mean").round(0))

# Average daily load shape by local hour.
print(m.pivot_table(index="hour_local", columns="ba", values="demand_mwh", aggfunc="mean").round(0))
