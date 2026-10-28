# Data quality: read this before you model anything

This is real operational data reported by grid operators and weather stations. Expect problems.
The pipeline **flags** them but mostly does **not** fix them. How you handle them is part of
the challenge, and judges will ask.

> Organizers: after `make data`, paste the output of `python scripts/validate.py` at the bottom
> of this file so participants see the actual counts.

## Grid data (EIA-930)

**Missing hours.** BAs occasionally fail to report. The pipeline reindexes to a complete hourly
grid, so missing hours show up as rows with NaN and `flag_demand_missing = True`.

**Zeros, negatives, spikes.** Reporting glitches produce physically impossible values.
See `flag_demand_nonpositive` and `flag_demand_spike`. The spike rule (> 50% from the 24-hour rolling
median) is deliberately simple. Can you do better?

**Totals don't always add up.** Generation by fuel doesn't always sum to `net_gen_mwh`, and
`net_gen − interchange` doesn't always equal `demand`. EIA documents this. Pseudo-ties and
dynamic scheduling (commercial arrangements) can make reported numbers differ from physical flows.

**"Other" hides some generation.** Some generators are lumped into Other to protect confidentiality.

**Fuel categories changed in mid-2024.** Solar, wind, and hydro were split into subcategories. Use
the `*_total_mwh` columns for continuity.

**Hourly totals run low.** EIA notes that aggregating EIA-930 generation to monthly/annual gives
lower numbers than its other publications (EIA-923), largely because small generators aren't
all captured hourly.

**Time zones and DST.** All data is stored in UTC. Local time has a missing hour every March and a
duplicated hour every November. That's why we never key on local time. `ts_utc` is the
**end** of the hour.

## Weather data (NOAA GHCNh)

**Stations ≠ regions.** A BA covers millions of people across several states; we approximate it
with 3–4 airport stations. Coastal vs. inland (Los Angeles vs. Sacramento) can differ by 15 °C on
the same afternoon. Improving the weighting is a legitimate project.

**Irregular observation times.** Stations report around :51 past the hour, plus extra "special"
reports during storms. We round to the nearest hour and average.

**Bad values.** Sentinel values and sensor errors exist. We null anything outside crude physical
bounds (e.g. temperature outside −60…60 °C) and ignore NOAA's per-value quality codes. Using those
codes properly is a good cleaning exercise.

**Surface wind is not turbine wind.** Station wind is measured around 10 m above ground. Turbines
sit at 80–120 m, and output scales roughly with wind speed cubed. Expect weak correlations if you
naively regress wind generation on airport wind.

**Precipitation is sparse and spiky.** Most hours are zero.

## Known-good baseline

`forecast_mwh` is each grid operator's own day-ahead forecast, built by professionals with far
better weather inputs than ours. Beating it with airport weather is hard. That's useful context,
not a reason to skip forecasting. Explaining *where and why* the official forecast misses is often
more interesting than beating it on average.

---

## Validation report

_(paste `python scripts/validate.py` output here)_
