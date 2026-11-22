# Folder 09 — Dashboard

**Responsibility of this folder:** show the results to users with filters.
**Real project:** the Streamlit app (`streamlit_app.py` + 15 pages in `pages/`), which also runs inside Snowflake as `F1_RACE_INTELLIGENCE`, and the Power BI report (`powerbi/`, 13 pages, 116 visuals, built by `powerbi/build_pbip.py`).

---

## File: `mini_dashboard.py`

**1. Location:** `exam_simplified/09_dashboard/mini_dashboard.py`
Run: `.venv/bin/streamlit run exam_simplified/09_dashboard/mini_dashboard.py`

**2. What it does:** a one-page version of the race predictor: pick a Grand Prix and who takes pole, and the podium, chart and table update.

**3. Parameters and logic:** it reads `forecast_scenarios.csv`, which holds **44 precomputed scenarios** (2 upcoming races × 22 pole-sitters). This is exactly how the Power BI page works, because Power BI cannot run Python models. The real Streamlit page runs the model live, so it can also change a driver's team, grid slot, form and teammate battle.

**4. Simplified code**
```python
# ============================================================
# FILE: 09_dashboard/mini_dashboard.py
# REAL MODULES: streamlit_app.py + pages/26_D2_Race_Predictor.py (Streamlit)
#               and powerbi/build_pbip.py (the Power BI "Race predictor" page)
# WHAT IT DOES: a tiny dashboard. Pick a race and a pole-sitter and the predicted podium updates.
#   Like Power BI, it reads the precomputed scenarios (every race x every pole-sitter) in forecast_scenarios.csv.
# Run it with:   .venv/bin/streamlit run exam_simplified/09_dashboard/mini_dashboard.py
# ============================================================

import os
import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS = os.path.join(HERE, "..", "..", "06_classification_algorithm", "forecast_scenarios.csv")
data = pd.read_csv(SCENARIOS)

st.title("ApexIQ: who wins the next Grand Prix?")
st.caption("Last race: " + data["last_race"].iat[0])

# Filters (the same two slicers as the Power BI page)
race = st.selectbox("Grand Prix", data["race"].unique())
pole = st.selectbox("Who takes pole?", data["pole_scenario"].unique())

# Keep only the rows of the chosen scenario
chosen = data[(data["race"] == race) & (data["pole_scenario"] == pole)].sort_values("predicted_rank")

# Show the podium: the three most likely winners
first, second, third = st.columns(3)
for column, (_, driver) in zip([first, second, third], chosen.head(3).iterrows()):
    column.metric(f"P{driver['predicted_rank']}: {driver['driver_name']}", f"{driver['win_probability']:.1f}%",
                  driver["constructor_name"])

# The full predicted order with the parameters behind it
st.bar_chart(chosen.head(10).set_index("driver_name")["win_probability"])
st.dataframe(chosen[["predicted_rank", "driver_name", "constructor_name", "grid_position", "win_probability",
                     "driver_rolling_finish_5", "constructor_rolling_points_10", "circuit_experience"]],
             hide_index=True)
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `data = pd.read_csv(SCENARIOS)` | All 44 scenarios × 22 drivers |
| `st.selectbox("Grand Prix", ...)` | Filter 1: the race |
| `st.selectbox("Who takes pole?", ...)` | Filter 2: the pole-sitter |
| `data[(data["race"] == race) & (data["pole_scenario"] == pole)]` | Keep the chosen scenario's 22 rows |
| `column.metric(...)` | The three podium cards |
| `st.bar_chart(...)`, `st.dataframe(...)` | Chance to win, and the parameters behind it |

**6. Say this in the jury:** "The dashboard is where users use the model. In Streamlit, inside Snowflake too, every filter recalculates the forecast live. In Power BI, the slicers pick from 44 precomputed scenarios."

**7. Viva question:** *Why both Streamlit and Power BI?*
**Answer:** Streamlit holds the full analysis and runs the model live, locally and inside Snowflake. Power BI is the business-user view with drag-and-drop filters, the tool most companies use. Both show the same numbers.
