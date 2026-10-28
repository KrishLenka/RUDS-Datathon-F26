# Data dictionary

All timestamps are **UTC** (`ts_utc`) unless the column name says `local`.
Energy is in **MWh per hour** (numerically equal to average MW over that hour).

## `model_table.parquet` / `.csv` (start here)

One row per `(ba, ts_utc)`. Built from the three tables below.

### Keys & calendar
| Column | Type | Description |
|---|---|---|
| `ba` | str | Balancing authority code: `PJM`, `ERCO`, `CISO`, `NYIS`, `ISNE` |
| `ts_utc` | timestamp (UTC) | Hour **ending** (EIA convention) |
| `ts_local` | str | Same hour in the region's local time, `YYYY-MM-DD HH:MM` |
| `hour_local` | int | 0–23, local |
| `dow_local` | int | 0 = Monday … 6 = Sunday |
| `month` | int | 1–12, local |
| `is_weekend` | bool | Saturday/Sunday, local |
| `is_federal_holiday` | bool | U.S. federal holiday, local date |

### Grid (EIA-930)
| Column | Description |
|---|---|
| `demand_mwh` | Actual electricity demand reported by the BA. **Raw** (not cleaned). |
| `forecast_mwh` | The BA's own day-ahead demand forecast. A free baseline to compare against. |
| `net_gen_mwh` | Net generation inside the BA. |
| `interchange_mwh` | Total net interchange (+ = exporting, − = importing). |
| `forecast_error_mwh` | `demand_mwh − forecast_mwh` |
| `demand_mwh_filled` | Demand with spikes/non-positive values removed and gaps of ≤ 3 hours linearly interpolated. Longer gaps stay NaN. |
| `flag_demand_missing` | Hour has no demand report. |
| `flag_demand_nonpositive` | Demand ≤ 0 (physically implausible for these BAs). |
| `flag_demand_spike` | Demand is > 50% away from the centered 24-hour rolling median. |
| `flag_forecast_missing` | Hour has no day-ahead forecast. |

### Weather (NOAA GHCNh, aggregated per BA)
Each BA's value is a **weighted average of 3–4 airport stations** (weights in
`config/regions.yaml`, roughly proportional to metro population), renormalized
over whichever stations reported that hour.

| Column | Unit | Description |
|---|---|---|
| `temp_c` | °C | Air temperature |
| `dewpoint_c` | °C | Dew point (humidity proxy; drives A/C load) |
| `rel_humidity_pct` | % | Relative humidity |
| `wind_speed_ms` | m/s | Wind speed at station (≈10 m); **not** hub-height wind |
| `precip_mm` | mm | Precipitation (max across reports in the hour) |
| `n_stations_reporting` | int | How many stations had a temperature that hour |
| `cooling_degree_hours` | °C·h | `max(temp_c − 18.3, 0)` (18.3 °C = 65 °F) |
| `heating_degree_hours` | °C·h | `max(18.3 − temp_c, 0)` |

### Generation mix (EIA-930, summarized)
| Column | Description |
|---|---|
| `gen_solar_total_mwh` | All solar categories summed (see note below) |
| `gen_wind_total_mwh` | All wind categories summed |
| `gen_hydro_total_mwh` | All hydro categories summed |
| `gen_all_sources_mwh` | Sum of every energy source reported |
| `renewable_share` | (solar + wind) / all sources |

## `generation_fuel.parquet`
One column per EIA energy-source code: `gen_<code>_mwh` (e.g. `gen_ng_mwh` natural gas,
`gen_nuc_mwh` nuclear, `gen_col_mwh` coal, `gen_sun_mwh` solar, `gen_wnd_mwh` wind,
`gen_wat_mwh` hydro, `gen_oth_mwh` other), plus the `*_total_mwh` harmonized columns.

**Category change:** starting in the second half of 2024, EIA split solar, wind, and hydro
into subcategories (e.g. solar with vs. without integrated battery storage, pumped storage,
battery storage). Raw per-code columns therefore appear/disappear mid-dataset. Use the
`*_total_mwh` columns for anything that spans mid-2024.

## `grid_hourly.parquet`, `weather_hourly.parquet`
The grid-only and weather-only halves of `model_table`, same column definitions.
