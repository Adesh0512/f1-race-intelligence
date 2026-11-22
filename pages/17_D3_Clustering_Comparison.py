import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "09_unsupervised_dataset"))
sys.path.insert(0, os.path.join(ROOT, "10_clustering_comparison"))
import numpy as np
from sklearn.decomposition import PCA
from build_unsupervised_dataset import load_profiles
from clustering_comparison import make_models, tune_dbscan
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header, pretty, GREEN

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
t3, t0, t1, t2, t5, t4 = st.tabs(["Why These 6 Algorithms", "Clusters Side by Side", "Benchmark Table", "Choosing k",
                                   "Tuning GMM & DBSCAN", "Hierarchical Dendrogram"])


@st.cache_data
def fit_all(k):
    """Refits all six algorithms with the module's own settings and returns labels on one shared 2-D PCA map."""
    prof, X = load_profiles()
    eps, ms = tune_dbscan(X)
    xy = PCA(n_components=2, random_state=42).fit_transform(X)
    frames = []
    for name, make in make_models(k, eps, ms).items():
        lab = np.asarray(make(42).fit_predict(X))
        frames.append(pd.DataFrame({"algorithm": name, "PC 1": xy[:, 0], "PC 2": xy[:, 1], "driver": prof["driver_name"],
                                    "season": prof["season"], "cluster": np.where(lab == -1, "Noise", "Cluster " + (lab + 1).astype(str))}))
    return pd.concat(frames, ignore_index=True), eps, ms


with t0:
    k = int(champ["n_clusters"])
    pts, eps, ms = fit_all(k)
    st.markdown("#### Parameters used")
    st.dataframe(pd.DataFrame([
        ("K-Means", f"k = {k}, init = k-means++, 10 restarts, seed 42", "k from the elbow method (Choosing k tab)"),
        ("K-Medoids (PAM)", f"k = {k}, 10 restarts, seed 42", "same k, so the comparison is like for like"),
        ("Agglomerative (Ward)", f"k = {k}, linkage = ward", "Ward merges the pair that adds least variance; cut at k"),
        ("Gaussian Mixture", f"k = {k} components, full covariance, seed 42", "BIC/AIC checked (Tuning tab); same k for a fair comparison"),
        ("BIRCH", f"k = {k}, threshold = 0.5", "threshold sets how tightly the CF-tree summarises points"),
        ("DBSCAN", f"eps = {eps}, min_samples = {ms}", "grid search: ≥ 3 clusters, ≤ 15% noise, best silhouette; k-distance curve"),
    ], columns=["Algorithm", "Parameters", "How they were chosen"]), width="stretch")

    st.markdown("#### Clusters each algorithm produced")
    sizes = (pts.groupby(["algorithm", "cluster"]).size().reset_index(name="n")
             .sort_values(["algorithm", "n"], ascending=[True, False]))
    summary = sizes.groupby("algorithm").apply(
        lambda g: " / ".join(f"{n}" for c, n in zip(g["cluster"], g["n"]) if c != "Noise")
        + (f"  + {int(g.loc[g['cluster'] == 'Noise', 'n'].sum())} noise" if (g["cluster"] == "Noise").any() else ""), include_groups=False)
    st.dataframe(res[["algorithm", "n_clusters", "silhouette", "stability_ari"]].assign(
        cluster_sizes=res["algorithm"].map(summary)), width="stretch")
    order = res["algorithm"].tolist()
    palette = {f"Cluster {i}": c for i, c in enumerate([F1_RED, GREEN, "#9AA1AB", "#C99700", "#2F6FDB"], start=1)} | {"Noise": "#15181D"}
    fig = px.scatter(pts, x="PC 1", y="PC 2", color="cluster", facet_col="algorithm", facet_col_wrap=3,
                     category_orders={"algorithm": order, "cluster": sorted(pts["cluster"].unique())},
                     color_discrete_map=palette, hover_data=["driver", "season"], height=640, opacity=0.75,
                     title="The same 703 driver-seasons on one 2-D map (PCA), coloured by each algorithm's clusters")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(get_plotly_theme(fig.update_traces(marker_size=4)).update_layout(margin=dict(t=120)), width="stretch")
    st.caption("Cluster numbers are arbitrary per algorithm; compare the shapes. The map is only for viewing: "
               "every algorithm clustered all 9 standardised features.")

    best = res.loc[res["rank_score"].idxmin()]
    km = res.set_index("algorithm")
    big = sizes[(sizes["algorithm"] == "DBSCAN") & (sizes["cluster"] != "Noise")]["n"].max()
    st.success(f"""**Most suitable: {best['algorithm']}.** It has the best mean rank ({best['rank_score']}) across the five ranking measures.
Among the algorithms that place every driver-season in a cluster it has the highest silhouette ({best['silhouette']:.3f}) and
Calinski-Harabasz ({best['calinski_harabasz']:.0f}) and the lowest Davies-Bouldin ({best['davies_bouldin']:.3f}), and it stays
stable when rerun (ARI {best['stability_ari']:.2f}). K-Medoids is a close second but slower. Ward and BIRCH split the midfield
differently each run (ARI ≈ {km.loc['BIRCH', 'stability_ari']:.2f}). The Gaussian Mixture is stable but its clusters overlap
(silhouette {km.loc['Gaussian Mixture', 'silhouette']:.3f}). DBSCAN finds no real density gaps: it puts {big} of {len(pts) // len(res)}
seasons in one cluster and labels {km.loc['DBSCAN', 'noise_pct']:.1f}% as noise. K-Means centroids also read directly as tiers:
contender, midfield, backmarker.""")

with t1:
    st.dataframe(res.assign(algorithm=res["algorithm"].where(~res["champion"].astype(bool), res["algorithm"] + " (Champion)"))
                 .drop(columns=["champion"]), width="stretch", hide_index=True)
    metric = st.radio("Metric", ["silhouette", "davies_bouldin", "calinski_harabasz", "stability_ari", "runtime_ms"], horizontal=True, format_func=pretty)
    fig = px.bar(res, x="algorithm", y=metric, color="algorithm", title=f"{pretty(metric)} by algorithm",
                 color_discrete_map={"K-Means": F1_RED}, color_discrete_sequence=["#9AA1AB"], text_auto=".3~f")
    fig.update_traces(textposition="outside", cliponaxis=False).update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(get_plotly_theme(fig), width="stretch")
    st.info("**Ranking rule:** mean rank across Silhouette (↑), Davies-Bouldin (↓), Calinski-Harabasz (↑), "
            "bootstrap stability ARI (↑) and noise % (↓). DBSCAN's metrics are computed on non-noise points only.")

with t2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks["k"], y=ks["inertia"], name="Inertia (WCSS)", mode="lines+markers", line=dict(color=F1_RED)))
    fig.add_trace(go.Scatter(x=ks["k"], y=ks["silhouette"], name="Silhouette", mode="lines+markers", yaxis="y2", line=dict(color=GREEN)))
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
