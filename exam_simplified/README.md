# ApexIQ — Simplified Exam Version

This folder is a **short, beginner-friendly copy of the logic** of the real ApexIQ project. Each file here matches one real module, uses the same data and the same settings, and prints the same key numbers. It is for explaining the project, not for replacing it.

- **Project:** ApexIQ — Formula 1 Race Intelligence Using Data Warehousing and Data Mining
- **Team:** Adesh Patankar (ADT24SOCB0049), Dhruv Sakhare (ADT24SOCB0369)
- **Guide:** Dr. Reena Pagare
- **Course:** Data Warehousing and Data Mining, MIT School of Computing, 2026-27

---

## 1. Introduction

Formula 1 keeps detailed records of every race. ApexIQ stores 31 seasons of results (1994–2024) in a data warehouse and uses data mining to answer two questions:

1. **Before a race starts, who will win?** (supervised learning: classification)
2. **Without being told, which drivers are title contenders, midfield or backmarkers?** (unsupervised learning: clustering)

It also **forecasts the next real race**, the 2026 Qatar Grand Prix, from every race up to the 2026 Las Vegas Grand Prix.

## 2. Problem statement

Fans, teams and broadcasters guess race winners by intuition. Only 1 driver in about 21 wins a race, so the data is heavily imbalanced, and simply backing the driver on pole is already a strong rule. The problem is to build a warehouse that can be analysed from many angles, and models that beat simple rules when tested honestly on races they never saw.

## 3. Objectives

1. Design a star and snowflake schema and run OLAP queries.
2. Deploy the warehouse to Snowflake in layers, using its cloud features.
3. Build a leakage-free dataset with class labels and pre-race features.
4. Mine association rules with Apriori and FP-Growth and compare them.
5. Compare 7 classifiers and select a champion that predicts the winner.
6. Find driver tiers with clustering, comparing 6 algorithms.
7. Forecast the next Grand Prix and test the model on real later races.
8. Present everything in dashboards (Streamlit, Streamlit in Snowflake and Power BI).

## 4. Folder structure

```
exam_simplified/
├── README.md                     ← you are here
├── VIVA_PREP.md                  ← 2-3 minute pitch, who explains what, concepts, 30 viva questions, demo order
├── run_all.py                    ← runs every module in order
├── 01_data_warehouse/            ← Dashboard 1: star schema (ETL) and OLAP queries
│   ├── build_star_schema.py
│   ├── olap_queries.py
│   └── EXPLAIN.md
├── 02_snowflake/                 ← Dashboard 1: cloud deployment in 5 layers
│   ├── deploy_to_snowflake.py
│   └── EXPLAIN.md
├── 03_supervised_dataset/        ← Dashboard 2: class labels, 16 features, time split
│   ├── class_labels.py
│   ├── features_and_split.py
│   └── EXPLAIN.md
├── 04_pattern_mining/            ← Dashboard 2: Apriori vs FP-Growth, association rules
│   ├── apriori_vs_fpgrowth.py
│   └── EXPLAIN.md
├── 05_classifier_comparison/     ← Dashboard 2: 7 classifiers on unseen seasons
│   ├── compare_classifiers.py
│   └── EXPLAIN.md
├── 06_champion_model/            ← Dashboard 2: cost-sensitive XGBoost + race softmax
│   ├── xgboost_champion.py
│   └── EXPLAIN.md
├── 07_clustering/                ← Dashboard 3: driver-season profiles, 6 algorithms, K-Means tiers
│   ├── driver_season_profiles.py
│   ├── compare_clustering.py
│   ├── kmeans_tiers.py
│   └── EXPLAIN.md
├── 08_race_forecast/             ← forecast of the next Grand Prix (Qatar 2026)
│   ├── forecast_next_race.py
│   └── EXPLAIN.md
├── 09_dashboard/                 ← one-page race predictor dashboard
│   ├── mini_dashboard.py
│   └── EXPLAIN.md
└── output/                       ← files the scripts create (warehouse database, profiles)
```

Every `EXPLAIN.md` follows the same seven points for each file: location, what it does, parameters and logic, the code, a line-by-line explanation, what to say in the jury, and one viva question with its answer.

### Simplified file → real project file

