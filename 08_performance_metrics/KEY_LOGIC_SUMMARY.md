# 08. Performance Metrics: Key Logic & Core Summary

## 1. Train vs. Validation vs. Test
| Partition | Seasons & entries | ROC-AUC | PR-AUC | Accuracy | Winner recall | Brier | Top-1 winner hit |
|---|---|---:|---:|---:|---:|---:|---:|
| Train | 1994–2021 (10,999 rows) | 0.9730 | 0.5990 | 91.30% | 93.52% | 0.0625 | 59.1% (301/509) |
| Validation | 2022 (440 rows, 22 GPs) | 0.9606 | 0.5997 | 89.77% | 90.91% | 0.0692 | 50.0% (11/22) |
| Test | 2023–2024 (919 rows, 46 GPs) | 0.9636 | 0.6658 | 90.53% | 82.61% | 0.0658 | 63.0% (29/46) |
| **Combined holdout** | **2022–2024 (1,359 rows, 68 GPs)** | **0.9629** | **0.6433** | **90.29%** | **85.29%** | **0.0669** | **58.8% (40/68)** |

The train→test ROC-AUC gap is only 0.01, so the model shows little overfitting.

## 2. Confusion Matrix (holdout, threshold 0.5)
| | Predicted non-winner | Predicted winner | Total |
|---|---:|---:|---:|
| **Actual non-winner** | **1,169 (TN)** | 122 (FP) | 1,291 |
| **Actual winner** | 10 (FN) | **58 (TP)** | 68 |

- **Winner recall:** 85.29% (58/68). The model catches more than 4 out of 5 real winners.
- **Winner precision:** 32.22% (58/180). Several genuine contenders cross the 0.5 threshold in each race. The race softmax then picks one of them, which gives the 58.8% top-1 hit rate.
- **F1 (winner):** 0.4677 · **Log loss:** 0.2165.
- **Top-3 winner presence:** 86.76% (59/68 GPs).

## 3. Minimal Metric Logic
```python
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, confusion_matrix
roc = roc_auc_score(y, p); pr = average_precision_score(y, p); brier = brier_score_loss(y, p)
tn, fp, fn, tp = confusion_matrix(y, (p >= 0.5).astype(int)).ravel()
top1 = df.loc[df.groupby("race_id")["p"].idxmax(), "target_is_win"].mean()
```

```bash
python3 08_performance_metrics/calculate_metrics.py   # writes classification_report.csv, confusion_matrix.csv, partition_metrics.csv
```
