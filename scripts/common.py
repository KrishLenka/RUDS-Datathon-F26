"""Shared helpers for the fetch/build scripts."""
from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "regions.yaml"
# DATATHON_DATA_DIR lets you point the pipeline somewhere else (e.g. the
# synthetic sample data used by the smoke test) without touching data/.
DATA_DIR = Path(os.environ.get("DATATHON_DATA_DIR", REPO_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("datathon")


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    for d in (RAW_DIR / "eia", RAW_DIR / "noaa", PROCESSED_DIR):
        d.mkdir(parents=True, exist_ok=True)
