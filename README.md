# ⚡ Grid × Weather Datathon

Hourly U.S. electricity demand, forecasts, and generation by fuel source from the
**EIA Hourly Electric Grid Monitor (Form EIA-930)**, joined with hourly station
weather from **NOAA GHCNh**, for five major grid regions.

| Region code | Grid operator | Covers |
|---|---|---|
| `PJM`  | PJM Interconnection | Mid-Atlantic (incl. NJ, PA, MD, DC) + parts of the Midwest |
| `ERCO` | ERCOT | Most of Texas |
| `CISO` | California ISO | Most of California |
| `NYIS` | New York ISO | New York State |
| `ISNE` | ISO New England | New England |

**Coverage:** 2023-01-01 → 2025-12-31, hourly, UTC. ~130k rows in the joined table.

---

## Quick start (participants)

```bash
git clone <this repo>
cd grid-weather-datathon
pip install -r requirements.txt
python starter/quickstart.py          # load + explore in 5 minutes
```

The file you most likely want is **`data/processed/model_table.parquet`** (or `.csv`).
One row = one region × one hour, with grid numbers, weather, generation mix, and
calendar features already joined. See [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

Before modeling anything, read [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md).
The data is real and it is messy, on purpose.

## Challenge tracks

See [`docs/CHALLENGE_TRACKS.md`](docs/CHALLENGE_TRACKS.md). Short version:

1. **Grid Analyst Agent:** an LLM agent that answers questions about the grid using tools over this data
2. **Extreme-Weather Stress Explorer:** what weather drives the worst demand, and an app that shows it
3. **Renewable Generation Copilot:** explain and forecast solar/wind output from weather
4. **Data Detective:** find, classify, and fix the data-quality problems, and build tooling that does it automatically

Starter code for the agent track: [`starter/agent_tools.py`](starter/agent_tools.py) (5 ready-made tools + JSON schemas)
and [`starter/agent_example.py`](starter/agent_example.py) (a ~40-line tool-use loop).

## Repository layout

```
config/regions.yaml       regions, weather stations + weights, date range
scripts/fetch_eia.py      download EIA-930 via the EIA API (needs free key)
scripts/fetch_noaa.py     download NOAA GHCNh station files (no key)
scripts/build_dataset.py  clean, flag, aggregate weather, join → data/processed/
scripts/validate.py       data-quality report + EIA forecast baseline
starter/                  quickstart + agent tools + agent example
tests/make_sample_data.py synthetic offline data for testing the pipeline
docs/                     data dictionary, data quality, tracks, organizer notes, sources
```

## Rebuilding the data (organizers)

```bash
export EIA_API_KEY=...            # free: https://www.eia.gov/opendata/register.php
make data                         # fetch_eia → fetch_noaa → build → validate
```

Change regions, stations, or dates in `config/regions.yaml` and re-run.
To test without network access: `make sample` (synthetic data, never analyze it).

## Sources & attribution

- U.S. Energy Information Administration, *Hourly Electric Grid Monitor* / Form EIA-930.
  https://www.eia.gov/electricity/gridmonitor/
- NOAA National Centers for Environmental Information, *Global Historical Climatology
  Network – hourly (GHCNh)*. https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly

Both are U.S. government open data. NOAA asks for attribution, and asks that modified data
not be presented as original NOAA data; the processed tables here are derived and modified.
Details in [`docs/SOURCES.md`](docs/SOURCES.md). Code is MIT-licensed.
