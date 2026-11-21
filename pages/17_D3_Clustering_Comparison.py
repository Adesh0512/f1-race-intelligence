import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED

apply_f1_theme()

st.title("⚖️ Dashboard 3 · Clustering Algorithm Comparison (5 Algorithms)")
st.markdown("### K-Means vs. Agglomerative (Ward) vs. Gaussian Mixture vs. BIRCH vs. DBSCAN")

mod = os.path.join(ROOT, "10_clustering_comparison")
res = pd.read_csv(os.path.join(mod, "comparison_results.csv"))
ks = pd.read_csv(os.path.join(mod, "k_selection.csv"))
champ = res[res["champion"]].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Algorithms Compared", len(res))
c2.metric("Chosen k", int(champ["n_clusters"]), "Elbow method")
c3.metric("Champion", champ["algorithm"])
c4.metric("Champion Silhouette", f"{champ['silhouette']:.4f}")

st.markdown("---")
t1, t2, t4, t3 = st.tabs(["📊 Benchmark Table", "📐 Choosing k", "🌳 Hierarchical Dendrogram", "🧠 Why These 5 Algorithms"])

with t1:
    st.dataframe(res.drop(columns=["champion"]), width="stretch", hide_index=True)
    metric = st.radio("Metric", ["silhouette", "davies_bouldin", "calinski_harabasz", "stability_ari", "runtime_ms"], horizontal=True)
    fig = px.bar(res, x="algorithm", y=metric, color="algorithm", title=f"{metric} by algorithm",
                 color_discrete_sequence=[F1_RED, "#00BDAE", "#F2C811", "#118DFF", "#8B949E"])
    st.plotly_chart(get_plotly_theme(fig), width="stretch")
    st.info("**Ranking rule:** mean rank across Silhouette (↑), Davies-Bouldin (↓), Calinski-Harabasz (↑), "
            "bootstrap stability ARI (↑) and noise % (↓). DBSCAN's metrics are computed on non-noise points only.")

with t2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks["k"], y=ks["inertia"], name="Inertia (WCSS)", mode="lines+markers", line=dict(color=F1_RED)))
    fig.add_trace(go.Scatter(x=ks["k"], y=ks["silhouette"], name="Silhouette", mode="lines+markers", yaxis="y2", line=dict(color="#00BDAE")))
    fig.update_layout(title="Elbow & Silhouette Methods (K-Means, k = 2..8)", xaxis_title="k",
                      yaxis=dict(title="Inertia"), yaxis2=dict(title="Silhouette", overlaying="y", side="right"))
    st.plotly_chart(get_plotly_theme(fig), width="stretch")
    st.markdown("The **elbow** (largest bend in inertia) is at **k = 3**. k = 2 has a higher silhouette but only splits "
                "'front-runners vs. the rest', which is too coarse for useful tiers.")

with t4:
    from scipy.cluster.hierarchy import linkage, dendrogram
    sys.path.insert(0, os.path.join(ROOT, "09_unsupervised_dataset"))
    from build_unsupervised_dataset import load_profiles
    _, X = load_profiles()
    Z = linkage(X, method="ward")
    d = dendrogram(Z, truncate_mode="lastp", p=30, no_plot=True)
    fig = go.Figure()
    for xs, ys in zip(d["icoord"], d["dcoord"]):
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#C9D1D9", width=1.2), hoverinfo="skip", showlegend=False))
    cut = (Z[-3, 2] + Z[-2, 2]) / 2  # height that leaves exactly 3 clusters
    fig.add_hline(y=cut, line=dict(color=F1_RED, dash="dash"), annotation_text="cut → 3 clusters")
    fig.update_layout(title="Agglomerative (Ward) dendrogram: last 30 merges of 703 driver-seasons",
                      xaxis=dict(showticklabels=False, title="merged groups"), yaxis_title="Ward merge distance")
    st.plotly_chart(get_plotly_theme(fig), width="stretch")
    st.markdown("Each merge joins the two groups whose union increases within-cluster variance the least. Cutting the tree where the vertical "
                "gaps are largest gives **3 clusters**, the same k chosen by the elbow method. The tallest jump separates the dominant seasons from the rest.")

with t3:
    st.markdown("""
    | Algorithm | Family | Key idea | Strength | Weakness |
    |---|---|---|---|---|
    | **K-Means** | Centroid | Minimise within-cluster squared distance | Fast, stable, interpretable centroids | Needs k, assumes spherical clusters |
    | **Agglomerative (Ward)** | Hierarchical | Merge clusters with least variance increase | Dendrogram, no random init | O(n²) memory, merges are final |
    | **Gaussian Mixture** | Probabilistic | EM fits k Gaussians, soft membership | Elliptical clusters, probabilities | Sensitive to init, more parameters |
    | **BIRCH** | Tree / incremental | CF-tree summarises data in one pass | Scales to huge data | Threshold-sensitive |
    | **DBSCAN** | Density | Core points with ≥ min_samples within eps | Finds any shape, flags outliers | No k but eps-sensitive, struggles with varying density |
    """)
