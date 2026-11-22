# Folder 05 — Classifier Comparison

**Responsibility of this folder:** train seven classification algorithms on the same data and compare them fairly on races they never saw.
**Real project:** `05_algorithm_comparison/train_comparison.py`, `temporal_validation.py` (6-fold expanding window and significance test) and the dashboard page *Classifier Comparison & Validation*.

---

## File: `compare_classifiers.py`

**1. Location:** `exam_simplified/05_classifier_comparison/compare_classifiers.py`

**2. What it does:** trains 7 models on 1994–2021, tests them on the 68 races of 2022–2024 and prints four metrics for each.

**3. Parameters and logic**
| Model | Settings | ROC-AUC | PR-AUC | Winners picked |
|---|---|---|---|---|
| Dummy | random guess | 0.5000 | 0.050 | 23 / 68 |
| Logistic regression (grid only) = **baseline** | grid slot only | 0.9198 | 0.399 | 35 / 68 |
| Decision tree | depth 5, balanced | 0.9177 | 0.472 | 36 / 68 |
| Random forest | 150 trees, depth 6, balanced | 0.9561 | 0.587 | 35 / 68 |
| Gradient boosting | 100 trees, depth 3, lr 0.05 | 0.9622 | 0.599 | 36 / 68 |
| LightGBM | 100 trees, depth 4, lr 0.05, unbalanced | 0.9586 | 0.615 | 35 / 68 |
| **XGBoost (champion)** | 100 trees, depth 4, lr 0.05, scale_pos_weight 15 | **0.9629** | **0.643** | **40 / 68** |

Metrics:
- **ROC-AUC:** the chance that a random winner is ranked above a random non-winner.
- **PR-AUC:** precision–recall area; better under imbalance (chance level = 0.05).
- **Recall:** of the real winners, how many were flagged.
- **Winners picked:** races where the top-ranked driver actually won.

**4. Simplified code**
```python
# ============================================================
# FILE: 05_classifier_comparison/compare_classifiers.py
# REAL MODULE: 05_algorithm_comparison/train_comparison.py
# WHAT IT DOES: trains 7 classifiers on 1994-2021 and tests them on 2022-2024 (68 races they never saw).
# It scores each one on ROC-AUC, PR-AUC, recall and "winner picked" (did the top-ranked driver win?).
# ============================================================

import os
import warnings
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, recall_score

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
FEATURES = ["grid_position", "driver_rolling_finish_5", "driver_rolling_points_5", "constructor_rolling_finish_10",
            "constructor_rolling_points_10", "circuit_avg_finish", "circuit_win_rate", "circuit_podium_rate",
            "circuit_experience", "season_points_before", "career_starts", "career_win_rate", "career_dnf_rate",
            "ahead_of_teammate_grid", "driver_age", "grid_vs_form_gap"]

data = pd.read_csv(DATA, low_memory=False)
train = data[data["season"] <= 2021]          # learn from the past
test = data[data["season"] >= 2022]           # test on the future (68 races)
X_train, y_train = train[FEATURES].fillna(0), train["target_is_win"]
X_test, y_test = test[FEATURES].fillna(0), test["target_is_win"]

# The 7 models with the same settings as the real project
MODELS = {
    "Dummy (random guess)": DummyClassifier(strategy="uniform", random_state=42),
    "Baseline: logistic regression on grid only": LogisticRegression(random_state=42, max_iter=300),
    "Decision tree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=42),
    "Random forest": RandomForestClassifier(n_estimators=150, max_depth=6, class_weight="balanced", random_state=42),
    "Gradient boosting": GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42),
    "LightGBM": lgb.LGBMClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, is_unbalance=True,
                                   random_state=42, verbose=-1),
    "XGBoost (champion)": xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15,
                                            subsample=0.85, colsample_bytree=0.85, random_state=42, eval_metric="logloss"),
}


def winners_picked(test_rows, probabilities):
    """In how many races did the driver with the highest probability actually win?"""
    rows = test_rows.assign(prob=probabilities)
    hits = 0
    for race_id, race in rows.groupby("race_id"):
        favourite = race.sort_values("prob", ascending=False).iloc[0]   # the model's pick
        if favourite["target_is_win"] == 1:
            hits = hits + 1
    return hits


results = []
for name, model in MODELS.items():
    # the baseline only gets the grid slot; every other model gets all 16 features
    columns = ["grid_position"] if name.startswith("Baseline") else FEATURES
    model.fit(X_train[columns], y_train)
    probabilities = model.predict_proba(X_test[columns])[:, 1]        # chance of winning for each driver
    predictions = model.predict(X_test[columns])                       # 1 = "winner", 0 = "not winner"
    results.append({
        "model": name,
        "ROC-AUC": round(roc_auc_score(y_test, probabilities), 4),
        "PR-AUC": round(average_precision_score(y_test, probabilities), 4),
        "recall": round(recall_score(y_test, predictions), 3),
        "winners picked (of 68)": winners_picked(test, probabilities),
    })

table = pd.DataFrame(results)
print(table.to_string(index=False))
# Real project: XGBoost ROC-AUC 0.9629, PR-AUC 0.6433, 40 of 68 winners; the grid-only baseline picks 35 of 68
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `train = data[data["season"] <= 2021]`, `test = ...>= 2022` | Time split |
| `MODELS = {...}` | The 7 models with the real project's settings |
| `def winners_picked(...)` | For each race, take the driver with the highest probability and check if he won |
| `columns = ["grid_position"] if name.startswith("Baseline") else FEATURES` | The baseline sees only the grid slot: it is the "back the pole-sitter" rule |
| `model.fit(X_train[columns], y_train)` | Learn from the training races |
| `model.predict_proba(...)[:, 1]` | Each driver's chance of winning |
| `roc_auc_score`, `average_precision_score`, `recall_score` | The metrics |

**6. Say this in the jury:** "We compared seven algorithms on the same 16 features and the same unseen seasons. Accuracy is misleading here, so we ranked them on ROC-AUC, PR-AUC and winners picked. XGBoost was best on all three, picking 40 of 68 winners against 35 for the pole-sitter rule."

**7. Viva question:** *The baseline has 95% accuracy. Why is it the worst useful model?*
**Answer:** It never predicts "winner" at the 0.5 threshold, so its recall is 0. It is accurate only because 95% of entries are non-winners.

**Also in the real project:** a 6-fold expanding-window validation (train 1994 → season−1, test the next season, 2019–2024), where XGBoost beats the baseline in 4 of 6 seasons. A race-level bootstrap (1,000 resamples) gives ROC-AUC +0.042, 95% CI [+0.018, +0.073], p < 0.001.