| Simplified file | Real project file(s) |
|---|---|
| `01_data_warehouse/build_star_schema.py` | `00_data_warehouse/etl_master_ingestion.py`, `create_star_schema.sql`, `create_snowflake_schema.sql` |
| `01_data_warehouse/olap_queries.py` | `00_data_warehouse/olap_queries.sql` (12 queries), `run_olap_suite.py` |
| `02_snowflake/deploy_to_snowflake.py` | `deploy_to_snowflake.py`, `MASTER_SNOWFLAKE_DEPLOYMENT.sql`, `deploy_streamlit_app.py` |
| `03_supervised_dataset/class_labels.py` | `03_class_labels/label_generation.py` |
| `03_supervised_dataset/features_and_split.py` | `06_classification_algorithm/feature_engineering.py`, `07_innovation/` |
| `04_pattern_mining/apriori_vs_fpgrowth.py` | `04_pattern_mining/apriori_analysis.py`, `fp_growth_analysis.py` |
| `05_classifier_comparison/compare_classifiers.py` | `05_algorithm_comparison/train_comparison.py`, `temporal_validation.py` |
| `06_champion_model/xgboost_champion.py` | `06_classification_algorithm/improved_classifier.py`, `08_performance_metrics/calculate_metrics.py` |
| `07_clustering/driver_season_profiles.py` | `09_unsupervised_dataset/build_unsupervised_dataset.py` |
| `07_clustering/compare_clustering.py` | `10_clustering_comparison/clustering_comparison.py` |
| `07_clustering/kmeans_tiers.py` | `11_clustering_algorithm/kmeans_clustering.py`, `12_clustering_metrics/clustering_metrics.py` |
| `08_race_forecast/forecast_next_race.py` | `06_classification_algorithm/future_race.py`, `data/external/fetch_recent_results.py` |
| `09_dashboard/mini_dashboard.py` | `streamlit_app.py`, `pages/26_D2_Race_Predictor.py`, `powerbi/build_pbip.py` |
| `run_all.py` | `run_all_modules.py` |

## 5. How to run

From the project folder (`f1-race-intelligence`):

```bash
.venv/bin/python exam_simplified/run_all.py
```

```bash
.venv/bin/streamlit run exam_simplified/09_dashboard/mini_dashboard.py
```

Every file can also run on its own, for example `.venv/bin/python exam_simplified/06_champion_model/xgboost_champion.py`. Run `build_star_schema.py` before `olap_queries.py`, and `driver_season_profiles.py` before the other two clustering files.

## 6. Execution workflow (how the modules connect)

```
f1.zip results ──► 01 ETL ──► star schema ──► OLAP queries
                     │
                     └──► 02 Snowflake (RAW → CLEAN → DW → ML → ANALYTICS)

feature store (12,358 driver-races, 16 features, labels)
   ├──► 03 labels + time split
   ├──► 04 pattern mining (Apriori / FP-Growth → 1,393 rules)
   ├──► 05 compare 7 classifiers ──► 06 champion XGBoost ──► 08 forecast next race ──► 09 dashboard
   └──► 07 driver-season profiles ──► 6 clustering algorithms ──► K-Means tiers
```

1. **Dashboard 1 (data warehouse):** the ETL builds the star schema; OLAP queries analyse it; the same model is deployed to Snowflake.
2. **Dashboard 2 (supervised learning):** the feature store gives labels and pre-race features; pattern mining finds rules; 7 classifiers are compared; the champion XGBoost predicts each race and the next one.
3. **Dashboard 3 (unsupervised learning):** races are summarised into driver seasons; 6 algorithms are compared; K-Means finds 3 tiers, checked against the real championship.

## 7. Modules in one sentence each

| Module | In one sentence |
|---|---|
| 01 Data warehouse | Splits 8,650 results into dimensions (who/where/when) and a fact table (one row per driver per race), then rolls up, drills down, slices, dices and pivots. |
| 02 Snowflake | Puts the warehouse in the cloud in 5 layers, with cloning, Time Travel, a stream and task, a dynamic table and a secure view (42 objects). |
| 03 Supervised dataset | Defines the labels (win, podium, points, DNF), the 16 pre-race features, and trains on 1994–2021 and tests on 2022–2024. |
| 04 Pattern mining | Turns each driver-race into a basket of 24 possible items and finds 414 frequent itemsets and 1,393 rules with both algorithms. |
| 05 Classifier comparison | Trains 7 models and ranks them on ROC-AUC, PR-AUC, recall and winners picked. |
| 06 Champion model | Cost-sensitive XGBoost with a race softmax; it picks 40 of 68 unseen winners. |
| 07 Clustering | Builds 703 driver-season profiles, compares 6 algorithms and finds 3 tiers with K-Means. |
| 08 Race forecast | Rebuilds the 16 features up to the latest race and forecasts Qatar 2026. |
| 09 Dashboard | Filters for race and pole-sitter, which update the predicted podium. |

## 8. Algorithms and why they were used

