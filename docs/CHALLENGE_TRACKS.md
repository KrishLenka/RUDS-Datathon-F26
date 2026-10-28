# Challenge tracks

Every project must use the provided grid + weather data as its core. Teams may bring in other
public data (census population, EIA plant locations, holidays, etc.) if they document it.

These tracks favor **building something people can use**: an agent, an app, a tool.
There is no leaderboard. Judges score on usefulness, rigor, and how honestly you deal with data quality.

---

## Track 1: Grid Analyst Agent 🤖
Build an LLM agent that answers natural-language questions about the grid by calling tools over the data.

> "What drove PJM's highest-demand hour in 2024?"
> "How much more power does ERCOT use per degree above 30 °C?"
> "When was California's EIA forecast most wrong, and what was the weather doing?"

- Start from `starter/agent_tools.py` (5 tools) and `starter/agent_example.py` (tool-use loop)
- Strong projects add tools (SQL over the parquet, charting, anomaly detection, a forecasting model)
- Stretch: RAG over the EIA-930 documentation so the agent can explain data caveats itself
- **Judging:** answer accuracy on a hidden question set, tool design, and whether the agent admits when the data can't answer

## Track 2: Extreme-Weather Stress Explorer 🌡️
Which weather conditions produce the most extreme demand, and how close does each grid come to its limits?

- Heat waves vs. cold snaps; the role of humidity (dew point) vs. temperature alone
- Does the official forecast miss more during extremes?
- **Deliverable:** an interactive app (Streamlit, web, notebook dashboard) that lets a non-expert explore it
- Stretch: an "early warning" view that flags upcoming risky conditions from a weather input

## Track 3: Renewable Generation Copilot ☀️💨
Explain and forecast solar and wind output from weather.

- Solar: cloud cover / precipitation / time of day / season
- Wind: why does airport wind correlate so poorly with wind-farm output? (see DATA_QUALITY.md)
- Watch out for the mid-2024 fuel-category change
- **Deliverable:** a model plus a tool or agent that explains a given day's renewable output in plain English

## Track 4: Data Detective 🔍
The data has holes, spikes, impossible totals, and time-zone traps. Find them, classify them, fix them,
and build something that does it automatically next time.

- Compare your cleaned demand against `demand_mwh_filled`: what does our simple rule get wrong?
- Use NOAA quality codes; detect stuck sensors; check generation vs. demand vs. interchange balance
- **Deliverable:** a reusable cleaning library or an AI "data QA agent" that inspects new data and writes a report
- Stretch: quantify how much your cleaning changes a downstream answer (e.g. peak demand or temperature sensitivity)

---

## Submission checklist
- [ ] Public repo with a README explaining what you built and how to run it
- [ ] A 3-minute demo (live or video)
- [ ] A short "data decisions" section: what you cleaned, dropped, or assumed, and why
- [ ] For agent projects: 5 example questions and the agent's actual answers (including one it gets wrong)
