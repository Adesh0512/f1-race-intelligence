# ============================================================
# FILE: 07_clustering/kmeans_tiers.py
# REAL MODULES: 11_clustering_algorithm/kmeans_clustering.py and 12_clustering_metrics/clustering_metrics.py
# WHAT IT DOES:
#   1. runs the champion, K-Means with k = 3, on the 703 standardised profiles
#   2. names the clusters by average finish: best = Title Contenders, middle = Midfield Regulars, worst = Backmarkers
#   3. checks the quality: silhouette, Davies-Bouldin, Calinski-Harabasz, stability (ARI) and the real championship
# Run driver_season_profiles.py first.
# ============================================================

import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score, adjusted_rand_score

HERE = os.path.dirname(os.path.abspath(__file__))
profiles = pd.read_csv(os.path.join(HERE, "..", "output", "driver_season_profiles.csv"))
STORE = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
FEATURES = ["avg_grid", "avg_finish", "finish_std", "win_rate", "podium_rate", "points_rate",
            "dnf_rate", "teammate_quali_rate", "starts"]
TIER_NAMES = ["Title Contenders", "Midfield Regulars", "Backmarkers"]

X = StandardScaler().fit_transform(profiles[FEATURES])

# ---- 1. K-Means: pick 3 centres, give each point to the nearest centre, move centres to the mean, repeat ----
kmeans = KMeans(n_clusters=3, init="k-means++", n_init=10, random_state=42).fit(X)
profiles["cluster"] = kmeans.labels_

# ---- 2. Name the clusters: the cluster with the best (lowest) average finish is "Title Contenders" ----
average_finish = profiles.groupby("cluster")["avg_finish"].mean().sort_values()
names = {}
for position, cluster_number in enumerate(average_finish.index):
    names[cluster_number] = TIER_NAMES[position]
profiles["tier"] = profiles["cluster"].map(names)

print(profiles.groupby("tier")[["avg_grid", "avg_finish", "win_rate", "podium_rate", "dnf_rate"]].mean().round(3))
print(profiles["tier"].value_counts().to_string())             # 108 / 325 / 270

# ---- 3. Quality checks ----
print("\nSilhouette:", round(silhouette_score(X, kmeans.labels_), 4))                  # 0.2636 (higher is better)
print("Davies-Bouldin:", round(davies_bouldin_score(X, kmeans.labels_), 4))          # 1.2759 (lower is better)
print("Calinski-Harabasz:", round(calinski_harabasz_score(X, kmeans.labels_), 1))    # 347.5 (higher is better)

# Stability: run K-Means again with 30 different random seeds; ARI = 1 means the same groups every time
scores = []
for seed in range(30):
    again = KMeans(n_clusters=3, n_init=1, random_state=seed).fit_predict(X)
    scores.append(adjusted_rand_score(kmeans.labels_, again))
print("Seed stability (mean ARI):", round(sum(scores) / len(scores), 4))             # about 0.92

# External check against the real championship (never used to make the clusters)
store = pd.read_csv(STORE, usecols=["driver_id", "season", "season_points_before"])
points = store.groupby(["driver_id", "season"])["season_points_before"].max().rename("points").reset_index()
points["standing"] = points.groupby("season")["points"].rank(ascending=False, method="min")
merged = profiles.merge(points, on=["driver_id", "season"], how="left")
contenders = merged[merged["tier"] == "Title Contenders"]
in_top_3 = (contenders["standing"] <= 3).mean() * 100
print(f"Title Contender seasons that ended in the championship top 3: {in_top_3:.1f}%")   # 80.6%
