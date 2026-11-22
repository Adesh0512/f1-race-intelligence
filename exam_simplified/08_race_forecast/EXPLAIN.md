# Folder 08 — Next-Race Forecast

**Responsibility of this folder:** predict a race that has not happened yet, the 2026 Qatar Grand Prix (29 Nov 2026), from every race up to the 2026 Las Vegas GP (22 Nov 2026).
**Real project:** `06_classification_algorithm/future_race.py`, `data/external/fetch_recent_results.py` and the dashboard page *Race Predictor*.

---

## File: `forecast_next_race.py`

**1. Location:** `exam_simplified/08_race_forecast/forecast_next_race.py`

**2. What it does:**
1. Joins the 1994–2024 history with the 45 races of 2025–2026 (from the public Jolpica-F1 API).
2. Rebuilds the 16 features for every driver from races before the race date.
3. Trains the champion XGBoost on all of it.
4. Scores the next race and applies the race softmax.

**3. Parameters and logic**
| Parameter | Value | Meaning |
|---|---|---|
| History | 622 races, last = Las Vegas 2026 | f1.zip + Jolpica-F1 |
| Next race | Qatar GP, Lusail, 2026-11-29 | from `calendar_upcoming.csv` |
| Line-up | drivers of the last race | who will start |
| Projected grid | rank of each driver's average start over his last 5 races | qualifying has not happened yet |
| Defaults for no history | form 14.0, points 0.5, team form 12.0, team points 0, circuit 13.0, DNF rate 0.2 | same as the feature store |
| Model | the champion XGBoost (same settings), softmax T = 0.8 | |
| `POLE_SITTER` | None or a name | "what if" this driver starts first |

**Result (projected grid):** Antonelli 29.9%, Norris 24.6%, Verstappen 23.8%, Leclerc 10.3%, Russell 3.8%.
**Honest real-world test:** a model trained only to 2024 called 29 of the 45 races of 2025–2026; backing the pole-sitter called 31. The 2026 rule change made older form a weaker guide.

