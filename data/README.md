# data/

- `raw/`: downloads from EIA and NOAA (git-ignored; regenerate with `make fetch`)
- `processed/`: cleaned + joined tables participants use (committed to the repo)

`processed/` is empty until an organizer runs `make data` with an EIA API key.
See `../docs/DATA_DICTIONARY.md` for column definitions.
