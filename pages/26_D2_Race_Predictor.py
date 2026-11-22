import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import xgboost as xgb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "06_classification_algorithm"))
from db_utils import apply_f1_theme, get_plotly_theme, page_header, PURPLE, GREEN
from feature_engineering import ENGINEERED_FEATURE_COLS as FEATURES
from improved_classifier import softmax_race_probabilities

apply_f1_theme()

page_header('Dashboard 2', 'Supervised learning', 'Race predictor',
            "Pick a Grand Prix the model never saw (2022–2024), change the pre-race inputs, and see who it expects to win.")


@st.cache_resource
def champion():
    """Same data, split and settings as the champion in 06_classification_algorithm/improved_classifier.py."""
    df = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
    train = df[df["season"] < 2022]
    model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15, subsample=0.85,
                              colsample_bytree=0.85, random_state=42, eval_metric="logloss")
    model.fit(train[FEATURES].fillna(0), train["target_is_win"].astype(int))
    return model, df[df["season"] >= 2022].copy()


def predict(model, rows):
    """Per-driver win probability, normalised with the champion's race softmax so the race sums to 100%."""
    raw = model.predict_proba(rows[FEATURES].fillna(0))[:, 1]
    return softmax_race_probabilities(raw, [0] * len(rows)) * 100


model, holdout = champion()
races = holdout.drop_duplicates("race_id").sort_values(["season", "round"])

a, b = st.columns([1, 3])
season = a.selectbox("Season", sorted(races["season"].unique(), reverse=True))
in_season = races[races["season"] == season]
rid = b.selectbox("Grand Prix", in_season["race_id"], format_func=lambda r: in_season.loc[in_season["race_id"] == r, "race_name"].iat[0])
race = holdout[holdout["race_id"] == rid].sort_values("grid_position").reset_index(drop=True)
race_name = f"{season} {race['race_name'].iat[0]}"

EDIT = {"grid_position": "Grid slot", "driver_rolling_finish_5": "Avg finish, last 5 races",
        "driver_rolling_points_5": "Avg points, last 5 races", "constructor_rolling_points_10": "Team avg points, last 10",
        "ahead_of_teammate_grid": "Out-qualified teammate"}
st.markdown(f"#### What-if inputs for the {race_name}")
st.caption("These are the real pre-race values. Edit any cell (for example give a driver pole position) and the prediction "
           "below updates. The other 11 features stay as they were before the race.")
key = f"edit_{rid}_{st.session_state.get('reset', 0)}"
shown = race[["driver_name", "constructor_name"] + list(EDIT)].rename(columns={"driver_name": "Driver", "constructor_name": "Team", **EDIT})
shown["Out-qualified teammate"] = shown["Out-qualified teammate"].astype(bool)
edited = st.data_editor(
    shown, key=key, hide_index=True, width="stretch", disabled=["Driver", "Team"],
    column_config={"Grid slot": st.column_config.NumberColumn(min_value=1, max_value=26, step=1),
                   "Avg finish, last 5 races": st.column_config.NumberColumn(min_value=1.0, max_value=26.0, step=0.1, format="%.1f"),
                   "Avg points, last 5 races": st.column_config.NumberColumn(min_value=0.0, max_value=26.0, step=0.1, format="%.1f"),
                   "Team avg points, last 10": st.column_config.NumberColumn(min_value=0.0, max_value=44.0, step=0.1, format="%.1f")})
if st.button("Reset to the real pre-race values"):
    st.session_state["reset"] = st.session_state.get("reset", 0) + 1
    st.rerun()

scenario = race.copy()
for f, label in EDIT.items():
    scenario[f] = edited[label].astype(float).values
scenario["grid_vs_form_gap"] = scenario["grid_position"] - scenario["driver_rolling_finish_5"]  # derived feature follows the edits

base = predict(model, race)
new = predict(model, scenario)
out = pd.DataFrame({"Driver": race["driver_name"], "Team": race["constructor_name"], "Grid": scenario["grid_position"].astype(int),
                    "Win probability %": new.round(1), "Change vs real inputs": (new - base).round(1),
                    "Actual finish": race["target_finish_position"].astype(int)}).sort_values("Win probability %", ascending=False)
changed = not np.allclose(new, base)

fav, actual = out.iloc[0], race.loc[race["target_is_win"] == 1, "driver_name"].iat[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Predicted winner", fav["Driver"], f"{fav['Win probability %']:.1f}% chance", delta_color="off")
c2.metric("Actual winner", actual, f"started P{int(race.loc[race['target_is_win'] == 1, 'grid_position'].iat[0])}", delta_color="off")
c3.metric("Model's pick (real inputs)", race["driver_name"].iat[int(np.argmax(base))],
          "correct" if race["driver_name"].iat[int(np.argmax(base))] == actual else "missed", delta_color="off")
c4.metric("Inputs", "Edited" if changed else "Real", "what-if scenario" if changed else "as before the race", delta_color="off")

top = out.head(10).iloc[::-1]
fig = px.bar(top, x="Win probability %", y="Driver", orientation="h", text="Win probability %",
             color=np.where(top["Driver"] == actual, "Actual winner", "Other"),
             color_discrete_map={"Actual winner": GREEN, "Other": PURPLE},
             title=f"{race_name}: predicted win probability, top 10" + (" (what-if)" if changed else ""))
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False).update_layout(yaxis_title=None, legend_title_text="")
st.plotly_chart(get_plotly_theme(fig), width="stretch")
st.dataframe(out, width="stretch", hide_index=True)

with st.expander("How the prediction is made"):
    st.markdown(f"""
    1. The champion **cost-sensitive XGBoost** (100 trees, depth 4, `scale_pos_weight = 15`) is trained on 1994–2021 only,
       so every 2022–2024 race here is genuinely unseen.
    2. It scores each driver from **{len(FEATURES)} pre-race features**: grid slot, recent driver and team form, circuit record,
       career numbers and the teammate qualifying battle.
    3. A **race softmax** (temperature 0.8) turns the scores into probabilities that add up to 100% for the race.
    4. The predicted winner is the driver with the highest probability. Over the 68 races it picks the real winner in 40.
    """)
