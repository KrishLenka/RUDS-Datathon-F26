# Organizer notes: is this a good datathon dataset?

**Verdict: yes, a strong fit**, especially for a cleaning + AI-integrated-project format.
It's weaker for a pure Kaggle-style leaderboard, which the tracks deliberately avoid.

## Why it works

| Criterion | Assessment |
|---|---|
| **Intuitive** | Everyone understands "hot day → A/C → more power." No domain lecture needed to start. |
| **Real messiness** | Missing hours, spikes, fuel-category changes, DST, station-to-region mismatch. Genuine cleaning work, not artificial noise. |
| **Join problem** | Grid data is by region, weather is by station. Forces a real design decision (how to aggregate). |
| **Right size** | ~130k rows joined (~10–40 MB). Runs on a laptop; no Spark, no GPUs. |
| **Built-in baseline** | EIA's day-ahead forecast is in the data, so teams can measure themselves against professionals. |
| **Open + free** | U.S. government data. No licensing issues; anyone can extend it. |
| **Many project shapes** | Forecasting, anomaly detection, causal-ish analysis, dashboards, agents, RAG over docs. |
| **Topical** | Data-center load growth, heat waves, and the renewable transition make it easy to motivate. |
| **Local hook** | PJM covers New Jersey. Participants can ask questions about their own grid. |

## Why it's good for an *agentic* competition specifically

- Tabular, numeric data is where LLMs fail without tools, so teams **have** to build real tool use
  rather than stuffing a CSV into a prompt.
- Natural tool boundaries: query, aggregate, compare-to-forecast, fit a sensitivity, detect anomalies, plot.
- Has documentation worth RAG-ing (EIA-930 known issues, GHCNh docs), so agents can explain caveats.
- Verifiable answers: "peak hour in PJM, July 2024" has one correct answer, so judges can build a
  hidden question set and score agents objectively without a prediction leaderboard.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Teams default to "train XGBoost, report RMSE" | Tracks emphasize apps/agents; judging rubric rewards usefulness + data decisions, not RMSE |
| API-key friction / NOAA downtime during the event | **Pre-download.** Ship `data/processed/` in the repo; fetch scripts are for organizers |
| Weather ≠ region (airport stations) | Documented; improving it is itself a valid project |
| LLM API costs for agent track | Tools work with any provider, including local/open models; consider sponsor credits |
| Beginners overwhelmed | `model_table.csv` opens in Excel; `quickstart.py` runs in seconds |
| Hard to beat EIA's forecast | Frame it as "explain the misses," not "beat it" |

## Before the event

1. Get an EIA API key, run `make data`, check `validate.py` output, paste it into DATA_QUALITY.md.
2. Spot-check 2–3 station IDs actually downloaded (the fetch log warns on misses).
3. Commit `data/processed/` (well under GitHub's 100 MB/file limit), or attach it to a GitHub Release.
4. Write the hidden agent question set (15–25 questions with computed answers) from the real data.
5. Optional: hold back the last month of data as a surprise "live" test for forecasting tracks.

## Extensions if you want more

- More BAs (MISO, SWPP, ERCO sub-regions via `region-sub-ba-data`)
- Interchange between regions (`interchange-data`) for a network/graph angle
- EIA-860 plant locations, to place solar/wind farms near weather stations
- Hourly CO₂ emissions (EIA publishes these on the Grid Monitor)
