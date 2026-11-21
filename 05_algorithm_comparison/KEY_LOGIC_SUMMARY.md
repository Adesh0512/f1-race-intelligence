# 05. Algorithm Comparison & Validation: Key Logic & Core Summary

## 1. Experimental Protocol & Invariants
- **Universe:** 12,358 entries (577 Grands Prix, 1994–2024).
- **Chronological split:** train on 1994–2021 (10,999 rows, 509 GPs); test on the 2022–2024 ground-effect era (1,359 rows, 68 GPs).
- **Temporal invariant:** max(T_train) = 2021 < min(T_test) = 2022. No random k-fold shuffling: the model is always tested on the future.
- **One champion configuration everywhere (modules 05–08):** `XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15, subsample=0.85, colsample_bytree=0.85, random_state=42)`.

## 2. Benchmark of 7 Model Families (held-out 2022–2024)
| Model | ROC-AUC | PR-AUC | Balanced Acc | Winner Recall | Top-1 Winner Hit (68 GPs) | Top-3 Hit | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1. Dummy (uniform) | 0.5000 | 0.0500 | 49.28% | 48.5% | 33.8% (23/68) | 55.9% | 0.2500 |
| 2. Logistic Reg (grid only) | 0.9198 | 0.3994 | 50.00% | 0.0% | 51.5% (35/68) | 83.8% | 0.0345 |
| 3. Decision Tree (depth 5) | 0.9177 | 0.4715 | 84.75% | 83.8% | 52.9% (36/68) | 76.5% | 0.1005 |
| 4. Random Forest | 0.9561 | 0.5866 | 88.19% | 89.7% | 51.5% (35/68) | 86.8% | 0.0919 |
| 5. Gradient Boosting (GBDT) | 0.9622 | 0.5994 | 70.20% | 41.2% | 52.9% (36/68) | 86.8% | 0.0293 |
| 6. LightGBM | 0.9586 | 0.6152 | 86.02% | 83.8% | 51.5% (35/68) | 83.8% | 0.0811 |
| **7. XGBoost (champion)** | **0.9629** | **0.6433** | **87.92%** | **85.3%** | **58.8% (40/68)** | **86.8%** | 0.0669 |

- The grid-only baseline reaches 95% **accuracy** by predicting "no win" for everyone (recall 0). That is why accuracy is not used to rank models at 20:1 imbalance.
- Batch inference for all 1,359 holdout rows takes about 3 ms.

## 3. Validation 1: 6-Fold Expanding Window
Train on 1994 → season−1, test on that season only.

| Test season | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | **Mean** |
|---|---:|---:|---:|---:|---:|---:|---:|
| XGBoost ROC-AUC | 0.9480 | 0.9137 | 0.9336 | 0.9606 | 0.9844 | 0.9317 | **0.9453** |
| Grid-only baseline | 0.9549 | 0.9226 | 0.9213 | 0.9000 | 0.9409 | 0.9186 | 0.9264 |
| XGBoost top-1 hit | 38.1% | 47.1% | 54.5% | 50.0% | 77.3% | 50.0% | 52.8% |

## 4. Validation 2: Statistical Significance
| Test | Result | Verdict |
|---|---|---|
| **Race-level paired bootstrap** (1,000 resamples of the 68 holdout GPs) | ΔROC-AUC = **+0.0424**, 95% CI **[+0.0183, +0.0732]**, p < 0.001 | **Significant**: the CI excludes 0 |
| Wilcoxon signed-rank on the 6 folds (one-sided) | W = 18, p = 0.078 | XGBoost wins 4 of 6 folds. With only 6 pairs the smallest achievable p is 0.016, so this test has low power |

## 5. Outputs
`comparison_results.csv`, `temporal_validation_results.csv`, `significance_test.csv`. Dashboard 2 page: **Classifier Comparison & Validation**.

```bash
python3 05_algorithm_comparison/train_comparison.py
python3 05_algorithm_comparison/temporal_validation.py
```
