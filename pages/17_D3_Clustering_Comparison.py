import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header

apply_f1_theme()

page_header('Dashboard 3', 'Unsupervised learning', 'Comparing six clustering algorithms',
            'K-Means, K-Medoids, Agglomerative (Ward), Gaussian Mixture, BIRCH and DBSCAN, run on the same 703 profiles and scored the same way.')

mod = os.path.join(ROOT, "10_clustering_comparison")
res = pd.read_csv(os.path.join(mod, "comparison_results.csv"))
ks = pd.read_csv(os.path.join(mod, "k_selection.csv"))
bic = pd.read_csv(os.path.join(mod, "gmm_bic_aic.csv"))
kd = pd.read_csv(os.path.join(mod, "dbscan_k_distance.csv"))
champ = res[res["champion"]].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Algorithms Compared", len(res))
c2.metric("Chosen k", int(champ["n_clusters"]), "Elbow method")
c3.metric("Champion", champ["algorithm"])
c4.metric("Champion Silhouette", f"{champ['silhouette']:.4f}")

st.markdown("---")
t1, t2, t5, t4, t3 = st.tabs(["Benchmark Table", "Choosing k", "Tuning GMM & DBSCAN", "Hierarchical Dendrogram", "Why These 6 Algorithms"])

with t1:
    st.dataframe(res.drop(columns=["champion"]), width="stretch", hide_index=True)
    metric = st.radio("Metric", ["silhouette", "davies_bouldin", "calinski_harabasz", "stability_ari", "runtime_ms"], horizontal=True)
    fig = px.bar(res, x="algorithm", y=metric, color="algorithm", title=f"{metric} by algorithm",
                 color_discrete_map={"K-Means": F1_RED}, color_discrete_sequence=["#9AA1AB"])
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

with t5:
    a, b = st.columns(2)
    fig = go.Figure([go.Scatter(x=bic["k"], y=bic["bic"], name="BIC", mode="lines+markers", line=dict(color=F1_RED)),
                     go.Scatter(x=bic["k"], y=bic["aic"], name="AIC", mode="lines+markers", line=dict(color="#59616C", dash="dash"))])
    fig.update_layout(title="Gaussian Mixture: BIC and AIC by number of components", xaxis_title="components (k)", yaxis_title="lower is better")
    a.plotly_chart(get_plotly_theme(fig), width="stretch")
    k_bic = int(bic.loc[bic["bic"].idxmin(), "k"])
    a.markdown(f"BIC is lowest at **k = {k_bic}**: with full covariance, extra Gaussians keep fitting the density better. "
               "That is a density-modelling answer, not a tier count, so all algorithms are compared at the elbow's **k = 3**.")
    eps, ms = kd["chosen_eps"].iat[0], int(kd["min_samples"].iat[0])
    fig = go.Figure([go.Scatter(x=kd["rank"], y=kd["k_distance"], mode="lines", line=dict(color="#15181D"), name=f"{ms}-NN distance")])
    fig.add_hline(y=eps, line=dict(color=F1_RED, dash="dash"), annotation_text=f"chosen eps = {eps}")
    fig.update_layout(title=f"DBSCAN k-distance curve (distance to {ms}th nearest neighbour, sorted)", xaxis_title="points, sorted", yaxis_title="distance")
    b.plotly_chart(get_plotly_theme(fig), width="stretch")
    b.markdown(f"eps should sit near the curve's knee. At eps = {eps}, **{(kd['k_distance'] > eps).mean() * 100:.0f}%** of points are not core points; "
               f"most still join a cluster as border points, leaving {res.loc[res['algorithm'] == 'DBSCAN', 'noise_pct'].iat[0]:.1f}% as noise. The long upper tail is the sparse group of dominant seasons that one eps cannot cover.")

with t4:
    from scipy.cluster.hierarchy import linkage, dendrogram
    sys.path.insert(0, os.path.join(ROOT, "09_unsupervised_dataset"))
    from build_unsupervised_dataset import load_profiles
    _, X = load_profiles()
    Z = linkage(X, method="ward")
    d = dendrogram(Z, truncate_mode="lastp", p=30, no_plot=True)
    fig = go.Figure()
    for xs, ys in zip(d["icoord"], d["dcoord"]):
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#59616C", width=1.2), hoverinfo="skip", showlegend=False))
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
    | **K-Medoids (PAM)** | Medoid | Centres must be real data points; minimise total distance | Robust to outliers, each centre is an actual driver-season | O(n²) distance matrix, slower |
    | **Agglomerative (Ward)** | Hierarchical | Merge clusters with least variance increase | Dendrogram, no random init | O(n²) memory, merges are final |
    | **Gaussian Mixture** | Probabilistic | EM fits k Gaussians, soft membership | Elliptical clusters, probabilities | Sensitive to init, more parameters |
    | **BIRCH** | Tree / incremental | CF-tree summarises data in one pass | Scales to huge data | Threshold-sensitive |
    | **DBSCAN** | Density | Core points with ≥ min_samples within eps | Finds any shape, flags outliers | No k but eps-sensitive, struggles with varying density |
    """)
