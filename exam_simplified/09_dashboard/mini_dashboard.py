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
