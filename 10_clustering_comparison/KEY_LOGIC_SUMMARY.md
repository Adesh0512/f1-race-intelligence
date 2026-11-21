# 10. Clustering Algorithm Comparison: Key Logic & Core Summary

## 1. Five Algorithms from Five Different Families
| Algorithm | Family | Core idea | Needs k? |
|---|---|---|:---:|
| **K-Means** | Centroid / partitional | Minimise within-cluster squared distance (Lloyd's algorithm, k-means++ init) | Yes |
| **Agglomerative (Ward)** | Hierarchical | Bottom-up merging; each merge adds the least variance | Yes (cut level) |
| **Gaussian Mixture (GMM)** | Probabilistic / model-based | EM fits k Gaussians; soft membership | Yes |
| **BIRCH** | Tree-based / incremental | Builds a CF-tree in one scan, then clusters the leaf summaries | Yes |
| **DBSCAN** | Density-based | Clusters = dense regions (≥ `min_samples` within `eps`); sparse points = noise | No |

## 2. Step 1: Choosing k (Elbow + Silhouette, K-Means, k = 2..8)
| k | 2 | **3** | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Inertia (WCSS) | 4074.6 | **3174.8** | 2741.7 | 2407.9 | 2151.7 | 1983.2 | 1870.3 |
| Silhouette | 0.3188 | **0.2636** | 0.2426 | 0.2344 | 0.2222 | 0.2175 | 0.2155 |

- **Elbow at k = 3**: the largest bend in the inertia curve (biggest drop 2→3, then flattening).
- k = 2 has a higher silhouette but only splits "front-runners vs. everyone else"; k = 3 adds a meaningful midfield tier.
- DBSCAN does not take k. `eps` and `min_samples` were grid-searched (eps 0.8–2.5, min_samples 5/8/10/15) requiring ≥ 3 clusters and ≤ 15% noise → **eps = 1.3, min_samples = 5**.

## 3. Step 2: Benchmark Results (703 profiles, 9 standardised features)
| Rank | Algorithm | Clusters | Noise % | Silhouette ↑ | Davies-Bouldin ↓ | Calinski-Harabasz ↑ | Stability ARI ↑ | Runtime |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|
| 🏆 1 | **K-Means** | 3 | 0.0 | **0.2636** | 1.2759 | **347.5** | 0.9447 | 13 ms |
| 2 | Agglomerative (Ward) | 3 | 0.0 | 0.1808 | 1.5146 | 280.8 | 0.5198 | 46 ms |
| 2 | BIRCH | 3 | 0.0 | 0.1951 | 1.5231 | 298.3 | 0.5017 | 49 ms |
| 4 | Gaussian Mixture | 3 | 0.0 | 0.1409 | 1.6854 | 252.7 | **0.9953** | 189 ms |
| 5 | DBSCAN | 4 | 7.7 | 0.1116 | 0.8546* | 24.0 | 0.8974 | 8 ms |

\*DBSCAN metrics exclude its 54 noise points. Its low Davies-Bouldin comes from one tiny, isolated cluster, while its Calinski-Harabasz (24) and silhouette are the worst.
Runtimes vary slightly between runs.

**Ranking rule:** the mean of the per-metric ranks across Silhouette, Davies-Bouldin, Calinski-Harabasz, Stability ARI and Noise %.
**Stability ARI:** Adjusted Rand Index between the full-data labels and labels re-fitted on 10 random 90% subsamples with new seeds.

## 4. Interpretation
- **K-Means wins** on 3 of the 5 criteria and is the fastest among the algorithms that assign every point.
- **Ward and BIRCH** produce similar partitions, but they are unstable (ARI ≈ 0.5): removing 10% of the data reshuffles the cluster boundaries.
- **GMM** is the most stable, but its full-covariance Gaussians overlap heavily, which gives the lowest silhouette among the k = 3 methods.
- **DBSCAN** struggles because the data has **varying density**: one dense midfield blob and a sparse tail of dominant seasons. A single `eps` cannot fit both, so the dominant seasons are labelled as noise.

## 5. Run
```bash
python3 10_clustering_comparison/clustering_comparison.py   # writes k_selection.csv, comparison_results.csv
```
