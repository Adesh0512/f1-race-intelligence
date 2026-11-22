"""
Forecasts the next races that have not happened yet with the champion XGBoost.

History = the 1994-2024 feature store (f1.zip) + the results since then (data/external/results_2025_onwards.csv,
fetched from the Jolpica-F1 API). The 16 pre-race features are rebuilt from that history with the feature store's
own definitions (verified: they reproduce the stored 2024 values exactly), for any circuit, team line-up and grid.

1. Real-world test: the champion trained on 1994-2024 only predicts every race since (it never saw them).
2. The champion's settings are retrained on everything up to the latest race, then forecast the upcoming races.

Usage: .venv/bin/python 06_classification_algorithm/future_race.py
       (writes forecast_upcoming.csv and real_world_test.csv; self-checks the feature rebuild)
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


EXTERNAL = os.path.join(ROOT, "data", "external")


def load_history(include_recent=True):
    """Every driver-race with the unclipped finish and race points the rolling features use (1994-2024, then 2025 on)."""
    d = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
    raw = pd.read_csv(os.path.join(ROOT, "data", "raw", "F1_ML_Winner_Prediction_Dataset.csv"), low_memory=False,
                      usecols=["race_id", "driver_id", "finish_position", "race_points", "driver_dob"])
    h = d.merge(raw, on=["race_id", "driver_id"], how="left")
    h["finish"] = h["finish_position"].fillna(h["target_finish_position"])  # raw starts in 2004; earlier rows use the store's finish
    h["race_points"] = h["race_points"].fillna(0)
    h["race_date"] = pd.to_datetime(h["race_date"])
    dob = raw.dropna(subset=["driver_dob"]).drop_duplicates("driver_id").set_index("driver_id")["driver_dob"]
    recent_csv = os.path.join(EXTERNAL, "results_2025_onwards.csv")
    if include_recent and os.path.exists(recent_csv):
        rec = pd.read_csv(recent_csv)
        rec["race_date"] = pd.to_datetime(rec["race_date"])
        rec["finish"] = rec["finish_position"]
        dob = pd.concat([dob, rec.drop_duplicates("driver_id").set_index("driver_id")["driver_dob"]])
        dob = dob[~dob.index.duplicated()]
        h = pd.concat([h, rec.drop(columns=["status"], errors="ignore")], ignore_index=True)
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
    """Champion settings (improved_classifier.py), trained on every row of history that has its features."""
    train = history.dropna(subset=["driver_rolling_finish_5"])
    model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15, subsample=0.85,
                              colsample_bytree=0.85, random_state=42, eval_metric="logloss")
    return model.fit(train[FEATURES].fillna(0), train["target_is_win"].astype(int))


def add_recent_features(history, dob):
    """Rebuilds the 16 features for every race after the feature store, each from the history before it."""
    out = history.copy()
    for rid in history.loc[history["driver_rolling_finish_5"].isna(), "race_id"].unique():
        race = history[history["race_id"] == rid]
        f = race_features(history, dob, race[["driver_id", "driver_name", "constructor_id", "constructor_name", "grid_position"]],
                          race["circuit_id"].iat[0], race["race_date"].iat[0])
        out.loc[race.index, FEATURES] = f[FEATURES].values
    return out


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


def upcoming_calendar():
    """The races still to run after the latest result (fetched with the results)."""
    cal = pd.read_csv(os.path.join(EXTERNAL, "calendar_upcoming.csv"))
    cal["race_date"] = pd.to_datetime(cal["race_date"])
    return cal


# ---------------------------------------------------------------- scenarios (what the dashboard filters change)
def move_to_grid(lineup, driver_id, slot):
    """Puts a driver on a grid slot; whoever held it takes his old slot, so the grid stays a valid order."""
    out = lineup.copy()
    me = out.index[out["driver_id"] == driver_id][0]
    old = out.at[me, "grid_position"]
    out.loc[out["grid_position"] == slot, "grid_position"] = old
    out.at[me, "grid_position"] = slot
    return out


def move_to_team(lineup, driver_id, constructor_id, constructor_name):
    out = lineup.copy()
    out.loc[out["driver_id"] == driver_id, ["constructor_id", "constructor_name"]] = [constructor_id, constructor_name]
    return out


def forecast(history, dob, model, lineup, circuit_id, race_date, overrides=None):
    """
    Win probability for every driver in one race.
    overrides: {driver_id: {"driver_rolling_finish_5": x, "ahead_of_teammate_grid": 0/1}} replace a built feature;
    the derived grid_vs_form_gap is recomputed so the inputs stay consistent.
    """
    f = race_features(history, dob, lineup, circuit_id, race_date)
    for driver_id, values in (overrides or {}).items():
        for feature, value in values.items():
            f.loc[f["driver_id"] == driver_id, feature] = value
    f["grid_vs_form_gap"] = f["grid_position"] - f["driver_rolling_finish_5"]
    f["win_probability"] = win_probability(model, f)
    f["rank"] = f["win_probability"].rank(ascending=False, method="first").astype(int)
    return f.sort_values("rank").reset_index(drop=True)


def what_if_venues(history):
    """Every circuit of the latest season, so any track can be tried as a hypothetical next race."""
    last = history[history["season"] == history["season"].max()].drop_duplicates("circuit_id").sort_values("round")
    return last[["circuit_id", "circuit_name", "race_name"]].reset_index(drop=True)


def real_world_test(store_only, recent, dob):
    """The champion as validated (trained on 1994-2024 only) predicts every race after 2024."""
    model = full_history_model(store_only)
    rows = []
    for rid, race in recent.groupby("race_id", sort=False):
        p = win_probability(model, race)
        pick, actual = race["driver_name"].iat[int(np.argmax(p))], race.loc[race["target_is_win"] == 1, "driver_name"].iat[0]
        pole = race.loc[race["grid_position"] == race["grid_position"].min(), "driver_name"].iat[0]
        rows.append({"season": race["season"].iat[0], "round": race["round"].iat[0], "race_name": race["race_name"].iat[0],
                     "predicted_winner": pick, "win_probability": round(float(p.max()), 2), "actual_winner": actual,
                     "pole_sitter": pole, "model_correct": int(pick == actual), "pole_correct": int(pole == actual)})
    return pd.DataFrame(rows).sort_values(["season", "round"])


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
    store_only, dob = load_history(include_recent=False)
    print("[+] self-check: rebuilt 2024 Abu Dhabi GP features match the feature store", self_check(store_only, dob))
    history, dob = load_history()
    history = add_recent_features(history, dob)
    recent = history[history["race_date"] > store_only["race_date"].max()]

    test = real_world_test(store_only, recent, dob)
    test.to_csv(os.path.join(BASE, "real_world_test.csv"), index=False)
    print(f"[+] real-world test on {len(test)} races after 2024: model {test.model_correct.sum()} correct, "
          f"pole-sitter {test.pole_correct.sum()} correct")

    model = full_history_model(history)
    lineup = latest_lineup(history)
    lineup["grid_position"] = projected_grid(history, lineup)
    out = []
    for race in upcoming_calendar().itertuples(index=False):
        f = race_features(history, dob, lineup, race.circuit_id, race.race_date)
        out.append(f.assign(season=race.season, round=race.round, race_name=race.race_name, race_date=race.race_date.date(),
                            circuit_name=race.circuit_name, win_probability=win_probability(model, f).round(2)))
    fc = pd.concat(out, ignore_index=True)
    fc["predicted_rank"] = fc.groupby(["season", "round"])["win_probability"].rank(ascending=False, method="first").astype(int)
    fc = fc[["season", "round", "race_name", "race_date", "circuit_name", "driver_name", "constructor_name", "grid_position",
             "win_probability", "predicted_rank"]]
    fc.to_csv(os.path.join(BASE, "forecast_upcoming.csv"), index=False)

    # Power BI cannot run the model, so precompute every race x pole-sitter scenario for its slicers
    last_win = history[(history["race_date"] == history["race_date"].max()) & (history["target_is_win"] == 1)].iloc[0]
    rows = []
    for race in upcoming_calendar().itertuples(index=False):
        for pole in [None] + list(lineup.sort_values("grid_position")["driver_id"].iloc[1:]):
            grid = lineup if pole is None else move_to_grid(lineup, pole, 1)
            f = forecast(history, dob, model, grid, race.circuit_id, race.race_date)
            rows.append(f.assign(
                race=f"{race.race_name}, {race.race_date:%d %b %Y}", race_date=race.race_date.date(), circuit_name=race.circuit_name,
                pole_scenario=f"Projected grid ({f.iloc[f['grid_position'].argmin()]['driver_name']} on pole)" if pole is None
                else f"{f.loc[f['driver_id'] == pole, 'driver_name'].iat[0]} on pole", is_default=int(pole is None),
                last_race=f"{last_win['race_name']}, {last_win['race_date']:%d %b}: {last_win['driver_name']}"))
    sc = pd.concat(rows, ignore_index=True).rename(columns={"rank": "predicted_rank"})
    sc["career_win_rate"] *= 100
    sc = sc[["race", "race_date", "circuit_name", "pole_scenario", "is_default", "last_race", "driver_name", "constructor_name",
             "grid_position", "win_probability", "predicted_rank", "driver_rolling_finish_5", "constructor_rolling_points_10",
             "circuit_experience", "circuit_avg_finish", "career_win_rate"]].round(2)
    assert sc.groupby(["race", "pole_scenario"])["win_probability"].sum().between(99.5, 100.5).all()
    sc.to_csv(os.path.join(BASE, "forecast_scenarios.csv"), index=False)
    print(f"[+] forecast_scenarios.csv: {sc.groupby(['race', 'pole_scenario']).ngroups} race x pole scenarios for Power BI")
    last = history.iloc[-1]
    print(f"[+] forecast_upcoming.csv: {fc.groupby(['season', 'round']).ngroups} upcoming races x {len(lineup)} drivers "
          f"(history up to {last['season']} {last['race_name']})")
    print(fc[fc.predicted_rank <= 3].to_string(index=False))
