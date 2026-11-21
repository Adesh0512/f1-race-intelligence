"""
Clustering Algorithm Comparison (Parameter 10)
==============================================
Benchmarks 5 clustering algorithms on 703 driver-season profiles (1994–2024):

1. K-Means              (centroid, Lloyd's algorithm, k-means++ init)
2. Agglomerative (Ward) (hierarchical, minimum-variance merge)
3. Gaussian Mixture     (probabilistic, full covariance, EM)
4. BIRCH                (CF-tree, single scan, scalable)
5. DBSCAN               (density-based, no k, flags noise)

Step 1 — choose k with the Elbow (inertia) and Silhouette methods (k = 2..8).
Step 2 — fit every algorithm at the chosen k (DBSCAN: eps from a grid search).
Step 3 — score with Silhouette (↑), Davies-Bouldin (↓), Calinski-Harabasz (↑),
         seed/bootstrap stability ARI (↑) and runtime; rank to pick the champion.

Outputs:
- 10_clustering_comparison/k_selection.csv
- 10_clustering_comparison/comparison_results.csv
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering, Birch, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    silhouette_score, davies_bouldin_score, calinski_harabasz_score, adjusted_rand_score
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "..", "09_unsupervised_dataset"))
from build_unsupervised_dataset import load_profiles

K_RANGE = range(2, 9)
N_STABILITY_RUNS = 10


def make_models(k, eps=1.5, min_samples=8):
    return {
        "K-Means": lambda s: KMeans(n_clusters=k, n_init=10, random_state=s),
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
    print("   PARAMETER 10: CLUSTERING ALGORITHM COMPARISON (5 ALGORITHMS)")
    print("=" * 100)

    prof, X = load_profiles()
    print(f"[+] Loaded {len(prof):,} driver-season profiles x {X.shape[1]} standardised features.")

    ks, elbow_k = select_k(X)
    ks.to_csv(os.path.join(BASE_DIR, "k_selection.csv"), index=False)
    print("\n--- STEP 1: CHOOSING k (K-Means, k = 2..8) ---")
    print(ks[["k", "inertia", "silhouette"]].to_string(index=False))
    k = elbow_k
    print(f"[+] Elbow point: k = {k}")

    eps, ms = tune_dbscan(X)
    print(f"[+] DBSCAN tuned: eps = {eps}, min_samples = {ms}")

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
    print(f"[+] Saved: comparison_results.csv, k_selection.csv")
    return res, k


if __name__ == "__main__":
    run_comparison()
