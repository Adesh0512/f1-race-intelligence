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
