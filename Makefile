.PHONY: data fetch build validate sample

data: fetch build validate

fetch:
	python scripts/fetch_eia.py
	python scripts/fetch_noaa.py

build:
	python scripts/build_dataset.py

validate:
	python scripts/validate.py

# Offline smoke test with SYNTHETIC data (written outside data/)
sample:
	DATATHON_DATA_DIR=.sample python tests/make_sample_data.py
	DATATHON_DATA_DIR=.sample python scripts/build_dataset.py
	DATATHON_DATA_DIR=.sample python scripts/validate.py
