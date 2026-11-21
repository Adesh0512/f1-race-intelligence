# 09. Unsupervised Dataset: Key Logic & Core Summary

## 1. Why a Separate Unsupervised Dataset?
Dashboard 2 (classification) works on **race entries with a label** (`target_is_win`).
Clustering needs **no label**: the goal is to discover groups that nobody defined in advance.
So we change the grain from *one driver in one race* to **one driver across one season**: a performance profile.

## 2. Dataset Specification
| Property | Value |
|---|---|
| Source | `data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv` (12,358 race entries) |
| Grain | 1 row per `(driver_id, season)` |
| Filter | ≥ 5 starts in the season (drops one-off substitutes) |
| Rows | **703 driver-seasons**, **153 drivers**, 1994–2024 |
| Features | **9 numeric**, no class label |
| Nulls | 0 (`finish_std` = 0 when a driver has a single classified finish) |
| Preprocessing | z-score standardisation (`StandardScaler`): K-Means uses Euclidean distance, so unscaled `starts` (≈17) would swamp `win_rate` (≈0.04) |
| Output | `09_unsupervised_dataset/driver_season_profiles.csv` |

## 3. The 9 Clustering Features
| # | Feature | Meaning | Mean | Range |
|---|---|---|---:|---|
| 1 | `avg_grid` | Mean starting grid slot (qualifying pace) | 11.39 | 1.26 – 20.0 |
| 2 | `avg_finish` | Mean finish position (race pace) | 11.31 | 1.27 – 19.56 |
| 3 | `finish_std` | Std-dev of finish (consistency) | 4.61 | 0.62 – 8.40 |
| 4 | `win_rate` | Wins / starts | 0.044 | 0 – 0.864 |
| 5 | `podium_rate` | Podiums / starts | 0.134 | 0 – 1.0 |
| 6 | `points_rate` | P1–P10 finishes / starts | 0.453 | 0 – 1.0 |
| 7 | `dnf_rate` | Retirements / starts (reliability) | 0.297 | 0 – 1.0 |
| 8 | `teammate_quali_rate` | Share of races out-qualifying the teammate (driver vs. car) | 0.460 | 0 – 1.0 |
| 9 | `starts` | Starts in the season (seat security) | 17.36 | 5 – 24 |

> Using season outcomes (wins, podiums) as **features** is fine here: clustering is descriptive, not predictive, so there is no "future" to leak. No class label is fed to the algorithm.

## 4. Minimal Build Logic
```python
prof = df.groupby(["driver_id", "season"]).agg(
    starts=("race_id", "nunique"), avg_grid=("grid_position", "mean"),
    avg_finish=("target_finish_position", "mean"), finish_std=("target_finish_position", "std"),
    win_rate=("target_is_win", "mean"), podium_rate=("target_is_podium", "mean"),
    points_rate=("target_is_points", "mean"), dnf_rate=("target_is_dnf", "mean"),
    teammate_quali_rate=("ahead_of_teammate_grid", "mean"))
prof = prof[prof["starts"] >= 5]
X = StandardScaler().fit_transform(prof[CLUSTER_FEATURE_COLS])
```

## 5. Run
```bash
python3 09_unsupervised_dataset/build_unsupervised_dataset.py
```
