# ============================================================
# FILE: 07_clustering/compare_clustering.py
# REAL MODULE: 10_clustering_comparison/clustering_comparison.py
# WHAT IT DOES: runs 6 clustering algorithms on the same 703 standardised profiles and compares them:
#   K-Means, K-Medoids (PAM), Agglomerative (Ward), Gaussian Mixture, BIRCH and DBSCAN.
#   It also shows how k = 3 was chosen (elbow of the inertia curve).
# Run driver_season_profiles.py first.
# ============================================================

import os
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering, Birch, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score, pairwise_distances

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
profiles = pd.read_csv(os.path.join(HERE, "..", "output", "driver_season_profiles.csv"))
FEATURES = ["avg_grid", "avg_finish", "finish_std", "win_rate", "podium_rate", "points_rate",
            "dnf_rate", "teammate_quali_rate", "starts"]

# Standardise: every feature gets mean 0 and spread 1, so "starts" (about 17) does not outweigh "win_rate" (about 0.04)
X = StandardScaler().fit_transform(profiles[FEATURES])

# ---- Choosing k with the elbow method ----
print("k   inertia   silhouette")
for k in range(2, 9):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    print(k, " ", round(km.inertia_, 1), " ", round(silhouette_score(X, km.labels_), 4))
K = 3   # the biggest drop in inertia ends at k = 3 (the "elbow")


def k_medoids(X, k, tries=10, seed=0):
    """Simplified K-Medoids (PAM, alternating): every centre must be a real driver-season."""
    distance = pairwise_distances(X)
    random = np.random.default_rng(seed)
    best_cost, best_labels = None, None
    for _ in range(tries):
        medoids = random.choice(len(X), k, replace=False)        # start with k random real points
        for _ in range(100):
            labels = distance[:, medoids].argmin(axis=1)          # each point joins its nearest medoid
            new_medoids = []
            for c in range(k):
                members = np.flatnonzero(labels == c)
                # new centre = the member with the smallest total distance to the other members
                totals = distance[np.ix_(members, members)].sum(axis=1)
                new_medoids.append(members[totals.argmin()])
            if sorted(new_medoids) == sorted(medoids):
                break                                             # nothing changed: done
            medoids = np.array(new_medoids)
        labels = distance[:, medoids].argmin(axis=1)
        cost = distance[np.arange(len(X)), medoids[labels]].sum()
        if best_cost is None or cost < best_cost:
            best_cost, best_labels = cost, labels
    return best_labels


all_labels = {
    "K-Means": KMeans(n_clusters=K, n_init=10, random_state=42).fit_predict(X),
    "K-Medoids (PAM)": k_medoids(X, K),
    "Agglomerative (Ward)": AgglomerativeClustering(n_clusters=K, linkage="ward").fit_predict(X),
    "Gaussian Mixture": GaussianMixture(n_components=K, covariance_type="full", random_state=42).fit_predict(X),
    "BIRCH": Birch(n_clusters=K, threshold=0.5).fit_predict(X),
    "DBSCAN": DBSCAN(eps=1.3, min_samples=5).fit_predict(X),   # finds its own number of clusters; -1 = noise
}

rows = []
for name, labels in all_labels.items():
    keep = labels != -1                                         # DBSCAN noise points are left out of the scores
    rows.append({"algorithm": name,
                 "clusters": len(set(labels[keep])),
                 "noise %": round(100 * (~keep).mean(), 1),
                 "silhouette (higher better)": round(silhouette_score(X[keep], labels[keep]), 4),
                 "Davies-Bouldin (lower better)": round(davies_bouldin_score(X[keep], labels[keep]), 4),
                 "Calinski-Harabasz (higher better)": round(calinski_harabasz_score(X[keep], labels[keep]), 1)})
print()
print(pd.DataFrame(rows).to_string(index=False))
# Real project: K-Means wins with silhouette 0.2636, Calinski-Harabasz 347.5 and high stability
