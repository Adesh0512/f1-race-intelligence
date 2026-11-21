"""
Champion Clustering Algorithm: K-Means (Parameter 11)
=====================================================
Fits the champion K-Means model (k = 3, k-means++ init, 10 restarts) selected in
Parameter 10 on 703 standardised driver-season profiles, then:

1. Names each cluster by its centroid (ordered by mean finish position)
2. Projects profiles to 2-D with PCA for visualisation
3. Persists the scaler + model to models/champion_kmeans_clusterer.joblib

Outputs:
- 11_clustering_algorithm/driver_season_clusters.csv  (each profile + cluster + PCA coords)
- 11_clustering_algorithm/cluster_profiles.csv        (centroids in original units)
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "..", "09_unsupervised_dataset"))
from build_unsupervised_dataset import load_profiles, CLUSTER_FEATURE_COLS

K = 3
# Clusters are ordered best -> worst by centroid mean finish position
TIER_NAMES = ["Title Contenders", "Midfield Regulars", "Backmarkers"]


def fit_champion(k=K):
    prof, _ = load_profiles()
    scaler = StandardScaler().fit(prof[CLUSTER_FEATURE_COLS])
    X = scaler.transform(prof[CLUSTER_FEATURE_COLS])
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42).fit(X)

    # Relabel raw cluster ids 0..k-1 so that 0 = best mean finish
    order = np.argsort(scaler.inverse_transform(km.cluster_centers_)[:, CLUSTER_FEATURE_COLS.index("avg_finish")])
    remap = {old: new for new, old in enumerate(order)}
    prof["cluster"] = [remap[c] for c in km.labels_]
    prof["cluster_name"] = prof["cluster"].map(dict(enumerate(TIER_NAMES)))

    pca = PCA(n_components=2, random_state=42).fit(X)
    prof[["pca_1", "pca_2"]] = pca.transform(X)

    centroids = pd.DataFrame(scaler.inverse_transform(km.cluster_centers_[order]), columns=CLUSTER_FEATURE_COLS)
    centroids.insert(0, "cluster_name", TIER_NAMES[:k])
    centroids.insert(0, "cluster", range(k))
    centroids["size"] = prof["cluster"].value_counts().sort_index().values

    return prof, centroids, scaler, km, remap, pca


if __name__ == "__main__":
    print("=" * 90)
    print("   PARAMETER 11: CHAMPION CLUSTERING ALGORITHM — K-MEANS (k = 3)")
    print("=" * 90)
    prof, centroids, scaler, km, remap, pca = fit_champion()

    prof.to_csv(os.path.join(BASE_DIR, "driver_season_clusters.csv"), index=False)
    centroids.round(4).to_csv(os.path.join(BASE_DIR, "cluster_profiles.csv"), index=False)
    models_dir = os.path.join(BASE_DIR, "..", "models")
    joblib.dump({"scaler": scaler, "model": km, "remap": remap, "features": CLUSTER_FEATURE_COLS,
                 "tier_names": TIER_NAMES}, os.path.join(models_dir, "champion_kmeans_clusterer.joblib"))

    print(f"[+] Inertia (WCSS): {km.inertia_:.2f} | Iterations to converge: {km.n_iter_}")
    print(f"[+] PCA 2-D explained variance: {pca.explained_variance_ratio_.sum()*100:.1f}%")
    print("\n--- CLUSTER CENTROIDS (original units) ---")
    print(centroids.round(3).to_string(index=False))

    for c, name in enumerate(TIER_NAMES):
        top = prof[prof["cluster"] == c].sort_values("win_rate", ascending=False).head(3)
        print(f"\n  {name}: e.g. " + ", ".join(f"{r.driver_name} {r.season}" for r in top.itertuples()))

    print("\n--- CASE STUDY: LEWIS HAMILTON CAREER TRAJECTORY ---")
    ham = prof[prof["driver_name"].str.contains("Hamilton", na=False)].sort_values("season")
    print("  " + " | ".join(f"{r.season}: {r.cluster_name.split()[0]}" for r in ham.itertuples()))

    print("\n[+] Saved: driver_season_clusters.csv, cluster_profiles.csv, models/champion_kmeans_clusterer.joblib")
