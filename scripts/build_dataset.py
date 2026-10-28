"""Turn the raw EIA + NOAA downloads into tidy, joinable tables.

    python scripts/build_dataset.py

Writes to data/processed/:
  grid_hourly.parquet     one row per (ba, ts_utc): demand, EIA forecast, net
                          generation, interchange, + data-quality flags
  generation_fuel.parquet one row per (ba, ts_utc): MWh by energy source, with
                          harmonized solar/wind/hydro totals across EIA's
                          2024 category change
  weather_hourly.parquet  one row per (ba, ts_utc): population-weighted weather
                          across the BA's stations, + degree-hours
  model_table.parquet     everything above joined, plus calendar features
  model_table.csv         same, for spreadsheet / beginner use

Cleaning philosophy: we FLAG, we don't silently fix. Original values are kept;
the only filled column is `demand_mwh_filled` (short gaps only). Deciding how
to treat the rest is part of the challenge.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from common import PROCESSED_DIR, RAW_DIR, ensure_dirs, load_config, log

REGION_TYPES = {"D": "demand_mwh", "DF": "forecast_mwh", "NG": "net_gen_mwh", "TI": "interchange_mwh"}
WEATHER_VARS = {
    "temperature": "temp_c",
    "dew_point_temperature": "dewpoint_c",
    "relative_humidity": "rel_humidity_pct",
    "wind_speed": "wind_speed_ms",
    "precipitation": "precip_mm",
}
PLAUSIBLE = {  # crude physical bounds; values outside become NaN
    "temp_c": (-60, 60),
    "dewpoint_c": (-70, 40),
    "rel_humidity_pct": (0, 100),
    "wind_speed_ms": (0, 75),
    "precip_mm": (0, 300),
}
BASE_TEMP_C = 18.3  # 65°F, the standard degree-day base


# ---------------------------------------------------------------- EIA grid --
def _parse_period(s: pd.Series) -> pd.Series:
    # API `hourly` periods look like "2024-07-01T14" and are UTC.
    return pd.to_datetime(s, format="%Y-%m-%dT%H", utc=True)


def build_grid(bas: list[str]) -> pd.DataFrame:
    frames = []
    for ba in bas:
        path = RAW_DIR / "eia" / f"region_data_{ba}.parquet"
        if not path.exists():
            log.warning("missing %s", path.name)
            continue
        df = pd.read_parquet(path)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["ts_utc"] = _parse_period(df["period"])
        wide = (
            df[df["type"].isin(REGION_TYPES)]
            .pivot_table(index="ts_utc", columns="type", values="value", aggfunc="first")
            .rename(columns=REGION_TYPES)
        )
        # Reindex to a complete hourly grid so missing hours are explicit rows.
        full = pd.date_range(wide.index.min(), wide.index.max(), freq="h", tz="UTC")
        wide = wide.reindex(full)
        wide.index.name = "ts_utc"
        wide["ba"] = ba
        frames.append(wide.reset_index())
    grid = pd.concat(frames, ignore_index=True)
    for col in REGION_TYPES.values():
        if col not in grid:
            grid[col] = np.nan
    return add_grid_flags(grid)


def add_grid_flags(grid: pd.DataFrame) -> pd.DataFrame:
    grid = grid.sort_values(["ba", "ts_utc"]).reset_index(drop=True)
    g = grid.groupby("ba")["demand_mwh"]

    grid["flag_demand_missing"] = grid["demand_mwh"].isna()
    grid["flag_demand_nonpositive"] = grid["demand_mwh"] <= 0

    # Spike detector: far from a centered 24h rolling median for that BA.
    med = g.transform(lambda s: s.rolling(25, center=True, min_periods=6).median())
    rel_dev = (grid["demand_mwh"] - med).abs() / med
    grid["flag_demand_spike"] = rel_dev > 0.5

    grid["flag_forecast_missing"] = grid["forecast_mwh"].isna()

    # Fill only short gaps (<= 3 hours) and only over clean values. A longer
    # gap stays entirely NaN (pandas' `limit` alone would half-fill it).
    clean = grid["demand_mwh"].mask(grid["flag_demand_nonpositive"] | grid["flag_demand_spike"])

    def fill_short(s: pd.Series, max_gap: int = 3) -> pd.Series:
        na = s.isna()
        run_id = (na != na.shift()).cumsum()
        run_len = na.groupby(run_id).transform("size")
        filled = s.interpolate(limit_area="inside")
        return filled.where(~na | (run_len <= max_gap))

    grid["demand_mwh_filled"] = clean.groupby(grid["ba"]).transform(fill_short)
    grid["forecast_error_mwh"] = grid["demand_mwh"] - grid["forecast_mwh"]
    return grid


def build_generation(bas: list[str]) -> pd.DataFrame:
    frames = []
    for ba in bas:
        path = RAW_DIR / "eia" / f"fuel_type_{ba}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["ts_utc"] = _parse_period(df["period"])
        df["col"] = "gen_" + df["fueltype"].str.lower() + "_mwh"
        wide = df.pivot_table(index="ts_utc", columns="col", values="value", aggfunc="first")

        # EIA split solar/wind/hydro into subcategories starting mid-2024.
        # Sum anything whose description mentions the resource so the series
        # is continuous across the change.
        names = df.drop_duplicates("col").set_index("col")["type-name"].str.lower()
        for resource in ("solar", "wind", "hydro"):
            cols = [c for c, n in names.items() if resource in n and c in wide]
            wide[f"gen_{resource}_total_mwh"] = wide[cols].sum(axis=1, min_count=1) if cols else np.nan

        wide["ba"] = ba
        frames.append(wide.reset_index())
    if not frames:
        return pd.DataFrame(columns=["ba", "ts_utc"])
    gen = pd.concat(frames, ignore_index=True)
    total_cols = [c for c in gen if c.startswith("gen_") and not c.endswith("_total_mwh")]
    gen["gen_all_sources_mwh"] = gen[total_cols].sum(axis=1, min_count=1)
    ren = gen[["gen_solar_total_mwh", "gen_wind_total_mwh"]].sum(axis=1, min_count=1)
    gen["renewable_share"] = ren / gen["gen_all_sources_mwh"]
    return gen


# ------------------------------------------------------------- NOAA weather --
def _station_frame(station: str) -> pd.DataFrame:
    parts = sorted((RAW_DIR / "noaa").glob(f"GHCNh_{station}_*.parquet"))
    if not parts:
        return pd.DataFrame()
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    df.columns = [c.lower() for c in df.columns]

    if "date" in df:
        ts = pd.to_datetime(df["date"], utc=True, errors="coerce")
    else:
        ts = pd.to_datetime(df[["year", "month", "day", "hour", "minute"]], errors="coerce", utc=True)
    out = pd.DataFrame({"ts_utc": ts.dt.round("h")})
    for src, dst in WEATHER_VARS.items():
        vals = pd.to_numeric(df[src], errors="coerce") if src in df else np.nan
        out[dst] = vals
        lo, hi = PLAUSIBLE[dst]
        out[dst] = out[dst].where(out[dst].between(lo, hi))
    # Several reports can round to the same hour (routine + special obs).
    agg = {c: "mean" for c in WEATHER_VARS.values()}
    agg["precip_mm"] = "max"
    return out.dropna(subset=["ts_utc"]).groupby("ts_utc").agg(agg)


def build_weather(cfg: dict) -> pd.DataFrame:
    frames = []
    for ba, region in cfg["regions"].items():
        stack, weights = [], []
        for st in region["stations"]:
            sdf = _station_frame(st["id"])
            if sdf.empty:
                log.warning("%s: no weather for station %s", ba, st["id"])
                continue
            stack.append(sdf)
            weights.append(st["weight"])
        if not stack:
            continue
        cols = list(WEATHER_VARS.values())
        idx = stack[0].index
        for s in stack[1:]:
            idx = idx.union(s.index)
        num = pd.DataFrame(0.0, index=idx, columns=cols)
        den = pd.DataFrame(0.0, index=idx, columns=cols)
        for sdf, w in zip(stack, weights):
            sdf = sdf.reindex(idx)
            num += sdf.fillna(0) * w
            den += sdf.notna() * w  # renormalize over stations reporting that hour
        wx = num / den.replace(0, np.nan)
        wx["n_stations_reporting"] = sum(s.reindex(idx)["temp_c"].notna().astype(int) for s in stack)
        wx["cooling_degree_hours"] = (wx["temp_c"] - BASE_TEMP_C).clip(lower=0)
        wx["heating_degree_hours"] = (BASE_TEMP_C - wx["temp_c"]).clip(lower=0)
        wx.index.name = "ts_utc"
        wx["ba"] = ba
        frames.append(wx.reset_index())
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["ba", "ts_utc"])


# ---------------------------------------------------------------- joining --
def add_calendar(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    tz = {ba: r["timezone"] for ba, r in cfg["regions"].items()}
    local = [ts.tz_convert(tz[ba]) for ts, ba in zip(df["ts_utc"], df["ba"])]
    df["ts_local"] = [t.strftime("%Y-%m-%d %H:%M") for t in local]
    df["hour_local"] = [t.hour for t in local]
    df["dow_local"] = [t.dayofweek for t in local]
    df["month"] = [t.month for t in local]
    dates = pd.to_datetime([t.date() for t in local])
    hol = USFederalHolidayCalendar().holidays(dates.min(), dates.max())
    df["is_federal_holiday"] = dates.isin(hol)
    df["is_weekend"] = df["dow_local"] >= 5
    return df


def main() -> None:
    cfg = load_config()
    ensure_dirs()
    bas = list(cfg["regions"])

    grid = build_grid(bas)
    gen = build_generation(bas)
    wx = build_weather(cfg)

    grid.to_parquet(PROCESSED_DIR / "grid_hourly.parquet", index=False)
    gen.to_parquet(PROCESSED_DIR / "generation_fuel.parquet", index=False)
    wx.to_parquet(PROCESSED_DIR / "weather_hourly.parquet", index=False)

    model = grid.merge(wx, on=["ba", "ts_utc"], how="left")
    gen_keep = ["ba", "ts_utc", "gen_solar_total_mwh", "gen_wind_total_mwh",
                "gen_hydro_total_mwh", "gen_all_sources_mwh", "renewable_share"]
    model = model.merge(gen[[c for c in gen_keep if c in gen]], on=["ba", "ts_utc"], how="left")
    model = add_calendar(model, cfg)
    model.to_parquet(PROCESSED_DIR / "model_table.parquet", index=False)
    model.to_csv(PROCESSED_DIR / "model_table.csv", index=False)

    log.info("grid %s rows | generation %s | weather %s | model_table %s",
             len(grid), len(gen), len(wx), len(model))


if __name__ == "__main__":
    main()
