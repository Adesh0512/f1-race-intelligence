"""
Forecasts races that have not happened yet (2025) with the champion XGBoost.

The 16 pre-race features are rebuilt from the full 1994-2024 history with the same definitions
as the feature store (verified: they reproduce the stored 2024 values), for any circuit, team line-up and grid.
The model is the champion's exact settings, retrained on every season 1994-2024 once it had been validated
on the unseen 2022-2024 races.

Usage: .venv/bin/python 06_classification_algorithm/future_race.py   (writes forecast_2025.csv and self-checks)
"""

import os
import sys

import numpy as np
import pandas as pd
import xgboost as xgb

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, "..")
sys.path.insert(0, BASE)
from feature_engineering import ENGINEERED_FEATURE_COLS as FEATURES
from improved_classifier import softmax_race_probabilities

# Values the feature store uses before a driver, team or driver-at-circuit has any history
FIRST = {"driver_rolling_finish_5": 14.0, "driver_rolling_points_5": 0.5, "constructor_rolling_finish_10": 12.0,
         "constructor_rolling_points_10": 0.0, "circuit_avg_finish": 13.0, "career_dnf_rate": 0.2}


def load_history():
    """Every driver-race 1994-2024 with the unclipped finish and race points the rolling features use."""
    d = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
    raw = pd.read_csv(os.path.join(ROOT, "data", "raw", "F1_ML_Winner_Prediction_Dataset.csv"), low_memory=False,
                      usecols=["race_id", "driver_id", "finish_position", "race_points", "driver_dob"])
    h = d.merge(raw, on=["race_id", "driver_id"], how="left")
    h["finish"] = h["finish_position"].fillna(h["target_finish_position"])  # raw starts in 2004; earlier rows use the store's finish
    h["race_points"] = h["race_points"].fillna(0)
    h["race_date"] = pd.to_datetime(h["race_date"])
    dob = raw.dropna(subset=["driver_dob"]).drop_duplicates("driver_id").set_index("driver_id")["driver_dob"]
    return h.sort_values(["race_date", "race_id", "grid_position"]).reset_index(drop=True), pd.to_datetime(dob)


