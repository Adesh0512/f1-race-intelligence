"""
Clustering Algorithm Comparison (Parameter 10)
==============================================
Benchmarks 6 clustering algorithms on 703 driver-season profiles (1994–2024):

1. K-Means              (centroid, Lloyd's algorithm, k-means++ init)
2. K-Medoids (PAM)      (medoid: every centre is a real driver-season)
3. Agglomerative (Ward) (hierarchical, minimum-variance merge)
4. Gaussian Mixture     (probabilistic, full covariance, EM)
5. BIRCH                (CF-tree, single scan, scalable)
6. DBSCAN               (density-based, no k, flags noise)

Step 1 — choose k with the Elbow (inertia) and Silhouette methods (k = 2..8);
         cross-check with GMM BIC/AIC; justify DBSCAN eps with the k-distance curve.
Step 2 — fit every algorithm at the chosen k (DBSCAN: eps from a grid search).
Step 3 — score with Silhouette (↑), Davies-Bouldin (↓), Calinski-Harabasz (↑),
         seed/bootstrap stability ARI (↑) and runtime; rank to pick the champion.

Outputs:
- 10_clustering_comparison/k_selection.csv
- 10_clustering_comparison/comparison_results.csv
- 10_clustering_comparison/gmm_bic_aic.csv
- 10_clustering_comparison/dbscan_k_distance.csv
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering, Birch, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import pairwise_distances
from sklearn.metrics import (
    silhouette_score, davies_bouldin_score, calinski_harabasz_score, adjusted_rand_score
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "..", "09_unsupervised_dataset"))
from build_unsupervised_dataset import load_profiles

K_RANGE = range(2, 9)
N_STABILITY_RUNS = 10


class KMedoids:
    """K-Medoids by alternating PAM (Voronoi iteration): each centre is an actual data point."""

    def __init__(self, n_clusters, n_init=10, max_iter=100, random_state=0):
        self.n_clusters, self.n_init, self.max_iter, self.random_state = n_clusters, n_init, max_iter, random_state

    def fit_predict(self, X):
        D = pairwise_distances(X)
        rng = np.random.default_rng(self.random_state)
        best = None
        for _ in range(self.n_init):
            medoids = rng.choice(len(X), self.n_clusters, replace=False)
            for _ in range(self.max_iter):
                labels = D[:, medoids].argmin(axis=1)
                # new medoid of each cluster = member with the smallest total distance to the other members
                new = np.array([np.flatnonzero(labels == c)[D[np.ix_(labels == c, labels == c)].sum(axis=1).argmin()]
                                for c in range(self.n_clusters)])
                if np.array_equal(np.sort(new), np.sort(medoids)):
                    break
                medoids = new
            labels = D[:, medoids].argmin(axis=1)
            cost = D[np.arange(len(X)), medoids[labels]].sum()
            if best is None or cost < best[0]:
                best = (cost, medoids, labels)
        self.cost_, self.medoid_indices_, self.labels_ = best
        return self.labels_


def make_models(k, eps=1.5, min_samples=8):
    return {
        "K-Means": lambda s: KMeans(n_clusters=k, n_init=10, random_state=s),
        "K-Medoids (PAM)": lambda s: KMedoids(n_clusters=k, n_init=10, random_state=s),
        "Agglomerative (Ward)": lambda s: AgglomerativeClustering(n_clusters=k, linkage="ward"),
        "Gaussian Mixture": lambda s: GaussianMixture(n_components=k, covariance_type="full", random_state=s),
        "BIRCH": lambda s: Birch(n_clusters=k, threshold=0.5),
        "DBSCAN": lambda s: DBSCAN(eps=eps, min_samples=min_samples),
    }


def select_k(X):
    rows = []
    for k in K_RANGE:
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        rows.append({"k": k, "inertia": round(km.inertia_, 2),
                     "silhouette": round(silhouette_score(X, km.labels_), 4)})
    ks = pd.DataFrame(rows)
    # Elbow: largest second difference of inertia; silhouette breaks ties toward a usable k >= 3
    ks["inertia_drop"] = -ks["inertia"].diff()
    ks["elbow_score"] = ks["inertia_drop"] - ks["inertia_drop"].shift(-1)
    elbow_k = int(ks.loc[ks["elbow_score"].idxmax(), "k"])
    return ks, elbow_k


def tune_dbscan(X):
    best = None
    for eps in np.arange(0.8, 2.6, 0.1):
        for ms in (5, 8, 10, 15):
            lab = DBSCAN(eps=eps, min_samples=ms).fit_predict(X)
            core = lab != -1
            n_cl = len(set(lab[core]))
            # require >= 3 clusters and <= 15% noise to be a fair, usable segmentation
            if n_cl < 3 or (~core).mean() > 0.15:
                continue
            sil = silhouette_score(X[core], lab[core])
            if best is None or sil > best[0]:
                best = (sil, round(float(eps), 2), ms)
    return (best[1], best[2]) if best else (1.5, 8)


def gmm_bic_aic(X):
    """Information criteria for Gaussian Mixture, k = 2..8: lower is better."""
    rows = []
    for k in K_RANGE:
        g = GaussianMixture(n_components=k, covariance_type="full", random_state=42).fit(X)
        rows.append({"k": k, "bic": round(g.bic(X), 1), "aic": round(g.aic(X), 1)})
    return pd.DataFrame(rows)


def dbscan_k_distance(X, min_samples):
    """Sorted distance from every point to its min_samples-th neighbour; the knee suggests eps."""
    dist, _ = NearestNeighbors(n_neighbors=min_samples).fit(X).kneighbors(X)
    return pd.DataFrame({"rank": np.arange(1, len(X) + 1), "k_distance": np.round(np.sort(dist[:, -1]), 4)})


def fit_predict(factory, seed, X):
    return factory(seed).fit_predict(X)


def stability_ari(factory, X, labels_full, runs=N_STABILITY_RUNS):
    """Mean ARI between the full-data labels and labels from 90% bootstrap resamples with new seeds."""
    rng = np.random.default_rng(0)
    scores = []
    for r in range(runs):
        idx = rng.choice(len(X), size=int(0.9 * len(X)), replace=False)
        lab = fit_predict(factory, 100 + r, X[idx])
        scores.append(adjusted_rand_score(labels_full[idx], lab))
    return float(np.mean(scores))


def run_comparison():
    print("=" * 100)
    print("   PARAMETER 10: CLUSTERING ALGORITHM COMPARISON (6 ALGORITHMS)")
    print("=" * 100)

    prof, X = load_profiles()
    print(f"[+] Loaded {len(prof):,} driver-season profiles x {X.shape[1]} standardised features.")

    ks, elbow_k = select_k(X)
    ks.to_csv(os.path.join(BASE_DIR, "k_selection.csv"), index=False)
    print("\n--- STEP 1: CHOOSING k (K-Means, k = 2..8) ---")
    print(ks[["k", "inertia", "silhouette"]].to_string(index=False))
    k = elbow_k
    print(f"[+] Elbow point: k = {k}")

    bic = gmm_bic_aic(X)
    bic.to_csv(os.path.join(BASE_DIR, "gmm_bic_aic.csv"), index=False)
    print(f"[+] GMM BIC minimum at k = {int(bic.loc[bic['bic'].idxmin(), 'k'])}, AIC minimum at k = {int(bic.loc[bic['aic'].idxmin(), 'k'])}")

    eps, ms = tune_dbscan(X)
    print(f"[+] DBSCAN tuned: eps = {eps}, min_samples = {ms}")
    kd = dbscan_k_distance(X, ms).assign(chosen_eps=eps, min_samples=ms)
    kd.to_csv(os.path.join(BASE_DIR, "dbscan_k_distance.csv"), index=False)
    print(f"[+] k-distance: {(kd['k_distance'] > eps).mean() * 100:.1f}% of points are non-core at this eps (border or noise; DBSCAN keeps border points)")

    rows = []
    print("\n--- STEP 2: FITTING ALL ALGORITHMS ---")
    print(f"{'Algorithm':<22} | {'k':>2} | {'Noise%':>6} | {'Silhouette':>10} | {'Davies-B':>8} | {'Calinski-H':>10} | {'Stability':>9} | {'Time ms':>7}")
    print("-" * 100)
    for name, factory in make_models(k, eps, ms).items():
        t0 = time.perf_counter()
        labels = fit_predict(factory, 42, X)
        ms_fit = (time.perf_counter() - t0) * 1000
        core = labels != -1
        n_cl = len(set(labels[core]))
        noise = (~core).mean() * 100
        sil = silhouette_score(X[core], labels[core])
        dbi = davies_bouldin_score(X[core], labels[core])
        chi = calinski_harabasz_score(X[core], labels[core])
        stab = stability_ari(factory, X, labels)
        print(f"{name:<22} | {n_cl:>2} | {noise:>5.1f}% | {sil:>10.4f} | {dbi:>8.4f} | {chi:>10.1f} | {stab:>9.4f} | {ms_fit:>7.1f}")
        rows.append({"algorithm": name, "n_clusters": n_cl, "noise_pct": round(noise, 2),
                     "silhouette": round(sil, 4), "davies_bouldin": round(dbi, 4),
                     "calinski_harabasz": round(chi, 1), "stability_ari": round(stab, 4),
                     "runtime_ms": round(ms_fit, 2)})

    res = pd.DataFrame(rows)
    # Rank: average of per-metric ranks (1 = best). Noise > 0 is penalised: noisy points are left unassigned.
    res["rank_score"] = (
        res["silhouette"].rank(ascending=False) + res["davies_bouldin"].rank(ascending=True)
        + res["calinski_harabasz"].rank(ascending=False) + res["stability_ari"].rank(ascending=False)
        + res["noise_pct"].rank(ascending=True)
    ) / 5
    res = res.sort_values("rank_score").reset_index(drop=True)
    res["champion"] = res.index == 0
    res.to_csv(os.path.join(BASE_DIR, "comparison_results.csv"), index=False)

    champ = res.iloc[0]
    print("-" * 100)
    print(f"\n[+] CHAMPION: {champ['algorithm']} (mean rank {champ['rank_score']:.2f}) at k = {k}")
    print(f"[+] Saved: comparison_results.csv, k_selection.csv, gmm_bic_aic.csv, dbscan_k_distance.csv")
    return res, k


if __name__ == "__main__":
    run_comparison()
