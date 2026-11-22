import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, TIER_COLORS, page_header

apply_f1_theme()

page_header('Dashboard 3', 'Unsupervised learning', 'K-Means: three driver tiers',
            'The chosen algorithm sorts every driver-season into Title Contenders, Midfield Regulars or Backmarkers, without being told what those are.')

mod = os.path.join(ROOT, "11_clustering_algorithm")
cl = pd.read_csv(os.path.join(mod, "driver_season_clusters.csv"))
cent = pd.read_csv(os.path.join(mod, "cluster_profiles.csv"))
COLORS = TIER_COLORS

cols = st.columns(len(cent))
for col, r in zip(cols, cent.itertuples()):
    col.metric(r.cluster_name, f"{r.size} seasons", f"avg finish P{r.avg_finish:.1f} · win {r.win_rate*100:.1f}%")

st.markdown("---")
t4, t1, t2, t7, t5, t3, t6 = st.tabs(["How K-Means Works", "Cluster Map (PCA)", "Centroid Profiles", "What the Tiers Mean",
                                       "Tiers by Era", "Driver Explorer", "Classify a Season"])

with t7:
    import json
    from sklearn.preprocessing import StandardScaler
    FEATS = ["avg_grid", "avg_finish", "finish_std", "win_rate", "podium_rate", "points_rate", "dnf_rate", "teammate_quali_rate", "starts"]
    Z = pd.DataFrame(StandardScaler().fit_transform(cl[FEATS]), columns=FEATS)
    cl_d = cl.assign(dist=np.linalg.norm(Z.values - Z.groupby(cl["cluster"]).transform("mean").values, axis=1))
    metrics = json.load(open(os.path.join(ROOT, "12_clustering_metrics", "clustering_metrics.json")))
    link = pd.read_csv(os.path.join(ROOT, "12_clustering_metrics", "cluster_feature_experiment.csv")).set_index("model")
    MEANING = {
        "Title Contenders": "Start near the front and finish on the podium more often than not. These are the drivers fighting for the championship.",
        "Midfield Regulars": "Solid points scorers in mid-grid cars: rarely win, often finish in the top 10, and retire more often than the leaders.",
        "Backmarkers": "Start and finish at the back, score points rarely and retire most often: usually the slowest cars on the grid.",
    }
    for r in cent.itertuples():
        typical = cl_d[cl_d["cluster"] == r.cluster].nsmallest(3, "dist")
        st.markdown(f"##### {r.cluster_name} · {r.size} driver-seasons")
        st.markdown(f"{MEANING[r.cluster_name]} Average grid **P{r.avg_grid:.1f}**, average finish **P{r.avg_finish:.1f}**, "
                    f"wins **{r.win_rate:.0%}**, podiums **{r.podium_rate:.0%}**, points **{r.points_rate:.0%}**, retirements **{r.dnf_rate:.0%}** of starts. "
                    f"Most typical seasons (closest to the centre): " + ", ".join(f"{t.driver_name} {t.season} ({t.constructor_name})" for t in typical.itertuples()) + ".")
    st.markdown("#### Why the tiers matter in practice")
    st.markdown(f"""
    - **They match reality without being told it:** {metrics['contenders_in_top3_standing_pct']:.0f}% of Title Contender seasons ended in the
      championship top 3, although the standings were never used for clustering.
    - **They help prediction:** adding a driver's previous-season tier to grid position raises the winner classifier's PR-AUC from
      {link.loc['Grid only', 'pr_auc']:.2f} to {link.loc['Grid + previous-season tier', 'pr_auc']:.2f} (Clustering Metrics → Clusters → Classifier).
    - **They measure how competitive an era is:** the share of Title Contenders per season (Tiers by Era tab) shows dominant eras vs. open fights.
    - **They support scouting and team decisions:** a driver who keeps out-qualifying a teammate while in the Midfield tier is performing above the car.
    - **They track careers:** the Driver Explorer shows a driver moving between tiers as their car improves or declines.
    """)

with t1:
    seasons = st.slider("Seasons", int(cl["season"].min()), int(cl["season"].max()), (1994, 2024))
    view = cl[cl["season"].between(*seasons)]
    fig = px.scatter(view, x="pca_1", y="pca_2", color="cluster_name", color_discrete_map=COLORS,
                     hover_data=["driver_name", "season", "constructor_name", "avg_finish", "win_rate"],
                     title="Driver-Seasons Projected to 2-D with PCA")
    st.plotly_chart(get_plotly_theme(fig), width="stretch")

with t2:
    st.dataframe(cent.round(3), width="stretch", hide_index=True)
    radar_cols = ["win_rate", "podium_rate", "points_rate", "teammate_quali_rate", "dnf_rate"]
    norm = cent.copy()
    norm["grid_pace"] = 1 - (cent["avg_grid"] - 1) / 19
    norm["race_pace"] = 1 - (cent["avg_finish"] - 1) / 19
    axes = ["grid_pace", "race_pace"] + radar_cols
    fig = go.Figure([go.Scatterpolar(r=list(norm.loc[i, axes]) + [norm.loc[i, axes[0]]], theta=axes + [axes[0]], fill="toself",
                                     name=norm.loc[i, "cluster_name"], line=dict(color=COLORS[norm.loc[i, "cluster_name"]])) for i in norm.index])
    fig.update_layout(title="Tier fingerprints (pace axes scaled 0–1, P1 = 1)", polar=dict(radialaxis=dict(range=[0, 1])))
    st.plotly_chart(get_plotly_theme(fig), width="stretch")
    long = cent.melt(id_vars=["cluster_name"], value_vars=["win_rate", "podium_rate", "points_rate", "dnf_rate", "teammate_quali_rate"])
    st.plotly_chart(get_plotly_theme(px.bar(long, x="variable", y="value", color="cluster_name", barmode="group",
                                            color_discrete_map=COLORS, title="Centroid Rates by Cluster")), width="stretch")

