import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "09_unsupervised_dataset"))
from db_utils import apply_f1_theme, get_plotly_theme
from build_unsupervised_dataset import CLUSTER_FEATURE_COLS, MIN_STARTS

apply_f1_theme()

st.title("🗂️ Dashboard 3 · Unsupervised Dataset: Driver-Season Performance Profiles")
st.markdown("### 1 row per driver per season (1994–2024) — no class label, built for clustering")

prof = pd.read_csv(os.path.join(ROOT, "09_unsupervised_dataset", "driver_season_profiles.csv"))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Driver-Season Profiles", f"{len(prof):,}")
c2.metric("Unique Drivers", prof["driver_id"].nunique())
c3.metric("Seasons", f"{prof['season'].min()}–{prof['season'].max()}")
c4.metric("Clustering Features", len(CLUSTER_FEATURE_COLS), "No target column")

st.markdown("---")
t1, t2, t3 = st.tabs(["📋 Data Dictionary & Sample", "📈 Feature Distributions", "🔗 Feature Correlation"])

with t1:
    st.markdown(f"""
    **Source:** `data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv` (12,358 race entries) aggregated by `(driver_id, season)`.
    **Filter:** drivers with at least **{MIN_STARTS} starts** in a season (removes one-off substitutes).
    **Preprocessing:** z-score standardisation (`StandardScaler`) so that no feature dominates the Euclidean distance.

    | Feature | Meaning |
    |---|---|
    | `avg_grid` | Mean starting grid slot — qualifying pace |
    | `avg_finish` | Mean finish position — race pace |
    | `finish_std` | Std-dev of finish position — consistency |
    | `win_rate` / `podium_rate` / `points_rate` | Share of starts ending in a win / podium / points (P1–P10) |
    | `dnf_rate` | Share of starts ending in retirement — reliability & incidents |
    | `teammate_quali_rate` | Share of races out-qualifying the teammate — driver skill vs. car |
    | `starts` | Race starts in the season — seat security |
    """)
    st.dataframe(prof.head(50), width="stretch", height=320)

with t2:
    feat = st.selectbox("Feature", CLUSTER_FEATURE_COLS, index=1)
    st.plotly_chart(get_plotly_theme(px.histogram(prof, x=feat, nbins=40, title=f"Distribution of {feat}")), width="stretch")
    st.dataframe(prof[CLUSTER_FEATURE_COLS].describe().T.round(3), width="stretch")

with t3:
    corr = prof[CLUSTER_FEATURE_COLS].corr().round(2)
    st.plotly_chart(get_plotly_theme(px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                                               title="Pearson Correlation Between Clustering Features")), width="stretch")
