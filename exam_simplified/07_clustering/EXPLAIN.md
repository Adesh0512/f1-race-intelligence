# Folder 07 — Clustering (unsupervised learning)

**Responsibility of this folder:** without any label, group driver seasons into performance tiers and check that the tiers are meaningful.
**Real project:** `09_unsupervised_dataset/`, `10_clustering_comparison/`, `11_clustering_algorithm/`, `12_clustering_metrics/` and the Dashboard 3 pages.

---

## File 1: `driver_season_profiles.py`

**1. Location:** `exam_simplified/07_clustering/driver_season_profiles.py` (real: `09_unsupervised_dataset/build_unsupervised_dataset.py`)

**2. What it does:** changes the grain to **one driver in one season** and builds 9 summary features. It keeps drivers with at least 5 starts.

**3. Parameters:** `MIN_STARTS = 5`. Result: 703 profiles, 153 drivers, 1994–2024, 9 features, no label.
Features: avg_grid, avg_finish, finish_std, win_rate, podium_rate, points_rate, dnf_rate, teammate_quali_rate, starts.

**4. Simplified code**
```python
# ============================================================
# FILE: 07_clustering/driver_season_profiles.py
# REAL MODULE: 09_unsupervised_dataset/build_unsupervised_dataset.py
# WHAT IT DOES: builds the dataset for clustering. It changes the grain from
#   "one driver in one race" to "one driver in one SEASON" and keeps drivers with at least 5 starts.
#   Result: 703 driver-season profiles, 9 features, NO label column (unsupervised learning).
# ============================================================

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
OUTPUT = os.path.join(HERE, "..", "output", "driver_season_profiles.csv")
MIN_STARTS = 5

data = pd.read_csv(DATA, low_memory=False)

# Group all races of one driver in one season and summarise them
groups = data.groupby(["driver_id", "season"])
profiles = groups.agg(
    driver_name=("driver_name", "first"),
    constructor_name=("constructor_name", lambda teams: teams.mode().iat[0]),   # main team that season
    starts=("race_id", "nunique"),                       # races started
    avg_grid=("grid_position", "mean"),                  # qualifying pace
    avg_finish=("target_finish_position", "mean"),       # race pace
    finish_std=("target_finish_position", "std"),        # consistency (spread of finishes)
    win_rate=("target_is_win", "mean"),                  # wins / starts
    podium_rate=("target_is_podium", "mean"),            # podiums / starts
    points_rate=("target_is_points", "mean"),            # points finishes / starts
    dnf_rate=("target_is_dnf", "mean"),                  # retirements / starts
    teammate_quali_rate=("ahead_of_teammate_grid", "mean"),  # how often he out-qualified his teammate
).reset_index()

profiles = profiles[profiles["starts"] >= MIN_STARTS]           # drop drivers with fewer than 5 races
profiles["finish_std"] = profiles["finish_std"].fillna(0)

print("Driver-season profiles:", len(profiles))                 # 703
print("Different drivers:", profiles["driver_id"].nunique())   # 153
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
profiles.to_csv(OUTPUT, index=False)
print(profiles[profiles["season"] == 2024].sort_values("win_rate", ascending=False).head(5)[
    ["driver_name", "season", "avg_finish", "win_rate"]].to_string(index=False))
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `data.groupby(["driver_id", "season"])` | Put all races of one driver in one season together |
| `starts=("race_id", "nunique")` | Count his races |
| `avg_finish=("target_finish_position", "mean")` | His average finish that season |
| `finish_std=(..., "std")` | How much his results varied (consistency) |
| `win_rate=("target_is_win", "mean")` | Wins ÷ starts (the mean of a 0/1 column is a rate) |
| `profiles[profiles["starts"] >= MIN_STARTS]` | Drop seasons with fewer than 5 races |

**6. Say this in the jury:** "For clustering we needed objects to group, so we summarised each driver's whole season into 9 numbers. There is no label; the algorithm must find the groups itself."

**7. Viva question:** *Using win rate as a feature: isn't that leakage?*
**Answer:** No. Clustering describes seasons that already happened; it predicts nothing, so there is no future to leak.

---

## File 2: `compare_clustering.py`

**1. Location:** `exam_simplified/07_clustering/compare_clustering.py` (real: `10_clustering_comparison/clustering_comparison.py`)

**2. What it does:** standardises the 9 features, chooses k with the elbow method, then runs 6 algorithms and compares them.

**3. Parameters and logic**
| Algorithm | Family | Settings | Silhouette | Davies-Bouldin | Calinski-Harabasz |
|---|---|---|---|---|---|
| **K-Means** | centroid | k=3, n_init 10, seed 42 | **0.264** | 1.276 | **347.5** |
| K-Medoids (PAM) | medoid | k=3, 10 starts | 0.234 | 1.393 | 329.1 |
| Agglomerative (Ward) | hierarchical | k=3 | 0.181 | 1.515 | 280.8 |
| Gaussian Mixture | probabilistic | k=3, full covariance | 0.141 | 1.685 | 252.7 |
| BIRCH | tree | k=3, threshold 0.5 | about 0.195 | about 1.5 | about 295 |
| DBSCAN | density | eps 1.3, min 5 | 0.112 (7.7% noise) | 0.855 | 24.0 |

**4. Simplified code**
```python
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
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `StandardScaler().fit_transform(...)` | Mean 0, spread 1 for each feature, so no feature dominates the distance |
| `for k in range(2, 9): KMeans(...)` | Try k = 2 to 8 and print inertia (total spread inside clusters) |
| `K = 3` | The elbow: after k = 3 the drop in inertia slows down |
| `def k_medoids(...)` | Like K-Means, but every centre must be a real driver-season |
| `DBSCAN(eps=1.3, min_samples=5)` | Finds dense areas by itself; label −1 = noise |
| `silhouette_score`, `davies_bouldin_score`, `calinski_harabasz_score` | The three quality scores |