with t5:
    era = cl.groupby(["season", "cluster_name"]).size().reset_index(name="drivers")
    st.plotly_chart(get_plotly_theme(px.area(era, x="season", y="drivers", color="cluster_name", color_discrete_map=COLORS,
                                             category_orders={"cluster_name": list(COLORS)},
                                             title="How many drivers per tier, each season")), width="stretch")
    share = cl.groupby("season")["cluster_name"].apply(lambda s: (s == "Title Contenders").mean() * 100).reset_index(name="pct")
    st.plotly_chart(get_plotly_theme(px.line(share, x="season", y="pct", markers=True, color_discrete_sequence=[F1_RED],
                                             title="% of the field that are Title Contenders (higher = more competitive era)")), width="stretch")

with t6:
    import joblib
    bundle = joblib.load(os.path.join(ROOT, "models", "champion_kmeans_clusterer.joblib"))
    st.markdown("Describe a driver's season and the saved K-Means model assigns its tier (nearest centroid).")
    a, b, c = st.columns(3)
    vals = {
        "avg_grid": a.slider("Average grid", 1.0, 20.0, 6.0, 0.5),
        "avg_finish": a.slider("Average finish", 1.0, 20.0, 7.0, 0.5),
        "finish_std": a.slider("Finish std-dev", 0.0, 9.0, 4.5, 0.1),
        "win_rate": b.slider("Win rate", 0.0, 1.0, 0.10, 0.01),
        "podium_rate": b.slider("Podium rate", 0.0, 1.0, 0.35, 0.01),
        "points_rate": b.slider("Points rate", 0.0, 1.0, 0.75, 0.01),
        "dnf_rate": c.slider("DNF rate", 0.0, 1.0, 0.15, 0.01),
        "teammate_quali_rate": c.slider("Beat teammate in quali", 0.0, 1.0, 0.55, 0.01),
        "starts": c.slider("Starts", 5, 24, 22),
    }
    x = bundle["scaler"].transform(pd.DataFrame([vals])[bundle["features"]])
    dist = np.linalg.norm(bundle["model"].cluster_centers_ - x, axis=1)
    tier = bundle["tier_names"][bundle["remap"][int(dist.argmin())]]
    st.success(f"### Assigned tier: {tier}")
    dd = pd.DataFrame({"tier": [bundle["tier_names"][bundle["remap"][i]] for i in range(len(dist))], "distance": dist}).sort_values("distance")
    st.plotly_chart(get_plotly_theme(px.bar(dd, x="distance", y="tier", orientation="h", color="tier", color_discrete_map=COLORS,
                                            title="Distance to each centroid (standardised space): smallest wins")), width="stretch")

with t3:
    driver = st.selectbox("Driver", sorted(cl["driver_name"].unique()),
                          index=sorted(cl["driver_name"].unique()).index("Lewis Hamilton") if "Lewis Hamilton" in set(cl["driver_name"]) else 0)
    d = cl[cl["driver_name"] == driver].sort_values("season")
    st.plotly_chart(get_plotly_theme(px.scatter(d, x="season", y="avg_finish", color="cluster_name", color_discrete_map=COLORS,
                                                size="starts", hover_data=["constructor_name"], title=f"{driver}: Tier by Season")
                                     .update_yaxes(autorange="reversed")), width="stretch")
    st.dataframe(d[["season", "constructor_name", "cluster_name", "avg_grid", "avg_finish", "win_rate", "podium_rate"]].round(3),
                 width="stretch", hide_index=True)

with t4:
    st.markdown(r"""
    1. **Initialise** k = 3 centroids with *k-means++* (spread-out seeding), 10 restarts, keep the best.
    2. **Assign** each driver-season to its nearest centroid (Euclidean distance on standardised features).
    3. **Update** each centroid to the mean of its members.
    4. **Repeat** until assignments stop changing (converged in 13 iterations).

    Objective (inertia / WCSS): $J = \sum_{j=1}^{k} \sum_{x_i \in C_j} \lVert x_i - \mu_j \rVert^2$

    **Parameter selection**

    | Parameter | Value | Why |
    |---|---|---|
    | k (clusters) | 3 | Elbow of the inertia curve; the Ward dendrogram's largest gap also gives 3; k = 2 only splits winners from the rest |
    | Features | 9, z-score standardised | Euclidean distance needs equal scales |
    | Initialisation | k-means++ | Spreads the starting centroids out, so it avoids poor local minima |
    | Restarts (n_init) | 10 | Keeps the run with the lowest inertia |
    | random_state | 42 | Same result every run (reproducible) |

    **Why K-Means won:** best Silhouette, Davies-Bouldin and Calinski-Harabasz among the 4 algorithms that assign every point,
    high stability across seeds, and centroids that read directly as performance tiers.
    """)
    st.code("""X = StandardScaler().fit_transform(profiles[FEATURES])          # 703 × 9, mean 0, sd 1
km = KMeans(n_clusters=3, init="k-means++", n_init=10, random_state=42).fit(X)
labels = km.labels_                     # tier of every driver-season
centres = km.cluster_centers_           # one average profile per tier
# clusters are renamed by average finish: best = Title Contenders""", language="python")
