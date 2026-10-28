"""Download hourly station weather from NOAA GHCNh (Global Historical
Climatology Network - hourly), the successor to the old ISD/"Global Hourly".

No API key needed. Files come from NCEI's by-year Parquet folders:
  https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/access/by-year/<YEAR>/parquet/GHCNh_<STATION>_<YEAR>.parquet

Falls back to the pipe-separated (.psv) version if Parquet is unavailable.

    python scripts/fetch_noaa.py

Output: data/raw/noaa/GHCNh_<STATION>_<YEAR>.parquet
"""
from __future__ import annotations

import io

import pandas as pd
import requests

from common import RAW_DIR, ensure_dirs, load_config, log

BASE = "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/access/by-year"


def download(station: str, year: int) -> pd.DataFrame | None:
    for fmt in ("parquet", "psv"):
        url = f"{BASE}/{year}/{fmt}/GHCNh_{station}_{year}.{fmt}"
        resp = requests.get(url, timeout=120)
        if resp.status_code != 200:
            continue
        buf = io.BytesIO(resp.content)
        if fmt == "parquet":
            return pd.read_parquet(buf)
        return pd.read_csv(buf, sep="|", low_memory=False)
    return None


def main() -> None:
    cfg = load_config()
    ensure_dirs()
    y0 = int(cfg["date_range"]["start"][:4])
    y1 = int(cfg["date_range"]["end"][:4])

    stations = {s["id"] for r in cfg["regions"].values() for s in r["stations"]}
    for station in sorted(stations):
        for year in range(y0, y1 + 1):
            out = RAW_DIR / "noaa" / f"GHCNh_{station}_{year}.parquet"
            if out.exists():
                continue
            df = download(station, year)
            if df is None:
                log.warning("no GHCNh file for %s %s — check the station ID", station, year)
                continue
            df.to_parquet(out, index=False)
            log.info("wrote %s (%s rows)", out.name, len(df))


if __name__ == "__main__":
    main()
