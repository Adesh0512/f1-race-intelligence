# Folder 03 — Supervised Dataset (labels, features, split)

**Responsibility of this folder:** prepare the data the classifiers learn from: the class labels (answers), the 16 pre-race features (inputs) and the time-based split.
**Real project:** `03_class_labels/`, `06_classification_algorithm/feature_engineering.py`, `07_innovation/` and the data file `data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv`.

---

## File 1: `class_labels.py`

**1. Location:** `exam_simplified/03_supervised_dataset/class_labels.py` (real: `03_class_labels/label_generation.py`)

**2. What it does:** explains the four class labels and checks them: none missing, exactly one winner per race, and the class imbalance.

**3. Parameters and logic**
| Label | Rule | Count |
|---|---|---|
| `target_is_win` (main) | finish position = 1 | 577 of 12,358 |
| `target_is_podium` | finish ≤ 3 | 1,731 |
| `target_is_points` | finish ≤ 10 | 5,770 |
| `target_is_dnf` | did not finish | 3,467 |

Dataset: 12,358 entries, 577 Grands Prix, 1994–2024. Imbalance: **20.42 : 1** (winners are 4.67%).

**4. Simplified code**
```python
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
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `data = pd.read_csv(DATA)` | Load the feature store |
| `data[label].isna().sum()` | Count empty values in a label column; must be 0 |
| `data.groupby("race_id")["target_is_win"].sum()` | Count winners in each race; must be exactly 1 |
| `non_winners / winners` | 11,781 / 577 = 20.42: the imbalance ratio |

**6. Say this in the jury:** "Our main label is target_is_win: 1 for the winner, 0 for everyone else. Every race has exactly one winner, and only about one entry in 21 is a winner, so the data is heavily imbalanced."

**7. Viva question:** *Why is imbalance a problem?*
**Answer:** A model that always says "not a winner" is 95% accurate but finds no winner. So we use cost-sensitive learning and judge models by PR-AUC, recall and winners picked, not by accuracy.

---

## File 2: `features_and_split.py`

**1. Location:** `exam_simplified/03_supervised_dataset/features_and_split.py`

**2. What it does:** lists the 16 pre-race features, shows how a rolling feature is built without leakage, and makes the chronological split.

**3. Parameters and logic**
| Group | Features |
|---|---|
| Qualifying | grid_position, ahead_of_teammate_grid, grid_vs_form_gap |
| Driver form | driver_rolling_finish_5, driver_rolling_points_5, season_points_before |
| Team form | constructor_rolling_finish_10, constructor_rolling_points_10 |
| Circuit history | circuit_avg_finish, circuit_win_rate, circuit_podium_rate, circuit_experience |
| Career | career_starts, career_win_rate, career_dnf_rate, driver_age |

Split: train 1994–2021 (509 races), validate 2022 (22), test 2023–2024 (46). Formula: `grid_vs_form_gap = grid_position − driver_rolling_finish_5`.

**4. Simplified code**
```python
# ============================================================
# FILE: 03_supervised_dataset/features_and_split.py
# REAL MODULES: 06_classification_algorithm/feature_engineering.py (the 16 features)
#               07_innovation/innovation_implementation.py (rolling form) and the chronological split
# WHAT IT DOES:
#   1. lists the 16 PRE-RACE features (things known before the race starts)
#   2. shows how one feature is built WITHOUT looking into the future (shift by one race)
#   3. splits the data by time: train 1994-2021, validate 2022, test 2023-2024
# ============================================================

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
data = pd.read_csv(DATA, low_memory=False)

# The 16 features, in 5 groups
FEATURES = {
    "Qualifying":      ["grid_position", "ahead_of_teammate_grid", "grid_vs_form_gap"],
    "Driver form":     ["driver_rolling_finish_5", "driver_rolling_points_5", "season_points_before"],
    "Team form":       ["constructor_rolling_finish_10", "constructor_rolling_points_10"],
    "Circuit history": ["circuit_avg_finish", "circuit_win_rate", "circuit_podium_rate", "circuit_experience"],
    "Career":          ["career_starts", "career_win_rate", "career_dnf_rate", "driver_age"],
}
total = 0
for group, names in FEATURES.items():
    print(f"{group:<16}: {', '.join(names)}")
    total = total + len(names)
print("Total features:", total)                                   # 16

# ---- How a rolling feature is made without leakage (example: one driver) ----
# "Average finish in the last 5 races" must use ONLY races BEFORE today's race.
# shift(1) moves every value down by one row, so today's own result is never included.
hamilton = data[data["driver_name"] == "Lewis Hamilton"].sort_values("race_date").head(8)
finishes = hamilton["target_finish_position"]
hamilton = hamilton.assign(rebuilt_form=finishes.shift(1).rolling(5, min_periods=1).mean())
print("\nLewis Hamilton's first races: his finish, and his form going INTO each race")
print(hamilton[["race_date", "target_finish_position", "rebuilt_form"]].to_string(index=False))

# grid_vs_form_gap = grid slot minus recent form (negative = starting better than his form suggests)
print("\ngrid_vs_form_gap formula check:",
      ((data["grid_position"] - data["driver_rolling_finish_5"]) - data["grid_vs_form_gap"]).abs().max() < 0.01)

# ---- Chronological split: never train on the future ----
train = data[data["season"] <= 2021]
validate = data[data["season"] == 2022]
test = data[data["season"] >= 2023]
print("\nTrain 1994-2021:", train["race_id"].nunique(), "races")     # 509
print("Validate 2022:  ", validate["race_id"].nunique(), "races")     # 22
print("Test 2023-2024: ", test["race_id"].nunique(), "races")         # 46
assert train["season"].max() < test["season"].min()                    # the test races are always later
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `FEATURES = {...}` | The 16 features in 5 groups |
| `finishes.shift(1)` | Move every result down one race, so a race never sees its own result |
| `.rolling(5, min_periods=1).mean()` | Average of the previous (up to) 5 finishes = recent form |
| `data["season"] <= 2021` / `== 2022` / `>= 2023` | Train on the past, validate and test on later seasons |
| `assert train["season"].max() < test["season"].min()` | Proof that no test race is older than a training race |

**6. Say this in the jury:** "Every feature is something you know before the lights go out: grid slot, recent form, team form, history at the track and career record. We shift by one race so the model never sees the result it is predicting, and we test only on later seasons."

**7. Viva question:** *Why not use a random train/test split?*
**Answer:** A random split would let the model learn from 2024 races and then predict 2019 races: that is learning from the future (leakage). A time split matches real use: we always predict races that have not happened yet.
