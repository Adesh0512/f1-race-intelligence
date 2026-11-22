# ============================================================
# FILE: 03_supervised_dataset/class_labels.py
# REAL MODULE: 03_class_labels/label_generation.py
# WHAT IT DOES: explains and checks the CLASS LABELS (the answers the model learns from)
#   target_is_win    = 1 if finish position == 1     (the main label)
#   target_is_podium = 1 if finish position <= 3
#   target_is_points = 1 if finish position <= 10
#   target_is_dnf    = 1 if the driver retired (did not finish)
# ============================================================

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")

data = pd.read_csv(DATA, low_memory=False)
print("Entries (one driver in one race):", len(data))            # 12,358
print("Grands Prix:", data["race_id"].nunique())                 # 577
print("Seasons:", data["season"].min(), "to", data["season"].max())  # 1994 to 2024

# Check 1: no label is missing
labels = ["target_is_win", "target_is_podium", "target_is_points", "target_is_dnf"]
for label in labels:
    missing = data[label].isna().sum()
    print(f"{label:<18} missing values = {missing}")
    assert missing == 0

# Check 2: every race has exactly ONE winner
winners_per_race = data.groupby("race_id")["target_is_win"].sum()
assert (winners_per_race == 1).all()
print("Every race has exactly 1 winner: OK")

# Class imbalance: how many non-winners for every winner?
winners = (data["target_is_win"] == 1).sum()
non_winners = (data["target_is_win"] == 0).sum()
print("Winners:", winners, " Non-winners:", non_winners)
print("Imbalance = %.2f : 1" % (non_winners / winners))          # 20.42 : 1
print("Winners are only %.2f%% of all entries" % (100 * winners / len(data)))
