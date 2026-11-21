# 06. Classification Algorithm: Key Logic & Core Summary

## 1. Champion: Cost-Sensitive XGBoost
- **Hyperparameters:** `n_estimators=100`, `max_depth=4`, `learning_rate=0.05`, `subsample=0.85`, `colsample_bytree=0.85`, `random_state=42`.
- **Cost-sensitive loss:** `scale_pos_weight=15`. With a 20.4:1 class imbalance, a missed winner costs 15× more than a false alarm:
$$\mathcal{L}(\theta) = -\sum_{i=1}^N \left[ 15 \cdot y_i \log \hat{p}_i + (1 - y_i) \log(1 - \hat{p}_i) \right] + \Omega(\text{trees})$$

## 2. Race-Level Softmax
Independent per-driver probabilities do not sum to 1 within a race. A temperature-scaled softmax over log-probabilities makes them mutually exclusive:
$$P(\text{Win}_i \mid \text{Race } j) = \frac{\exp(\log \hat{p}_i / T)}{\sum_{k \in \text{Race } j} \exp(\log \hat{p}_k / T)}, \quad T = 0.8$$
- The probabilities in every Grand Prix sum to exactly 1.
- Predicted winner = argmax over the grid. T < 1 sharpens the distribution toward the favourite.

## 3. Holdout Results (2022–2024, 68 GPs)
| ROC-AUC | PR-AUC | Winner recall | Winner precision | Top-1 winner hit | Brier |
|---:|---:|---:|---:|---:|---:|
| **0.9629** | **0.6433** | **85.3%** (58/68) | 32.2% | **58.8% (40/68)** | 0.0669 |

**Top features (gain):** `grid_position` 47.5%, `driver_rolling_finish_5` 10.0%, `career_win_rate` 4.7%, `constructor_rolling_points_10` 4.0%, `grid_vs_form_gap` 3.9%.

## 4. Persisted Artifacts
- `models/champion_xgboost_classifier.joblib`
- `06_classification_algorithm/holdout_predictions.csv`: every holdout entry with its raw and race-normalised probability (drives the ROC/PR curves, threshold tuner and race explorer)
- `06_classification_algorithm/feature_importance.csv`

```bash
python3 06_classification_algorithm/improved_classifier.py
```
