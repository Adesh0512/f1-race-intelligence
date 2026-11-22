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
