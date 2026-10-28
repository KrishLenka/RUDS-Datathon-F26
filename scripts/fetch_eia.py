"""Download hourly EIA-930 grid data via the EIA Open Data API (v2).

Pulls two datasets for every BA in config/regions.yaml:
  * electricity/rto/region-data     -> demand (D), day-ahead demand forecast (DF),
                                       net generation (NG), total interchange (TI)
  * electricity/rto/fuel-type-data  -> net generation by energy source

Requires a free API key: https://www.eia.gov/opendata/register.php
    export EIA_API_KEY=your_key_here
    python scripts/fetch_eia.py

Output: data/raw/eia/region_data_<BA>.parquet, data/raw/eia/fuel_type_<BA>.parquet
Timestamps are UTC (the API's `hourly` frequency). Do not use `local-hourly`
for modeling: local time has a missing hour and a duplicated hour every year
because of daylight saving time.
"""
from __future__ import annotations

import argparse
import os
import time

import pandas as pd
import requests

from common import RAW_DIR, ensure_dirs, load_config, log

API_ROOT = "https://api.eia.gov/v2"
PAGE_SIZE = 5000  # API maximum rows per request
DATASETS = {
    "region_data": "electricity/rto/region-data",
    "fuel_type": "electricity/rto/fuel-type-data",
}


def fetch_dataset(route: str, ba: str, start: str, end: str, api_key: str) -> pd.DataFrame:
    url = f"{API_ROOT}/{route}/data/"
    rows: list[dict] = []
    offset = 0
    while True:
        params = {
            "api_key": api_key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": ba,
            "start": f"{start}T00",
            "end": f"{end}T23",
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": PAGE_SIZE,
        }
        for attempt in range(5):
            resp = requests.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                break
            wait = 2 ** attempt
            log.warning("%s %s HTTP %s, retrying in %ss", route, ba, resp.status_code, wait)
            time.sleep(wait)
        else:
            resp.raise_for_status()

        payload = resp.json()["response"]
        batch = payload.get("data", [])
        rows.extend(batch)
        total = int(payload.get("total", 0))
        offset += len(batch)
        log.info("%s %s: %s / %s rows", route.split("/")[-1], ba, offset, total)
        if not batch or offset >= total:
            break
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bas", nargs="*", help="Subset of BA codes (default: all in config)")
    args = parser.parse_args()

    api_key = os.environ.get("EIA_API_KEY")
    if not api_key:
        raise SystemExit("Set EIA_API_KEY first (free key: https://www.eia.gov/opendata/register.php)")

    cfg = load_config()
    ensure_dirs()
    start, end = cfg["date_range"]["start"], cfg["date_range"]["end"]
    bas = args.bas or list(cfg["regions"])

    for ba in bas:
        for name, route in DATASETS.items():
            out = RAW_DIR / "eia" / f"{name}_{ba}.parquet"
            if out.exists():
                log.info("skip %s (exists)", out.name)
                continue
            df = fetch_dataset(route, ba, start, end, api_key)
            df.to_parquet(out, index=False)
            log.info("wrote %s (%s rows)", out.name, len(df))


if __name__ == "__main__":
    main()
