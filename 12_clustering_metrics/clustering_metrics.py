"""
Clustering Performance Metrics (Parameter 12)
=============================================
Evaluates the champion K-Means (k = 3) segmentation with three families of metrics:

1. Internal validity (no ground truth needed)
   - Silhouette coefficient (overall + per cluster)     range [-1, 1], higher = better
   - Davies-Bouldin index                               range [0, inf), lower = better
   - Calinski-Harabasz index                            higher = better
   - Inertia / WCSS
2. Stability
   - Seed stability: ARI between 30 random initialisations
   - Bootstrap stability: ARI on 30 x 80% resamples
3. External sanity check (labels NOT used for fitting)
   - Agreement with championship standing tier (P1–P3 / P4–P10 / P11+),
     measured with ARI, NMI, homogeneity, completeness and a contingency table.
     Standing = rank by points held before the season's final round.

Outputs:
- 12_clustering_metrics/clustering_metrics.json
- 12_clustering_metrics/per_cluster_silhouette.csv
- 12_clustering_metrics/championship_contingency.csv
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    silhouette_score, silhouette_samples, davies_bouldin_score, calinski_harabasz_score,
    adjusted_rand_score, normalized_mutual_info_score, homogeneity_score, completeness_score
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "..", "11_clustering_algorithm"))
from kmeans_clustering import fit_champion, K, TIER_NAMES, CLUSTER_FEATURE_COLS


def championship_tier(prof):
    df = pd.read_csv(os.path.join(BASE_DIR, "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"),
                     usecols=["driver_id", "season", "season_points_before"])
    pts = df.groupby(["driver_id", "season"])["season_points_before"].max().rename("pts").reset_index()
    pts["standing"] = pts.groupby("season")["pts"].rank(ascending=False, method="min")
    m = prof.merge(pts, on=["driver_id", "season"], how="left")
    return pd.cut(m["standing"], [0, 3, 10, np.inf], labels=["P1-P3", "P4-P10", "P11+"]).astype(str).values


def run_metrics(n_runs=30):
    print("=" * 90)
    print("   PARAMETER 12: CLUSTERING PERFORMANCE METRICS — K-MEANS (k = 3)")
    print("=" * 90)

    prof, centroids, scaler, km, remap, _ = fit_champion()
    X = scaler.transform(prof[CLUSTER_FEATURE_COLS])
    labels = prof["cluster"].values

    # 1. Internal validity
    sil = silhouette_score(X, labels)
    dbi = davies_bouldin_score(X, labels)
    chi = calinski_harabasz_score(X, labels)
    sil_samples = silhouette_samples(X, labels)
    per_cluster = pd.DataFrame({
        "cluster": range(K), "cluster_name": TIER_NAMES,
        "size": [int((labels == c).sum()) for c in range(K)],
        "mean_silhouette": [round(float(sil_samples[labels == c].mean()), 4) for c in range(K)],
        "negative_silhouette_pct": [round(float((sil_samples[labels == c] < 0).mean() * 100), 2) for c in range(K)],
    })

    # 2. Stability
    seed_labels = [KMeans(n_clusters=K, n_init=1, random_state=s).fit_predict(X) for s in range(n_runs)]
    seed_ari = [adjusted_rand_score(labels, l) for l in seed_labels]
    rng = np.random.default_rng(0)
    boot_ari = []
    for s in range(n_runs):
        idx = rng.choice(len(X), size=int(0.8 * len(X)), replace=False)
        boot_ari.append(adjusted_rand_score(labels[idx], KMeans(n_clusters=K, n_init=10, random_state=s).fit_predict(X[idx])))

    # 3. External sanity check
    tier = championship_tier(prof)
    ext = {
        "ari": adjusted_rand_score(tier, labels),
        "nmi": normalized_mutual_info_score(tier, labels),
        "homogeneity": homogeneity_score(tier, labels),
        "completeness": completeness_score(tier, labels),
    }
    contingency = pd.crosstab(prof["cluster_name"], tier).reindex(TIER_NAMES)[["P1-P3", "P4-P10", "P11+"]]

    metrics = {
        "algorithm": "K-Means", "k": K, "n_profiles": int(len(X)), "n_features": int(X.shape[1]),
        "silhouette": round(sil, 4), "davies_bouldin": round(dbi, 4), "calinski_harabasz": round(chi, 2),
        "inertia_wcss": round(float(km.inertia_), 2),
        "seed_stability_ari_mean": round(float(np.mean(seed_ari)), 4),
        "seed_stability_ari_min": round(float(np.min(seed_ari)), 4),
        "bootstrap_stability_ari_mean": round(float(np.mean(boot_ari)), 4),
        "bootstrap_stability_ari_std": round(float(np.std(boot_ari)), 4),
        "external_ari_vs_championship_tier": round(ext["ari"], 4),
        "external_nmi_vs_championship_tier": round(ext["nmi"], 4),
        "external_homogeneity": round(ext["homogeneity"], 4),
        "external_completeness": round(ext["completeness"], 4),
        "contenders_in_top3_standing_pct": round(float(contingency.loc[TIER_NAMES[0], "P1-P3"] / contingency.loc[TIER_NAMES[0]].sum() * 100), 2),
    }

    with open(os.path.join(BASE_DIR, "clustering_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    per_cluster.to_csv(os.path.join(BASE_DIR, "per_cluster_silhouette.csv"), index=False)
    contingency.to_csv(os.path.join(BASE_DIR, "championship_contingency.csv"))

    print("\n--- 1. INTERNAL VALIDITY ---")
    print(f"  Silhouette:         {sil:.4f}   (range -1..1, higher better)")
    print(f"  Davies-Bouldin:     {dbi:.4f}   (lower better)")
    print(f"  Calinski-Harabasz:  {chi:.2f}  (higher better)")
    print(f"  Inertia (WCSS):     {km.inertia_:.2f}")
    print(per_cluster.to_string(index=False))
    print("\n--- 2. STABILITY ---")
    print(f"  Seed ARI (30 inits):        mean {np.mean(seed_ari):.4f} | min {np.min(seed_ari):.4f}")
    print(f"  Bootstrap ARI (30 x 80%):   mean {np.mean(boot_ari):.4f} ± {np.std(boot_ari):.4f}")
    print("\n--- 3. EXTERNAL SANITY CHECK vs CHAMPIONSHIP STANDING ---")
    for k_, v in ext.items():
        print(f"  {k_:<14}: {v:.4f}")
    print(contingency.to_string())
    print(f"\n[+] {metrics['contenders_in_top3_standing_pct']}% of 'Title Contenders' finished the season in the top 3 of the standings.")
    print("[+] Saved: clustering_metrics.json, per_cluster_silhouette.csv, championship_contingency.csv")
    return metrics


if __name__ == "__main__":
    run_metrics()
