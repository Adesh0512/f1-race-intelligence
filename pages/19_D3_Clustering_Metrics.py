import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, TIER_COLORS, page_header

apply_f1_theme()

page_header('Dashboard 3', 'Unsupervised learning', 'How good are the clusters?',
            'Internal validity, stability across reruns, and a check against the real championship standings.', marks=5)

mod = os.path.join(ROOT, "12_clustering_metrics")
with open(os.path.join(mod, "clustering_metrics.json")) as f:
    m = json.load(f)
per = pd.read_csv(os.path.join(mod, "per_cluster_silhouette.csv"))
cont = pd.read_csv(os.path.join(mod, "championship_contingency.csv"), index_col=0)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Silhouette", f"{m['silhouette']:.4f}", "higher is better")
c2.metric("Davies-Bouldin", f"{m['davies_bouldin']:.4f}", "lower is better", delta_color="inverse")
c3.metric("Calinski-Harabasz", f"{m['calinski_harabasz']:.1f}", "higher is better")
c4.metric("Seed Stability (ARI)", f"{m['seed_stability_ari_mean']:.4f}", f"bootstrap {m['bootstrap_stability_ari_mean']:.4f}")

st.markdown("---")
t1, t2, t4, t3 = st.tabs(["Internal Validity", "vs. Championship Standing", "Clusters → Classifier", "Metric Definitions"])

with t1:
    st.dataframe(per, width="stretch", hide_index=True)
    from sklearn.metrics import silhouette_samples
    sys.path.insert(0, os.path.join(ROOT, "09_unsupervised_dataset"))
    from build_unsupervised_dataset import load_profiles
    _, X = load_profiles()
    cl = pd.read_csv(os.path.join(ROOT, "11_clustering_algorithm", "driver_season_clusters.csv"))
    cl["silhouette"] = silhouette_samples(X, cl["cluster"])
    cl = cl.sort_values(["cluster", "silhouette"], ascending=[True, False]).reset_index(drop=True)
    fig = px.bar(cl, x=cl.index, y="silhouette", color="cluster_name", hover_data=["driver_name", "season"],
                 color_discrete_map=TIER_COLORS,
                 title="Silhouette plot: every driver-season, sorted within its cluster (bars below 0 = closer to another cluster)")
    fig.add_hline(y=m["silhouette"], line=dict(dash="dash", color="#15181D"), annotation_text=f"mean {m['silhouette']:.3f}")
    st.plotly_chart(get_plotly_theme(fig.update_traces(marker_line_width=0).update_layout(bargap=0, xaxis_title="driver-season")), width="stretch")
    st.plotly_chart(get_plotly_theme(px.bar(per, x="cluster_name", y="mean_silhouette", color="cluster_name",
                                            color_discrete_map=TIER_COLORS,
                                            title="Mean Silhouette per Cluster")), width="stretch")

with t2:
    st.markdown("Championship standing was **never used** to fit the clusters — it is only used afterwards to check that the tiers make sense.")
    st.plotly_chart(get_plotly_theme(px.imshow(cont, text_auto=True, color_continuous_scale="Reds",
                                               labels=dict(x="Championship standing", y="Cluster"),
                                               title="Cluster vs. Championship Standing Tier")), width="stretch")
    e1, e2, e3 = st.columns(3)
    e1.metric("Adjusted Rand Index", f"{m['external_ari_vs_championship_tier']:.4f}")
    e2.metric("Normalised Mutual Info", f"{m['external_nmi_vs_championship_tier']:.4f}")
    e3.metric("Contenders in Top-3 Standing", f"{m['contenders_in_top3_standing_pct']:.1f}%")

with t4:
    exp = pd.read_csv(os.path.join(mod, "cluster_feature_experiment.csv"))
    st.markdown("**Question:** does the unsupervised tier help the supervised winner classifier? "
                "To stay leakage-safe, K-Means is refitted on 1994–2021 seasons only and each race gets the driver's **previous-season** tier.")
    st.dataframe(exp, width="stretch", hide_index=True)
    st.plotly_chart(get_plotly_theme(px.bar(exp.melt(id_vars="model", value_vars=["roc_auc", "pr_auc"]), x="variable", y="value", color="model",
                                            barmode="group", title="2022–2024 holdout")), width="stretch")
    st.info("**Finding:** the tier alone adds strong signal to grid position (PR-AUC ≈ +0.09), so the clusters capture real performance structure. "
            "On top of the 16 engineered features it is **redundant**: rolling form already encodes it. So the champion model does not include it.")

with t3:
    st.markdown(r"""
    | Metric | Formula / idea | Range | Better |
    |---|---|---|---|
    | **Silhouette** | $s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$, a = mean intra-cluster distance, b = mean distance to nearest other cluster | -1 … 1 | Higher |
    | **Davies-Bouldin** | Mean over clusters of the worst ratio (scatterᵢ + scatterⱼ) / distance(centroidᵢ, centroidⱼ) | 0 … ∞ | Lower |
    | **Calinski-Harabasz** | Between-cluster dispersion / within-cluster dispersion, scaled by (n − k)/(k − 1) | 0 … ∞ | Higher |
    | **Inertia (WCSS)** | Sum of squared distances to the assigned centroid | 0 … ∞ | Lower (for fixed k) |
    | **Adjusted Rand Index** | Pair-counting agreement between two labelings, corrected for chance | -0.5 … 1 | Higher |
    | **NMI** | Mutual information between labelings, normalised | 0 … 1 | Higher |
    """)