**4. Simplified code**
```python
# ============================================================
# FILE: 08_race_forecast/forecast_next_race.py
# REAL MODULES: 06_classification_algorithm/future_race.py and data/external/fetch_recent_results.py
# WHAT IT DOES: predicts the NEXT Grand Prix (2026 Qatar, 29 Nov 2026).
#   1. history = f1.zip results (1994-2024) + 2025-2026 results from the Jolpica-F1 API (up to Las Vegas 2026)
#   2. for every driver, rebuild the 16 features from races BEFORE the race date
#   3. train the champion XGBoost on all history and score the next race
#   4. race softmax -> chances that add up to 100%
# You can change POLE_SITTER to see a "what if" (like the dashboard filter).
# ============================================================

import os
import math
import pandas as pd
import xgboost as xgb

POLE_SITTER = None          # e.g. "Max Verstappen" to put him on pole; None = projected grid
TEMPERATURE = 0.8

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.join(HERE, "..", "..")
FEATURES = ["grid_position", "driver_rolling_finish_5", "driver_rolling_points_5", "constructor_rolling_finish_10",
            "constructor_rolling_points_10", "circuit_avg_finish", "circuit_win_rate", "circuit_podium_rate",
            "circuit_experience", "season_points_before", "career_starts", "career_win_rate", "career_dnf_rate",
            "ahead_of_teammate_grid", "driver_age", "grid_vs_form_gap"]
# Values the project uses when a driver or team has no history yet
FIRST = {"form": 14.0, "points": 0.5, "team_form": 12.0, "team_points": 0.0, "circuit": 13.0, "dnf": 0.2}

# ---------- 1. Load the history ----------
store = pd.read_csv(os.path.join(PROJECT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
raw = pd.read_csv(os.path.join(PROJECT, "data", "raw", "F1_ML_Winner_Prediction_Dataset.csv"), low_memory=False,
                  usecols=["race_id", "driver_id", "finish_position", "race_points", "driver_dob"])
history = store.merge(raw, on=["race_id", "driver_id"], how="left")
history["finish"] = history["finish_position"].fillna(history["target_finish_position"])
history["race_points"] = history["race_points"].fillna(0)
recent = pd.read_csv(os.path.join(PROJECT, "data", "external", "results_2025_onwards.csv"))   # 45 races of 2025-2026
recent["finish"] = recent["finish_position"]
history = pd.concat([history, recent.drop(columns=["status"])], ignore_index=True)
history["race_date"] = pd.to_datetime(history["race_date"])
history = history.sort_values(["race_date", "race_id", "grid_position"]).reset_index(drop=True)
birthdays = pd.to_datetime(history.dropna(subset=["driver_dob"]).drop_duplicates("driver_id").set_index("driver_id")["driver_dob"])
print("History:", history["race_id"].nunique(), "races, last one:", history.iloc[-1]["race_name"], history.iloc[-1]["race_date"].date())


def build_features(lineup, circuit_id, race_date):
    """The 16 pre-race features of every driver, using ONLY races before race_date."""
    past = history[history["race_date"] < race_date]
    rows = []
    for driver in lineup.itertuples():
        mine = past[past["driver_id"] == driver.driver_id]                    # this driver's earlier races
        team = past[past["constructor_id"] == driver.constructor_id].tail(10)  # his team's last 10 entries
        here = mine[mine["circuit_id"] == circuit_id]                          # his earlier races at this track
        season = mine[mine["race_date"].dt.year == race_date.year]             # earlier races this season
        has = len(mine) > 0
        rows.append({
            "driver_rolling_finish_5": mine["finish"].tail(5).mean() if has else FIRST["form"],
            "driver_rolling_points_5": mine["race_points"].tail(5).mean() if has else FIRST["points"],
            "constructor_rolling_finish_10": team["finish"].mean() if len(team) else FIRST["team_form"],
            "constructor_rolling_points_10": team["race_points"].mean() if len(team) else FIRST["team_points"],
            "circuit_avg_finish": here["finish"].mean() if len(here) else FIRST["circuit"],
            "circuit_win_rate": here["target_is_win"].mean() if len(here) else 0.0,
            "circuit_podium_rate": here["target_is_podium"].mean() if len(here) else 0.0,
            "circuit_experience": len(here),
            "season_points_before": season["race_points"].sum(),
            "career_starts": len(mine),
            "career_win_rate": mine["target_is_win"].mean() if has else 0.0,
            "career_dnf_rate": mine["target_is_dnf"].mean() if has else FIRST["dnf"],
            "driver_age": round((race_date - birthdays[driver.driver_id]).days / 365.25, 1)
                          if driver.driver_id in birthdays.index else None,
        })
    features = pd.concat([lineup.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    team_worst_grid = features.groupby("constructor_id")["grid_position"].transform("max")
    features["ahead_of_teammate_grid"] = (features["grid_position"] < team_worst_grid).astype(int)
    features["grid_vs_form_gap"] = features["grid_position"] - features["driver_rolling_finish_5"]
    return features


# ---------- 2. Fill in the features of the 2025-2026 races (the store stops at 2024) ----------
for race_id in history.loc[history["driver_rolling_finish_5"].isna(), "race_id"].unique():
    race = history[history["race_id"] == race_id]
    lineup = race[["driver_id", "driver_name", "constructor_id", "constructor_name", "grid_position"]]
    built = build_features(lineup, race["circuit_id"].iat[0], race["race_date"].iat[0])
    history.loc[race.index, FEATURES] = built[FEATURES].values

# ---------- 3. Train the champion on all history ----------
model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15,
                          subsample=0.85, colsample_bytree=0.85, random_state=42, eval_metric="logloss")
model.fit(history[FEATURES].fillna(0), history["target_is_win"].astype(int))

# ---------- 4. The next race and its projected grid ----------
calendar = pd.read_csv(os.path.join(PROJECT, "data", "external", "calendar_upcoming.csv"))
next_race = calendar.iloc[0]                                                  # Qatar Grand Prix, 2026-11-29
last_race = history[history["race_id"] == history["race_id"].iloc[-1]]
lineup = last_race[["driver_id", "driver_name", "constructor_id", "constructor_name"]].reset_index(drop=True)
# Qualifying has not happened: order drivers by their average starting slot over their last 5 races
average_start = history.groupby("driver_id")["grid_position"].apply(lambda s: s.tail(5).mean())
lineup["grid_position"] = lineup["driver_id"].map(average_start).rank(method="first").astype(int)

if POLE_SITTER:   # what-if: swap the chosen driver with the driver on pole
    chosen = lineup["driver_name"] == POLE_SITTER
    on_pole = lineup["grid_position"] == 1
    lineup.loc[on_pole, "grid_position"] = int(lineup.loc[chosen, "grid_position"].iat[0])
    lineup.loc[chosen, "grid_position"] = 1

features = build_features(lineup, next_race["circuit_id"], pd.Timestamp(next_race["race_date"]))
scores = model.predict_proba(features[FEATURES].fillna(0))[:, 1]

# Race softmax so the chances add up to 100%
powered = [math.exp(math.log(max(s, 1e-7)) / TEMPERATURE) for s in scores]
features["win_chance_%"] = [round(100 * p / sum(powered), 1) for p in powered]

print(f"\nForecast: {next_race['race_name']} {next_race['season']} ({next_race['race_date']})")
print(features.sort_values("win_chance_%", ascending=False)[
    ["driver_name", "constructor_name", "grid_position", "driver_rolling_finish_5", "win_chance_%"]].head(5).to_string(index=False))
# Real project (projected grid): Antonelli 29.9%, Norris 24.6%, Verstappen 23.8%
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `history = store.merge(raw, ...)` | Add the exact finish and points to the 1994–2024 history |
| `recent = pd.read_csv(... "results_2025_onwards.csv")` | The 2025–2026 results |
| `def build_features(lineup, circuit_id, race_date)` | Builds the 16 features using only `past` races |
| `mine["finish"].tail(5).mean()` | Average of his last 5 finishes |
| `team = past[...].tail(10)` | His team's last 10 entries |
| `here = mine[mine["circuit_id"] == circuit_id]` | His record at this track |
| `ahead_of_teammate_grid = grid < team's worst grid` | 1 if he out-qualified his teammate |
| `for race_id in history.loc[...isna()...]` | Fill in the features of 2025–2026 races, one race at a time |
| `average_start ... .rank(method="first")` | The projected grid |
| `if POLE_SITTER:` | Swap the chosen driver with the pole-sitter (what-if) |
| `math.exp(math.log(s) / TEMPERATURE)` | Race softmax so the chances add up to 100% |

**6. Say this in the jury:** "A prediction must be about the future. The data runs to the Las Vegas Grand Prix, so we forecast the next race, Qatar. For each driver we rebuild the same 16 features from his history, score them with the champion model and turn them into chances that add up to 100%. Antonelli is the favourite at 29.9%."

**7. Viva question:** *Qualifying hasn't happened. How do you know the grid?*
**Answer:** We project it from each driver's average starting position over his last 5 races. In the dashboard you can set the real pole-sitter after qualifying, and the forecast updates instantly.
