import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "06_classification_algorithm"))
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header
from feature_engineering import ENGINEERED_FEATURE_COLS

apply_f1_theme()

page_header('Dashboard 2', 'Supervised learning', 'Supervised dataset',
            '12,358 labelled driver-race entries from 577 Grands Prix, 1994–2024.')


@st.cache_data
def load():
    return pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)


df = load()
wins = int(df["target_is_win"].sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Labelled Entries", f"{len(df):,}")
c2.metric("Grands Prix", df["race_id"].nunique(), f"{df['season'].min()}–{df['season'].max()}")
c3.metric("Pre-Race Features", len(ENGINEERED_FEATURE_COLS), "No in-race leakage")
c4.metric("Class Imbalance", f"{(len(df) - wins) / wins:.2f} : 1", f"{wins} winners", delta_color="off")

st.markdown("---")
t1, t2, t3, t4 = st.tabs(["Class Labels", "16 Features", "Chronological Split", "Sample Rows"])

with t1:
    labels = pd.DataFrame([
        ("target_is_win", "finish_position == 1", "Primary classification target"),
        ("target_is_podium", "finish_position ≤ 3", "Secondary"),
        ("target_is_points", "finish_position ≤ 10", "Secondary"),
        ("target_is_dnf", "status ∉ classified finishes", "Secondary"),
        ("target_finish_position", "classified position, clipped 1–20", "Regression target"),
    ], columns=["label", "rule", "role"])
    labels["positives"] = [int(df[c].sum()) if c != "target_finish_position" else None for c in labels["label"]]
    labels["missing"] = [int(df[c].isna().sum()) for c in labels["label"]]
    st.dataframe(labels, width="stretch", hide_index=True)
    a, b = st.columns(2)
    dist = df["target_is_win"].map({1: "Winner (1)", 0: "Non-winner (0)"}).value_counts().reset_index()
    a.plotly_chart(get_plotly_theme(px.pie(dist, names="target_is_win", values="count", hole=0.55,
                                           color_discrete_sequence=["#C3C8CF", F1_RED], title="target_is_win distribution")), width="stretch")
    per_race = df.groupby("race_id")["target_is_win"].sum().value_counts().rename_axis("winners per race").reset_index()
    b.dataframe(per_race, hide_index=True)
    b.success("Every Grand Prix has exactly 1 winner: labels are mutually exclusive within a race.")
    b.info("**Imbalance handling:** cost-sensitive XGBoost (`scale_pos_weight = 15`), evaluated with PR-AUC, recall and race-level top-1 hit rate, not raw accuracy.")

with t2:
    feat = st.selectbox("Feature", ENGINEERED_FEATURE_COLS)
    st.plotly_chart(get_plotly_theme(px.box(df, x="target_is_win", y=feat, color="target_is_win", points=False,
                                            color_discrete_sequence=["#9AA1AB", F1_RED], title=f"{feat}: winners vs. non-winners")),
                    width="stretch")
    st.dataframe(df[ENGINEERED_FEATURE_COLS].describe().T.round(3), width="stretch")
    st.caption("Every feature is computed from races strictly before the current one (`shift(1)` on rolling windows). Pit strategy, safety cars and fastest laps are excluded.")

with t3:
    split = df.assign(partition=pd.cut(df["season"], [1993, 2021, 2022, 2024], labels=["Train 1994–2021", "Validation 2022", "Test 2023–2024"]))
    st.plotly_chart(get_plotly_theme(px.histogram(split, x="season", color="partition", nbins=31,
                                                  color_discrete_sequence=["#9AA1AB", "#C99700", F1_RED],
                                                  title="Entries per season by partition (no random shuffling)")), width="stretch")
    st.markdown("**Temporal invariant:** max(train season) = 2021 < min(test season) = 2022. The model is always tested on the future.")

with t4:
    st.dataframe(df.sample(200, random_state=1), width="stretch", height=380)
