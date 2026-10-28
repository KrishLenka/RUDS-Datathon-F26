"""Starter tools for an agentic track: plain Python functions over the
processed tables, plus JSON-schema tool definitions any LLM framework can use
(Anthropic, OpenAI, LangChain, LlamaIndex...).

Teams are expected to replace / extend these. They exist so nobody spends the
first two hours of the event writing a groupby.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("DATATHON_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))


@lru_cache(maxsize=1)
def table() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "processed" / "model_table.parquet")


def _window(ba: str, start: str, end: str) -> pd.DataFrame:
    m = table()
    lo = pd.Timestamp(start, tz="UTC")
    hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(hours=23)
    return m[(m["ba"] == ba.upper()) & m["ts_utc"].between(lo, hi)]


# ------------------------------------------------------------------ tools --
def list_regions() -> list[dict]:
    """Balancing authorities available, with their date coverage."""
    m = table()
    g = m.groupby("ba")["ts_utc"].agg(["min", "max"])
    return [{"ba": ba, "start": str(r["min"].date()), "end": str(r["max"].date())} for ba, r in g.iterrows()]


def demand_summary(ba: str, start: str, end: str) -> dict:
    """Peak / mean / min demand and EIA forecast error for a BA and date range."""
    w = _window(ba, start, end).dropna(subset=["demand_mwh"])
    w = w[~(w["flag_demand_spike"] | w["flag_demand_nonpositive"])]
    if w.empty:
        return {"error": "no clean demand data in that window"}
    peak = w.loc[w["demand_mwh"].idxmax()]
    err = (w["forecast_error_mwh"].abs() / w["demand_mwh"]).dropna()
    return {
        "ba": ba.upper(),
        "hours": int(len(w)),
        "mean_mwh": round(w["demand_mwh"].mean()),
        "peak_mwh": round(peak["demand_mwh"]),
        "peak_time_local": peak["ts_local"],
        "temp_at_peak_c": None if pd.isna(peak["temp_c"]) else float(round(peak["temp_c"], 1)),
        "min_mwh": round(w["demand_mwh"].min()),
        "eia_forecast_mape_pct": float(round(err.mean() * 100, 2)) if len(err) else None,
    }


def extreme_hours(ba: str, start: str, end: str, n: int = 10, by: str = "demand_mwh") -> list[dict]:
    """Top-n hours by a column (demand_mwh, forecast_error_mwh, temp_c, renewable_share...)."""
    w = _window(ba, start, end).dropna(subset=[by])
    cols = ["ts_local", "demand_mwh", "forecast_mwh", "temp_c", "dewpoint_c", "renewable_share"]
    top = w.reindex(w[by].abs().sort_values(ascending=False).index).head(n)
    return top[cols].round(2).astype(object).where(top[cols].notna(), None).to_dict("records")


def weather_demand_sensitivity(ba: str, start: str, end: str) -> dict:
    """MWh change per extra cooling / heating degree-hour (simple OLS)."""
    import numpy as np

    w = _window(ba, start, end).dropna(subset=["demand_mwh_filled", "cooling_degree_hours", "heating_degree_hours"])
    if len(w) < 48:
        return {"error": "need at least 48 hours of data"}
    X = np.column_stack([np.ones(len(w)), w["cooling_degree_hours"], w["heating_degree_hours"]])
    coef, *_ = np.linalg.lstsq(X, w["demand_mwh_filled"].to_numpy(), rcond=None)
    return {"ba": ba.upper(), "baseline_mwh": int(round(coef[0])),
            "mwh_per_cooling_degree_hour": float(round(coef[1], 1)),
            "mwh_per_heating_degree_hour": float(round(coef[2], 1))}


def data_quality(ba: str, start: str, end: str) -> dict:
    """Counts of each data-quality flag in the window."""
    w = _window(ba, start, end)
    flags = [c for c in w if c.startswith("flag_")]
    return {"ba": ba.upper(), "hours": int(len(w)), **{f: int(w[f].sum()) for f in flags},
            "weather_coverage_pct": float(round(w["temp_c"].notna().mean() * 100, 1)) if len(w) else None}


TOOLS = {f.__name__: f for f in (list_regions, demand_summary, extreme_hours,
                                 weather_demand_sensitivity, data_quality)}

_RANGE = {
    "ba": {"type": "string", "description": "Balancing authority code, e.g. PJM, ERCO, CISO, NYIS, ISNE"},
    "start": {"type": "string", "description": "Start date YYYY-MM-DD (UTC)"},
    "end": {"type": "string", "description": "End date YYYY-MM-DD (UTC, inclusive)"},
}

# Anthropic-style tool schemas. For OpenAI, wrap each as
# {"type": "function", "function": {"name", "description", "parameters": input_schema}}.
TOOL_SCHEMAS = [
    {"name": "list_regions", "description": list_regions.__doc__,
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "demand_summary", "description": demand_summary.__doc__,
     "input_schema": {"type": "object", "properties": _RANGE, "required": list(_RANGE)}},
    {"name": "extreme_hours", "description": extreme_hours.__doc__,
     "input_schema": {"type": "object", "required": list(_RANGE), "properties": {
         **_RANGE,
         "n": {"type": "integer", "description": "How many hours to return (default 10)"},
         "by": {"type": "string", "description": "Column to rank by (default demand_mwh)"}}}},
    {"name": "weather_demand_sensitivity", "description": weather_demand_sensitivity.__doc__,
     "input_schema": {"type": "object", "properties": _RANGE, "required": list(_RANGE)}},
    {"name": "data_quality", "description": data_quality.__doc__,
     "input_schema": {"type": "object", "properties": _RANGE, "required": list(_RANGE)}},
]


def call_tool(name: str, args: dict):
    return TOOLS[name](**args)
