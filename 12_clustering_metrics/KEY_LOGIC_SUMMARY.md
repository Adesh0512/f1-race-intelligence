# 12. Clustering Performance Metrics: Key Logic & Core Summary

## 1. Internal Validity (no ground truth needed)
| Metric | Value | Range | Better | Reading |
|---|---:|---|:---:|---|
| **Silhouette** | **0.2636** | −1 … 1 | ↑ | Clusters are distinct but touching. Typical of real performance data, which forms a continuum rather than separate islands |
| **Davies-Bouldin** | **1.2759** | 0 … ∞ | ↓ | Each cluster's spread is about 1.3× its distance to the nearest other cluster |
| **Calinski-Harabasz** | **347.51** | 0 … ∞ | ↑ | Between-cluster spread is much larger than within-cluster spread |
| **Inertia (WCSS)** | 3174.81 | 0 … ∞ | ↓ (fixed k) | Down 22% from k = 2 |

### Per-cluster silhouette
| Cluster | Size | Mean silhouette | Profiles with negative silhouette |
|---|---:|---:|---:|
| Title Contenders | 108 | 0.2783 | 2.78% |
| Midfield Regulars | 325 | 0.2794 | 0.00% |
| Backmarkers | 270 | 0.2388 | 4.07% |

Only 14 of 703 profiles (2%) sit closer to another cluster than to their own.

## 2. Stability
| Test | Result |
|---|---|
| **Seed stability:** ARI vs. 30 single-init runs with different seeds | mean **0.9235**, min 0.7846 |
| **Bootstrap stability:** ARI on 30 × 80% resamples | mean **0.8704** ± 0.0959 |

ARI above 0.85 means the segmentation is a property of the data, not of the random start.

## 3. External Sanity Check: Do the Clusters Match the Championship?
Championship standing (rank by points before the final round) was **never used to fit** the clusters. It is only used afterwards to check them.

| Cluster ↓ / Standing → | P1–P3 | P4–P10 | P11+ |
|---|---:|---:|---:|
| **Title Contenders** | **87** | 21 | 0 |
| **Midfield Regulars** | 6 | **200** | 119 |
| **Backmarkers** | 0 | 2 | **268** |

| Agreement metric | Value |
|---|---:|
| Adjusted Rand Index | 0.4518 |
| Normalised Mutual Information | 0.5330 |
| Homogeneity / Completeness | 0.5473 / 0.5195 |
| **Title Contenders who finished in the top 3** | **80.6%** |

- No Backmarker season ever finished in the top 3, and no Contender season finished outside the top 10.
- The ARI is moderate rather than high **by design**. The standing tiers have fixed sizes (3 / 7 / rest per season), while the clusters follow natural gaps, so 119 "P11+" midfielders fall in the Midfield cluster. That is a real finding: being a points finisher does not guarantee a top-10 championship position.

## 4. Minimal Metric Logic
```python
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score, adjusted_rand_score
sil = silhouette_score(X, labels); dbi = davies_bouldin_score(X, labels); chi = calinski_harabasz_score(X, labels)
seed_ari = [adjusted_rand_score(labels, KMeans(3, n_init=1, random_state=s).fit_predict(X)) for s in range(30)]
```

## 5. Run
```bash
python3 12_clustering_metrics/clustering_metrics.py   # writes clustering_metrics.json + 2 CSVs
```
