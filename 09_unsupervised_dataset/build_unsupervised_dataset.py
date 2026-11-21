"""
Unsupervised Dataset Construction (Parameter 09)
================================================
Builds an UNLABELLED driver-season performance profile dataset for clustering
from the 1994–2024 race-entry feature store.

Grain:   1 row per (driver, season) with >= MIN_STARTS race starts.
Purpose: Discover natural performance tiers (contenders, midfield, backmarkers)
         without using any class label — no target column enters the feature matrix.

Outputs:
- 09_unsupervised_dataset/driver_season_profiles.csv   (identifiers + 9 features)
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

MIN_STARTS = 5

CLUSTER_FEATURE_COLS = [
    "avg_grid",              # mean starting grid slot (qualifying pace)
    "avg_finish",            # mean classified finish position (race pace)
    "finish_std",            # finish position std-dev (consistency)
    "win_rate",              # wins / starts
    "podium_rate",           # podiums / starts
    "points_rate",           # points finishes / starts
    "dnf_rate",              # retirements / starts (reliability / incidents)
    "teammate_quali_rate",   # share of races out-qualifying the teammate
    "starts",                # race starts in the season (seat security)
]

ID_COLS = ["driver_id", "driver_name", "season", "constructor_name"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(BASE_DIR, "driver_season_profiles.csv")


def build_driver_season_profiles(min_starts=MIN_STARTS):
    data_path = os.path.join(BASE_DIR, "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    df = pd.read_csv(data_path, low_memory=False)

    g = df.groupby(["driver_id", "season"])
    prof = g.agg(
        driver_name=("driver_name", "first"),
        # main team of the season (handles mid-season moves)
        constructor_name=("constructor_name", lambda s: s.mode().iat[0]),
        starts=("race_id", "nunique"),
        avg_grid=("grid_position", "mean"),
        avg_finish=("target_finish_position", "mean"),
        finish_std=("target_finish_position", "std"),
        win_rate=("target_is_win", "mean"),
        podium_rate=("target_is_podium", "mean"),
        points_rate=("target_is_points", "mean"),
        dnf_rate=("target_is_dnf", "mean"),
        teammate_quali_rate=("ahead_of_teammate_grid", "mean"),
    ).reset_index()

    prof = prof[prof["starts"] >= min_starts].copy()
    prof["finish_std"] = prof["finish_std"].fillna(0.0)
    prof = prof[ID_COLS + CLUSTER_FEATURE_COLS].sort_values(["season", "avg_finish"]).reset_index(drop=True)
    return prof


def load_profiles():
    """Returns (profiles_df, X_scaled). Builds the CSV on first use."""
    if not os.path.exists(OUT_CSV):
        build_driver_season_profiles().to_csv(OUT_CSV, index=False)
    prof = pd.read_csv(OUT_CSV)
    X = StandardScaler().fit_transform(prof[CLUSTER_FEATURE_COLS])
    return prof, X


if __name__ == "__main__":
    print("=" * 80)
    print("   PARAMETER 09: UNSUPERVISED DATASET — DRIVER-SEASON PERFORMANCE PROFILES")
    print("=" * 80)
    prof = build_driver_season_profiles()
    prof.to_csv(OUT_CSV, index=False)

    assert prof[CLUSTER_FEATURE_COLS].isna().sum().sum() == 0, "Null values in clustering features"
    assert not prof.duplicated(["driver_id", "season"]).any(), "Duplicate driver-season rows"
    assert not any(c.startswith("target_") for c in CLUSTER_FEATURE_COLS), "Label leaked into features"

    print(f"[+] Profiles: {len(prof):,} driver-seasons | {prof['driver_id'].nunique()} drivers | "
          f"{prof['season'].min()}–{prof['season'].max()} | min starts = {MIN_STARTS}")
    print(f"[+] Feature matrix: {len(prof):,} x {len(CLUSTER_FEATURE_COLS)} (no class label)")
    print("\nFeature Summary:")
    print(prof[CLUSTER_FEATURE_COLS].describe().T[["mean", "std", "min", "50%", "max"]].round(3).to_string())
    print(f"\n[+] Saved: {OUT_CSV}")