| Algorithm | Used for | Why |
|---|---|---|
| ETL + star schema | storing the data | one join per dimension: fast, simple analysis |
| Snowflake schema | normalised version | removes repeated data (race → circuit → country) |
| Apriori | pattern mining | the classic algorithm; easy to explain |
| FP-Growth | pattern mining | no candidates, 2 scans; faster at low support |
| Logistic regression (grid only) | baseline | the "back the pole-sitter" rule every model must beat |
| Decision tree, random forest, gradient boosting, LightGBM | comparison | strong, common tabular models |
| **XGBoost (cost-sensitive)** | **champion classifier** | best ROC-AUC, PR-AUC and winners picked; class weighting built in |
| Race softmax (T = 0.8) | race probabilities | makes every race add up to 100%; the top driver is the pick |
| K-Means, K-Medoids, Ward, Gaussian Mixture, BIRCH, DBSCAN | clustering comparison | one of each main family (centroid, medoid, hierarchical, probabilistic, tree, density) |
| **K-Means (k = 3)** | **champion clustering** | best silhouette and Calinski-Harabasz, stable, easy to interpret |

## 9. Parameters and why they matter

| Parameter | Value | Why it matters |
|---|---|---|
| Seasons (supervised) | 1994–2024, 12,358 entries, 577 races | enough history to learn from |
| Warehouse fact | 8,650 rows, 2004–2024 | grain = 1 driver × 1 Grand Prix |
| Imbalance | 20.42 : 1 | why accuracy is misleading |
| Train / validate / test | ≤ 2021 / 2022 / 2023–2024 | the model never sees the future |
| Features | 16, all known before the race | no leakage |
| min_support / min_confidence | 0.02 / 0.25 | which itemsets and rules are kept |
| XGBoost | 100 trees, depth 4, learning rate 0.05, scale_pos_weight 15, subsample and colsample 0.85, seed 42 | the champion's settings |
| Softmax temperature | 0.8 | sharpens the race distribution |
| Clustering profiles | 703 driver-seasons, ≥ 5 starts, 9 standardised features | the unsupervised dataset |
| K-Means | k = 3, k-means++, 10 restarts, seed 42 | 3 tiers at the elbow |
| DBSCAN | eps 1.3, min_samples 5 | chosen from the k-distance curve |
| Snowflake | X-Small warehouse, auto-suspend 60 s, 5 schemas, 42 objects | small, cheap, layered |

## 10. Inputs and outputs

| Module | Input | Output |
|---|---|---|
| ETL | `F1_Warehouse_Master_65_Columns_2004_2024.csv` | `output/exam_warehouse.db` |
| Supervised modules | `data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv` | metrics printed on screen |
| Clustering | the same feature store | `output/driver_season_profiles.csv`, tiers and scores |
| Forecast | feature store + `data/external/results_2025_onwards.csv` + `calendar_upcoming.csv` | the win chance of every driver at Qatar 2026 |
| Dashboard | `06_classification_algorithm/forecast_scenarios.csv` | podium, chart and table in the browser |

## 11. Key results (memorise these)

| What | Number |
|---|---|
| Winners picked on unseen 2022–2024 | **40 of 68 (58.8%)** against 35 for the pole-sitter |
| Champion ROC-AUC / PR-AUC | **0.9629 / 0.6433** |
| Bootstrap gain over baseline | ROC-AUC +0.042, 95% CI [+0.018, +0.073] |
| Pattern mining | 414 itemsets, 1,393 rules, same from both algorithms |
| Clustering | K-Means k = 3, silhouette 0.264, tiers 108 / 325 / 270, **81% of Contenders finished top 3** |
| Next race | Qatar 2026: Antonelli 29.9%, Norris 24.6%, Verstappen 23.8% |
| Real-world test 2025–2026 | model 29 / 45 against the pole-sitter's 31 / 45 |

## 12. Limitations and scope

- **Pre-race only:** retirements, safety cars, strategy and weather happen after the start and cannot be predicted.
- **2025–2026:** the model was level with the pole-sitter in 2025 and behind in 2026, after a regulation change made older form a weaker guide.
- **Projected grid:** before qualifying the grid is estimated from recent starts.
- **Snowflake task:** it scores new results with a simple pole rule, not XGBoost, to save trial credits.
- **Power BI:** it cannot run Python, so it shows 44 precomputed scenarios.
- **Out of scope:** live in-race prediction and any betting use.

## 13. Differences found between earlier notes and the actual project

The numbers above come from the current code and result files. A few older notes differ; the current values are the correct ones:

| Older note | Current, verified value |
|---|---|
| `PROJECT_REPORT_DWDM_APEXIQ.md` names Prof. Nitin Alzende as guide and the year 2025–26 | guide Dr. Reena Pagare, academic year 2026-27 |
| `JURY_QA_PREP.md` says Power BI has 4 pages | the Power BI report has 13 pages and 116 visuals |
| Simplified BIRCH and stability scores | BIRCH silhouette 0.197 here against 0.195 in the real run; stability ARI 0.917 against 0.92. Small run-to-run differences; every other number matches exactly |
