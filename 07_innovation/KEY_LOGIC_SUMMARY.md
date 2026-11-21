# 07. Innovation Added: Key Logic & Core Summary

## 1. Innovations over a Grid-Only Baseline
1. **Multi-horizon rolling form:** driver 5-race and constructor 10-entry rolling finish and points. Computed with `shift(1)`, so the current race is never included.
2. **Circuit affinity:** the driver's historical win rate, podium rate, average finish and experience at that exact track.
3. **Intra-team qualifying delta:** `ahead_of_teammate_grid` separates driver pace from car pace.
4. **Cost-sensitive boosting + race softmax:** handles the 20:1 imbalance and enforces exactly one winner per race.

## 2. Measured Impact (2022–2024 holdout, 68 GPs)
| Metric | Baseline (grid only, logistic) | Innovation pipeline | Δ |
|---|---:|---:|---:|
| ROC-AUC | 0.9198 | **0.9629** | **+0.0431** |
| PR-AUC | 0.3994 | **0.6433** | **+0.2439** |
| Winner recall | 0.0% | **85.3%** | +85.3 pts |
| Winner F1 | 0.000 | **0.468** | +0.468 |
| Top-1 race winner hit | 51.5% (35/68) | **58.8% (40/68)** | **+5 GPs** |
| Top-3 winner presence | 83.8% | **86.8%** | +2 GPs |
| Probabilities sum to 1 per race | No | **Yes** | — |

The ROC-AUC gain is statistically significant: race-level bootstrap 95% CI [+0.018, +0.073] (module 05).

## 3. Dashboard 2 ↔ 3 Bridge: Are Cluster Tiers a Useful Feature?
`12_clustering_metrics/cluster_feature_experiment.py` adds each driver's **previous-season** K-Means tier. To stay leakage-safe, K-Means is fitted on 1994–2021 only.

| Model | ROC-AUC | PR-AUC | Top-1 hit |
|---|---:|---:|---:|
| Grid only (XGBoost) | 0.9206 | 0.3994 | 51.5% |
| Grid + previous-season tier | 0.9448 | 0.4926 | 51.5% |
| 16 features (champion) | **0.9629** | **0.6433** | **58.8%** |
| 16 features + tier | 0.9638 | 0.6138 | 55.9% |

The tier carries real signal on its own (+0.09 PR-AUC over grid alone) but is redundant once the rolling-form features are present, so the champion leaves it out.

```bash
python3 07_innovation/baseline_vs_improved.py
```