**6. Say this in the jury:** "We compared six different families of clustering. K-Means had the best silhouette and Calinski-Harabasz and was stable, so it is our champion."

**7. Viva question:** *DBSCAN has the best Davies-Bouldin. Why not choose it?*
**Answer:** It labels 7.7% of seasons as noise and does not cluster them, and it struggles when groups have different densities. We need every driver-season in a tier.

---

## File 3: `kmeans_tiers.py`

**1. Location:** `exam_simplified/07_clustering/kmeans_tiers.py` (real: `11_clustering_algorithm/kmeans_clustering.py` and `12_clustering_metrics/clustering_metrics.py`)

**2. What it does:** runs K-Means (k = 3), names the tiers, and checks their quality, stability and agreement with the real championship.

**3. Parameters and results**
| Tier | Seasons | Avg grid | Avg finish | Win rate |
|---|---|---|---|---|
| Title Contenders | 108 | 4.0 | 5.0 | 25.2% |
| Midfield Regulars | 325 | 9.6 | 10.4 | 1.2% |
| Backmarkers | 270 | 16.5 | 14.9 | 0.0% |

Silhouette 0.2636 · Davies-Bouldin 1.2759 · Calinski-Harabasz 347.5 · seed stability ARI about 0.92 (30 reruns) · **80.6% of Title Contender seasons finished in the championship top 3**, and no Backmarker season did.

**K-Means objective:** J = Σ over clusters Σ over points ‖x − centre‖² (make clusters as tight as possible).
**Silhouette:** s(i) = (b − a) / max(a, b), where a = mean distance to the own cluster and b = to the nearest other cluster.

**4. Simplified code**
```python
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
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `KMeans(n_clusters=3, init="k-means++", n_init=10, random_state=42)` | 3 groups; 10 restarts with spread-out starting centres, keep the best |
| `profiles.groupby("cluster")["avg_finish"].mean().sort_values()` | Rank clusters by average finish |
| `names[cluster_number] = TIER_NAMES[position]` | Best = Title Contenders, then Midfield, then Backmarkers |
| `adjusted_rand_score(kmeans.labels_, again)` | Same groups with another seed? 1 = identical |
| `points.groupby("season")["points"].rank(...)` | The real championship position of each driver |
| `(contenders["standing"] <= 3).mean()` | Share of Contenders who finished top 3 |

**6. Say this in the jury:** "K-Means found three tiers by itself. We never showed it the championship, yet 81% of the Title Contender seasons really finished in the top three. That shows the clusters are meaningful."

**7. Viva question:** *Silhouette 0.26 looks low. Why is it acceptable?*
**Answer:** Driver performance is a continuum, not separate islands, so neighbouring tiers touch. Only 2% of points have a negative silhouette, the result is stable (ARI 0.92), and the external check against the championship is strong.
