# Data sources

## EIA: Hourly Electric Grid Monitor (Form EIA-930)
- Dashboard & bulk downloads: https://www.eia.gov/electricity/gridmonitor/
- About the data / data elements / known issues: https://www.eia.gov/electricity/930-content/about.html
- API (free key): https://www.eia.gov/opendata/ → routes used:
  - `electricity/rto/region-data`: demand (`D`), day-ahead forecast (`DF`), net generation (`NG`), total interchange (`TI`)
  - `electricity/rto/fuel-type-data`: net generation by energy source
  - also available: `region-sub-ba-data` (sub-regional demand), `interchange-data` (BA-to-BA flows), and daily versions
- Bulk alternative: six-month CSV files for all BAs, linked from the Grid Monitor's *Download Data* page
- Coverage: hourly from mid-2015; sub-regional demand and generation by fuel from July 2018
- Cleaned research version: Catalyst Cooperative's PUDL project publishes EIA-930 with imputed demand,
  and documents the known issues well: https://docs.catalyst.coop/pudl/en/stable/data_sources/eia930.html

## NOAA: Global Historical Climatology Network hourly (GHCNh)
- Product page: https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly
- Documentation: https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf
- Station map (find station IDs): https://www.ncei.noaa.gov/maps/hourly/
- Files used: `…/hourly/access/by-year/<YEAR>/parquet/GHCNh_<STATION>_<YEAR>.parquet` (psv also available)
- Also on AWS Open Data, no account needed: `s3://noaa-ghcnh-pds/`
- GHCNh replaced the older Integrated Surface Dataset (ISD / "Global Hourly") in 2023.

## Attribution
- U.S. Energy Information Administration, Form EIA-930, Hourly Electric Grid Monitor.
- NOAA National Centers for Environmental Information, Global Historical Climatology Network – hourly (GHCNh), Version 1.

NOAA places no restrictions on use, requests attribution, and asks that modified data not be
represented as original NOAA data. The processed tables in this repo are derived and modified.
