# ============================================================
# FILE: 07_clustering/driver_season_profiles.py
# REAL MODULE: 09_unsupervised_dataset/build_unsupervised_dataset.py
# WHAT IT DOES: builds the dataset for clustering. It changes the grain from
#   "one driver in one race" to "one driver in one SEASON" and keeps drivers with at least 5 starts.
#   Result: 703 driver-season profiles, 9 features, NO label column (unsupervised learning).
# ============================================================

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
OUTPUT = os.path.join(HERE, "..", "output", "driver_season_profiles.csv")
MIN_STARTS = 5

data = pd.read_csv(DATA, low_memory=False)

# Group all races of one driver in one season and summarise them
groups = data.groupby(["driver_id", "season"])
profiles = groups.agg(
    driver_name=("driver_name", "first"),
    constructor_name=("constructor_name", lambda teams: teams.mode().iat[0]),   # main team that season
    starts=("race_id", "nunique"),                       # races started
    avg_grid=("grid_position", "mean"),                  # qualifying pace
    avg_finish=("target_finish_position", "mean"),       # race pace
    finish_std=("target_finish_position", "std"),        # consistency (spread of finishes)
    win_rate=("target_is_win", "mean"),                  # wins / starts
    podium_rate=("target_is_podium", "mean"),            # podiums / starts
    points_rate=("target_is_points", "mean"),            # points finishes / starts
    dnf_rate=("target_is_dnf", "mean"),                  # retirements / starts
    teammate_quali_rate=("ahead_of_teammate_grid", "mean"),  # how often he out-qualified his teammate
).reset_index()

profiles = profiles[profiles["starts"] >= MIN_STARTS]           # drop drivers with fewer than 5 races
profiles["finish_std"] = profiles["finish_std"].fillna(0)

print("Driver-season profiles:", len(profiles))                 # 703
print("Different drivers:", profiles["driver_id"].nunique())   # 153
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
profiles.to_csv(OUTPUT, index=False)
print(profiles[profiles["season"] == 2024].sort_values("win_rate", ascending=False).head(5)[
    ["driver_name", "season", "avg_finish", "win_rate"]].to_string(index=False))
