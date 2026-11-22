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
t0, t1, t2, t3, t4 = st.tabs(["Dataset Overview", "Class Labels", "16 Features", "Chronological Split", "Sample Rows"])

FEATURES = {  # input feature: (group, what it measures), all known before the race starts
    "grid_position": ("Grid", "Starting grid slot (1 = pole)"),
    "ahead_of_teammate_grid": ("Grid", "1 if the driver out-qualified their teammate"),
    "grid_vs_form_gap": ("Grid", "Grid slot minus recent average finish"),
    "driver_rolling_finish_5": ("Driver form", "Average finish over the previous 5 races"),
    "driver_rolling_points_5": ("Driver form", "Average points over the previous 5 races"),
    "season_points_before": ("Driver form", "Championship points before this round"),
    "constructor_rolling_finish_10": ("Team form", "Team's average finish over its previous 10 entries"),
    "constructor_rolling_points_10": ("Team form", "Team's average points over its previous 10 entries"),
    "circuit_avg_finish": ("Circuit history", "Driver's average finish at this circuit"),
    "circuit_win_rate": ("Circuit history", "Driver's win rate at this circuit"),
    "circuit_podium_rate": ("Circuit history", "Driver's podium rate at this circuit"),
    "circuit_experience": ("Circuit history", "Previous starts at this circuit"),
    "career_starts": ("Career", "Grands Prix started before this race"),
    "career_win_rate": ("Career", "Career win rate before this race"),
    "career_dnf_rate": ("Career", "Career retirement rate before this race"),
    "driver_age": ("Career", "Age in years on race day"),
}
assert set(FEATURES) == set(ENGINEERED_FEATURE_COLS), "every model feature needs a description"
LABEL_COLS = [c for c in df.columns if c.startswith("target_")]
ID_COLS = [c for c in df.columns if c not in FEATURES and c not in LABEL_COLS]

with t0:
    st.markdown(f"""
    #### F1 Race Lab feature store, 1994–2024
    **File:** `data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv` · **Source:** Ergast Formula 1 historical results
    (races, drivers, constructors, circuits, results, qualifying, standings), cleaned and joined by the module pipeline.

    **Application:** predict, *before the lights go out*, which driver will win a Grand Prix. The classifier gives each driver
    a win probability and the probabilities in one race add up to 1, so teams, broadcasters and fans get a ranked
    favourite list. Because every feature is known before the race, the model can be used on a real upcoming race.
    """)
    a, b, _ = st.columns([1, 1, 2])  # records and feature counts are already in the header row
    a.metric("Attributes", len(df.columns), f"{len(df):,} records × {len(df.columns)} columns", delta_color="off")
    b.metric("Target", "Winner", "target_is_win: 1 / 0", delta_color="off")
    st.dataframe(pd.DataFrame([("Input features (X)", len(FEATURES), "Grid, driver form, team form, circuit history, career: listed below"),
                               ("Target / class labels (y)", len(LABEL_COLS), ", ".join(LABEL_COLS) + " — primary: target_is_win"),
                               ("Identifiers (not used for learning)", len(ID_COLS), ", ".join(ID_COLS))],
                              columns=["Attribute role", "Count", "Columns"]), width="stretch")
    st.markdown("#### Input features")
    st.dataframe(pd.DataFrame([(f, g, d) for f, (g, d) in FEATURES.items()], columns=["Feature", "Group", "What it measures"]),
                 width="stretch")
    st.caption("Identifiers such as driver and team names are kept only to display results; the model never sees them, "
               "so it cannot simply memorise who is famous.")

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
