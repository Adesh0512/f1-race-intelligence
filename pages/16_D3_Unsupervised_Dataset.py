import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "09_unsupervised_dataset"))
from db_utils import apply_f1_theme, get_plotly_theme, page_header, DIV_SCALE
from build_unsupervised_dataset import CLUSTER_FEATURE_COLS, MIN_STARTS, ID_COLS
from sklearn.preprocessing import StandardScaler

apply_f1_theme()

page_header('Dashboard 3', 'Unsupervised learning', 'Driver-season dataset',
            '703 unlabelled driver-season profiles from 1994–2024, built for clustering. There is no target column.')

prof = pd.read_csv(os.path.join(ROOT, "09_unsupervised_dataset", "driver_season_profiles.csv"))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Driver-Season Profiles", f"{len(prof):,}")
c2.metric("Unique Drivers", prof["driver_id"].nunique())
c3.metric("Seasons", f"{prof['season'].min()}–{prof['season'].max()}")
c4.metric("Clustering Features", len(CLUSTER_FEATURE_COLS), "No target column")

st.markdown("---")
t0, t1, t2, t3 = st.tabs(["Dataset Overview", "Data Dictionary & Sample", "Feature Distributions", "Feature Correlation"])


@st.cache_data
def raw_groups():
    """How many driver-seasons exist before the minimum-starts filter."""
    d = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), usecols=["driver_id", "season", "race_id"])
    return len(d), d.groupby(["driver_id", "season"]).ngroups


with t0:
    n_entries, n_groups = raw_groups()
    F = prof[CLUSTER_FEATURE_COLS]
    st.markdown(f"""
    #### Driver-season performance profiles, 1994–2024
    **File:** `09_unsupervised_dataset/driver_season_profiles.csv` · **Source:** built from the F1 Race Lab feature store
    (Ergast Formula 1 historical results) by `build_unsupervised_dataset.py`. Each record summarises **one driver's whole season**.
    """)
    a, b, _ = st.columns([1, 1, 2])  # records and feature counts are already in the header row
    a.metric("Attributes", len(prof.columns), f"{len(ID_COLS)} identifiers + {len(CLUSTER_FEATURE_COLS)} features", delta_color="off")
    b.metric("Class label", "None", "unsupervised", delta_color="off")

    st.markdown("#### Characteristics")
    r_gf = F["avg_grid"].corr(F["avg_finish"])
    st.markdown(f"""
    - **Unlabelled and numeric:** {len(CLUSTER_FEATURE_COLS)} continuous measures per driver-season, no target column and **{int(F.isna().sum().sum())} missing values**.
    - **Very different scales:** `starts` ranges {F['starts'].min():.0f}–{F['starts'].max():.0f} while the rates run 0–1, so the data must be standardised.
    - **Skewed outcomes:** {(F['win_rate'] == 0).mean():.0%} of driver-seasons have no win at all; only a small group wins often.
    - **Related but distinct signals:** average grid and average finish correlate at r = {r_gf:.2f}, while DNF rate and consistency add separate information.
    - **A continuum, not islands:** performance shades from front-runners to backmarkers, so clusters will touch rather than sit far apart.
    """)

    st.markdown("#### Preprocessing and feature selection")
    st.dataframe(pd.DataFrame([
        ("1. Change the grain", f"Group the {n_entries:,} driver-race entries by driver and season ({n_groups:,} driver-seasons)"),
        ("2. Filter", f"Keep seasons with at least {MIN_STARTS} starts, removing one-off substitutes: {n_groups - len(prof):,} dropped, {len(prof):,} kept"),
        ("3. Build features", "Average grid, average finish, finish spread, win / podium / points / DNF rates, teammate qualifying record, starts"),
        ("4. Select features", "Keep the 9 measures of how a driver performed: qualifying pace, race pace, consistency, results, reliability, "
                               "teammate comparison and seat security. Leave out names, team and season, so tiers come from performance, "
                               "not from who or when"),
        ("5. Missing values", f"None found ({int(F.isna().sum().sum())}); an undefined finish spread would be set to 0 as a safeguard"),
        ("6. Standardise", "z-score every feature (mean 0, standard deviation 1) so no feature dominates the Euclidean distance"),
    ], columns=["Step", "What is done"]), width="stretch")

    st.markdown("#### Why this dataset suits clustering")
    st.markdown(f"""
    - There is **no label** to predict: the question is which groups of drivers exist, which is exactly what clustering answers.
    - **{len(prof):,} records × {len(CLUSTER_FEATURE_COLS)} numeric features** is large enough for stable clusters and small enough for every algorithm, including the O(n²) ones.
    - After standardisation all features are on one scale, so **distance means similarity** in performance.
    - The result can be **checked against reality** (the championship standings), which the clustering never sees.
    """)

    st.markdown("#### The prepared dataset (standardised, what the algorithms receive)")
    Z = pd.DataFrame(StandardScaler().fit_transform(F), columns=CLUSTER_FEATURE_COLS)
    st.dataframe(pd.concat([prof[["driver_name", "season"]], Z.round(2)], axis=1).head(10), width="stretch")
    st.caption(f"Check: every standardised column has mean {abs(Z.mean()).max():.2f} and standard deviation {Z.std(ddof=0).mean():.2f}.")

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
    st.plotly_chart(get_plotly_theme(px.imshow(corr, text_auto=".2f", color_continuous_scale=DIV_SCALE, zmin=-1, zmax=1,
                                               title="Pearson Correlation Between Clustering Features", aspect="auto", height=560)
                                     .update_xaxes(tickangle=-30)), width="stretch")