def race_features(history, dob, lineup, circuit_id, race_date):
    """
    Pre-race features for one race from the history before race_date.
    lineup: DataFrame with driver_id, driver_name, constructor_id, constructor_name, grid_position.
    """
    past = history[history["race_date"] < race_date]
    rows = []
    for r in lineup.itertuples(index=False):
        mine = past[past["driver_id"] == r.driver_id]
        team = past[past["constructor_id"] == r.constructor_id].tail(10)
        here = mine[mine["circuit_id"] == circuit_id]
        season = mine[mine["race_date"].dt.year == race_date.year]
        rows.append({
            "driver_rolling_finish_5": mine["finish"].tail(5).mean() if len(mine) else FIRST["driver_rolling_finish_5"],
            "driver_rolling_points_5": mine["race_points"].tail(5).mean() if len(mine) else FIRST["driver_rolling_points_5"],
            "constructor_rolling_finish_10": team["finish"].mean() if len(team) else FIRST["constructor_rolling_finish_10"],
            "constructor_rolling_points_10": team["race_points"].mean() if len(team) else FIRST["constructor_rolling_points_10"],
            "circuit_avg_finish": here["finish"].mean() if len(here) else FIRST["circuit_avg_finish"],
            "circuit_win_rate": here["target_is_win"].mean() if len(here) else 0.0,
            "circuit_podium_rate": here["target_is_podium"].mean() if len(here) else 0.0,
            "circuit_experience": len(here),
            "season_points_before": season["race_points"].sum(),
            "career_starts": len(mine),
            "career_win_rate": mine["target_is_win"].mean() if len(mine) else 0.0,
            "career_dnf_rate": mine["target_is_dnf"].mean() if len(mine) else FIRST["career_dnf_rate"],
            "driver_age": round((race_date - dob[r.driver_id]).days / 365.25, 1) if r.driver_id in dob.index else np.nan,  # store keeps 1 decimal
        })
    f = pd.concat([lineup.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    f["ahead_of_teammate_grid"] = (f["grid_position"] < f.groupby("constructor_id")["grid_position"].transform("max")).astype(int)
    f["grid_vs_form_gap"] = f["grid_position"] - f["driver_rolling_finish_5"]
    return f


def full_history_model(history):
    """Champion settings (improved_classifier.py), trained on every season once validation was done."""
    model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15, subsample=0.85,
                              colsample_bytree=0.85, random_state=42, eval_metric="logloss")
    return model.fit(history[FEATURES].fillna(0), history["target_is_win"].astype(int))


def win_probability(model, features):
    raw = model.predict_proba(features[FEATURES].fillna(0))[:, 1]
    return softmax_race_probabilities(raw, [0] * len(features)) * 100


def latest_lineup(history):
    """The 20 drivers and teams of the last race in the data (2024 Abu Dhabi GP)."""
    last = history[history["race_id"] == history["race_id"].iloc[-1]]
    return last[["driver_id", "driver_name", "constructor_id", "constructor_name"]].reset_index(drop=True)


def projected_grid(history, lineup):
    """Grid projection until qualifying: order of each driver's average start over his last 5 races."""
    avg = history.groupby("driver_id")["grid_position"].apply(lambda s: s.tail(5).mean())
    return lineup["driver_id"].map(avg).rank(method="first").astype(int)


def calendar_2025(history):
    """Grands Prix of the last season in the data, dated one year on (the 2025 calendar is not in the data)."""
    last = history[history["season"] == history["season"].max()].drop_duplicates("race_id").sort_values("round")
    cal = last[["round", "race_name", "circuit_id", "circuit_name", "race_date"]].copy()
    cal["race_date"] = cal["race_date"] + pd.DateOffset(years=1)
    return cal.reset_index(drop=True)


def self_check(history, dob):
    """Rebuilding the real 2024 Abu Dhabi GP from the races before it must give the stored feature values."""
    last_id = history["race_id"].iloc[-1]
    real = history[history["race_id"] == last_id].reset_index(drop=True)
    built = race_features(history, dob, real[["driver_id", "driver_name", "constructor_id", "constructor_name", "grid_position"]],
                          real["circuit_id"].iat[0], real["race_date"].iat[0])
    worst = {c: float(np.abs(built[c].round(2) - real[c].round(2)).max()) for c in FEATURES}
    assert all(v <= 0.011 for v in worst.values()), f"feature rebuild differs from the feature store: {worst}"
    return worst


if __name__ == "__main__":
    history, dob = load_history()
    print("[+] self-check: rebuilt 2024 Abu Dhabi GP features match the feature store", self_check(history, dob))
    model = full_history_model(history)
    lineup = latest_lineup(history)
    lineup["grid_position"] = projected_grid(history, lineup)
    out = []
    for race in calendar_2025(history).itertuples(index=False):
        f = race_features(history, dob, lineup, race.circuit_id, race.race_date)
        out.append(f.assign(season=2025, round=race.round, race_name=race.race_name, circuit_name=race.circuit_name,
                            win_probability=win_probability(model, f).round(2)))
    fc = pd.concat(out, ignore_index=True)
    fc["predicted_rank"] = fc.groupby("round")["win_probability"].rank(ascending=False, method="first").astype(int)
    fc = fc[["season", "round", "race_name", "circuit_name", "driver_name", "constructor_name", "grid_position",
             "win_probability", "predicted_rank"]]
    fc.to_csv(os.path.join(BASE, "forecast_2025.csv"), index=False)
    winners = fc[fc["predicted_rank"] == 1]
    print(f"[+] forecast_2025.csv: {fc['round'].nunique()} races x {len(lineup)} drivers")
    print(winners["driver_name"].value_counts().to_string())
