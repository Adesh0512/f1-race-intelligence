# Folder 06 — Champion Model (cost-sensitive XGBoost)

**Responsibility of this folder:** train the best classifier, turn its scores into race probabilities and measure it in detail.
**Real project:** `06_classification_algorithm/improved_classifier.py`, `08_performance_metrics/calculate_metrics.py`, `07_innovation/` and the dashboard page *Classification Algorithm*.

---

## File: `xgboost_champion.py`

**1. Location:** `exam_simplified/06_champion_model/xgboost_champion.py`

**2. What it does:** trains cost-sensitive XGBoost, applies the race softmax, and reports winners picked, ROC-AUC, PR-AUC, the confusion matrix and feature importance.

**3. Parameters and logic**
| Parameter | Value | Meaning |
|---|---|---|
| `n_estimators` | 100 | number of trees |
| `max_depth` | 4 | questions per tree |
| `learning_rate` | 0.05 | how much each tree corrects |
| `scale_pos_weight` | 15 | a winner counts 15× (cost-sensitive learning) |
| `subsample`, `colsample_bytree` | 0.85, 0.85 | each tree sees 85% of rows and features |
| `random_state` | 42 | same result every run |
| Softmax temperature T | 0.8 | sharpens the race distribution |

Race softmax: **P(i wins) = exp(log pᵢ / T) / Σⱼ exp(log pⱼ / T)**, so all drivers of one race add up to 100%.

Results on 2022–2024: **40 / 68 winners (58.8%)**, ROC-AUC **0.9629**, PR-AUC **0.6433**.
Confusion matrix at 0.5: TP 58, FN 10, FP 122, TN 1,169 → precision 0.322, recall 0.853.
Top features: grid_position 47.5%, driver_rolling_finish_5 10.0%.

**4. Simplified code**
```python
# ============================================================
# FILE: 06_champion_model/xgboost_champion.py
# REAL MODULES: 06_classification_algorithm/improved_classifier.py and 08_performance_metrics/calculate_metrics.py
# WHAT IT DOES:
#   1. trains the champion: cost-sensitive XGBoost (a missed winner costs 15x more than a false alarm)
#   2. turns each driver's score into a race probability with a softmax (all drivers in a race add up to 100%)
#   3. reports the confusion matrix, precision, recall and the most important features
# ============================================================

import os
import math
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score, average_precision_score, confusion_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
FEATURES = ["grid_position", "driver_rolling_finish_5", "driver_rolling_points_5", "constructor_rolling_finish_10",
            "constructor_rolling_points_10", "circuit_avg_finish", "circuit_win_rate", "circuit_podium_rate",
            "circuit_experience", "season_points_before", "career_starts", "career_win_rate", "career_dnf_rate",
            "ahead_of_teammate_grid", "driver_age", "grid_vs_form_gap"]
TEMPERATURE = 0.8      # softmax temperature used by the real project

data = pd.read_csv(DATA, low_memory=False)
train = data[data["season"] <= 2021]
test = data[data["season"] >= 2022].copy()

# ---- 1. Train the champion ----
model = xgb.XGBClassifier(
    n_estimators=100,        # 100 small trees, each one fixes the mistakes of the trees before it
    max_depth=4,             # each tree asks at most 4 questions
    learning_rate=0.05,      # each tree only corrects a little (safer)
    scale_pos_weight=15,     # cost-sensitive: a winner counts 15 times more (winners are rare, 1 in 21)
    subsample=0.85,          # each tree sees 85% of the rows ...
    colsample_bytree=0.85,   # ... and 85% of the features (less overfitting)
    random_state=42, eval_metric="logloss")
model.fit(train[FEATURES].fillna(0), train["target_is_win"])
test["score"] = model.predict_proba(test[FEATURES].fillna(0))[:, 1]

# ---- 2. Race softmax: probabilities of one race add up to exactly 100% ----
def race_softmax(scores):
    """P(i wins) = exp(log p_i / T) / sum over all drivers j of exp(log p_j / T)"""
    powered = [math.exp(math.log(max(s, 1e-7)) / TEMPERATURE) for s in scores]
    total = sum(powered)
    return [p / total for p in powered]

test["win_probability"] = 0.0
for race_id, race in test.groupby("race_id"):
    test.loc[race.index, "win_probability"] = race_softmax(list(race["score"]))

# The predicted winner of each race = the driver with the highest probability
hits = 0
for race_id, race in test.groupby("race_id"):
    if race.sort_values("win_probability", ascending=False).iloc[0]["target_is_win"] == 1:
        hits = hits + 1
races = test["race_id"].nunique()
print(f"Winner picked in {hits} of {races} races ({100 * hits / races:.1f}%)")      # 40 of 68 (58.8%)
print("ROC-AUC:", round(roc_auc_score(test["target_is_win"], test["score"]), 4))       # 0.9629
print("PR-AUC: ", round(average_precision_score(test["target_is_win"], test["score"]), 4))  # 0.6433

# ---- 3. Confusion matrix at threshold 0.5 ----
flagged = (test["score"] >= 0.5).astype(int)
tn, fp, fn, tp = confusion_matrix(test["target_is_win"], flagged).ravel()
print(f"Confusion matrix: TP={tp} FN={fn} FP={fp} TN={tn}")                             # 58, 10, 122, 1169
print(f"Precision = TP/(TP+FP) = {tp / (tp + fp):.3f}   Recall = TP/(TP+FN) = {tp / (tp + fn):.3f}")

# Feature importance: which inputs the trees used most
importance = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("\nTop 5 features:")
print((importance.head(5) * 100).round(1).to_string())                                 # grid_position about 47%

# One example race
example = test[test["race_name"].str.contains("British") & (test["season"] == 2024)]
print("\n2024 British Grand Prix, top 3 predicted:")
print(example.sort_values("win_probability", ascending=False)[["driver_name", "grid_position", "win_probability",
                                                                "target_finish_position"]].head(3).to_string(index=False))
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `xgb.XGBClassifier(n_estimators=100, ...)` | The champion model with its settings |
| `model.fit(train[FEATURES].fillna(0), train["target_is_win"])` | Learn; missing values become 0 |
| `model.predict_proba(...)[:, 1]` | Raw score of each driver |
| `def race_softmax(scores)` | Turns one race's scores into chances that add up to 1 |
| `math.exp(math.log(s) / TEMPERATURE)` | The softmax formula for one driver |
| `for race_id, race in test.groupby("race_id")` | Apply the softmax race by race |
| `race.sort_values("win_probability").iloc[0]` | The predicted winner = highest chance |
| `confusion_matrix(...).ravel()` | Counts TN, FP, FN, TP at threshold 0.5 |
| `tp / (tp + fp)`, `tp / (tp + fn)` | Precision and recall |
| `model.feature_importances_` | How much each feature helped the trees |

**6. Say this in the jury:** "XGBoost builds 100 small trees, each correcting the previous ones. Because winners are rare, a missed winner costs 15 times more. The softmax makes the chances of all drivers in a race add up to 100%, and the highest chance is our predicted winner. It is right in 40 of 68 unseen races."

**7. Viva question:** *Precision is only 0.32. Isn't that bad?*
**Answer:** At a 0.5 threshold about 2.6 real contenders per race are flagged, and only one can win, so precision is naturally low. The softmax then picks one driver per race, which is why "winners picked" (58.8%) is the measure that matters.

**Error example:** at the 2024 British GP the model ranked pole-sitter Russell first; he retired with a water-system failure and Hamilton, ranked second, won. Pre-race data cannot foresee failures.
