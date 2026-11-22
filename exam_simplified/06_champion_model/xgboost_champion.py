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
