# 11. Clustering Algorithm (K-Means): Key Logic & Core Summary

## 1. Algorithm
**K-Means (Lloyd's algorithm)** with `k = 3`, `init = "k-means++"`, `n_init = 10`, `random_state = 42`.

1. **Initialise:** k-means++ picks spread-out starting centroids (each new centroid is chosen with probability ∝ D(x)²).
2. **Assign:** each profile goes to its nearest centroid by Euclidean distance.
3. **Update:** each centroid moves to the mean of its members.
4. **Repeat** until the assignments stop changing. It converged in **13 iterations**; the best of the 10 restarts is kept.

Objective (inertia / WCSS): $J = \sum_{j=1}^{k}\sum_{x_i \in C_j}\lVert x_i-\mu_j\rVert^2$ = **3174.81**

Complexity: O(n · k · d · iterations), with n = 703, k = 3, d = 9.

## 2. Discovered Tiers (centroids in original units)
| Cluster | Size | Avg grid | Avg finish | Win % | Podium % | Points % | DNF % | Beat teammate in quali |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 🔴 **Title Contenders** | 108 | 4.0 | 5.0 | 25.2% | 59.3% | 84.9% | 13.6% | 58.4% |
| 🟡 **Midfield Regulars** | 325 | 9.6 | 10.4 | 1.2% | 9.1% | 57.1% | 27.6% | 53.3% |
| ⚪ **Backmarkers** | 270 | 16.5 | 14.9 | 0.0% | 0.3% | 15.2% | 38.6% | 32.4% |

Cluster ids are re-ordered by centroid average finish, so that 0 = best. The names are given **after** fitting by reading the centroids; the algorithm never sees them.

**Examples:** Title Contenders: Verstappen 2023, M. Schumacher 2004, Hamilton 2020. Midfield Regulars: Montoya 2005, R. Schumacher 2001, Button 2012. Backmarkers: Fisichella 2003, C. Fittipaldi 1994, Vergne 2013.

## 3. Case Study: Lewis Hamilton's Career Trajectory
2007–08 **Contender** → 2009 **Midfield** (uncompetitive McLaren MP4-24) → 2010–2022 **Contender** (13 straight seasons) → 2023–24 **Midfield** (Mercedes ground-effect slump).
Without any labels, the clusters pick up real changes in car competitiveness.

## 4. Visualisation
A PCA projection to 2-D explains **68.4%** of the variance. The three tiers separate along PC1 (overall pace), from Backmarkers on the left to Contenders on the right. See Streamlit page 18.

## 5. Persisted Artifacts
- `11_clustering_algorithm/driver_season_clusters.csv`: every profile with its cluster, name and PCA coordinates
- `11_clustering_algorithm/cluster_profiles.csv`: the centroids
- `models/champion_kmeans_clusterer.joblib`: `{scaler, model, remap, features, tier_names}`, ready to assign new profiles

## 6. Run
```bash
python3 11_clustering_algorithm/kmeans_clustering.py
```
