"""
Formula 1 Race Intelligence — Power BI Master Package Generator
================================================================
Builds the Power BI workbook ONLY from the module output files, so Power BI
shows exactly the same numbers as the Streamlit dashboards and the report.
Run after run_all_modules.py.

Generates:
1. F1_Race_Intelligence_PowerBI_Dataset.xlsx (one sheet per Power BI table)
2. F1_PowerBI_Theme.json (light classification-sheet theme matching the dashboards)
"""

import os
import json
import pandas as pd
from sklearn.metrics import roc_curve

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_XLSX = os.path.join(BASE_DIR, "F1_Race_Intelligence_PowerBI_Dataset.xlsx")
OUTPUT_THEME = os.path.join(BASE_DIR, "F1_PowerBI_Theme.json")


def path(*p):
    return os.path.join(BASE_DIR, *p)


def build_tables():
    t = {}

    # Fact: the champion model's real predictions for every 2022–2024 holdout entry
    fact = pd.read_csv(path("06_classification_algorithm", "holdout_predictions.csv"))
    fact["predicted_rank_in_race"] = fact.groupby("race_id")["norm_prob"].rank(ascending=False, method="first").astype(int)
    fact["predicted_is_winner"] = (fact["predicted_rank_in_race"] == 1).astype(int)
    fact["is_winner_hit"] = fact["predicted_is_winner"] * fact["target_is_win"]
    fact["winner_in_top3"] = ((fact["predicted_rank_in_race"] <= 3) & (fact["target_is_win"] == 1)).astype(int)
    fact["confidence_tier"] = pd.cut(fact["norm_prob"], [-1, 0.05, 0.20, 0.50, 1.0],
                                     labels=["Low (<5%)", "Moderate (5–20%)", "Contender (20–50%)", "Favourite (>50%)"]).astype(str)
    t["Fact_Holdout_Predictions"] = fact

    # Dimensions: full 1994–2024 history
    hist = pd.read_csv(path("data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
    agg = dict(starts=("race_id", "count"), wins=("target_is_win", "sum"), podiums=("target_is_podium", "sum"),
               avg_grid=("grid_position", "mean"), avg_finish=("target_finish_position", "mean"),
               first_season=("season", "min"), last_season=("season", "max"))
    for name, key in [("Dim_Drivers", "driver_name"), ("Dim_Constructors", "constructor_name")]:
        d = hist.groupby(key).agg(**agg).reset_index()
        d["win_rate_pct"] = (d["wins"] / d["starts"] * 100).round(1)
        d[["avg_grid", "avg_finish"]] = d[["avg_grid", "avg_finish"]].round(2)
        t[name] = d.sort_values("wins", ascending=False)
    t["Dim_Circuits"] = (hist.groupby(["circuit_name", "circuit_country"])
                         .agg(grands_prix=("race_id", "nunique"), first_season=("season", "min"), last_season=("season", "max"))
                         .reset_index().sort_values("grands_prix", ascending=False))
    t["Dim_Races"] = hist[["race_id", "season", "round", "race_name", "race_date", "circuit_name"]].drop_duplicates().sort_values(["season", "round"])

    # Dashboard 2: supervised learning
    t["ML_Model_Comparison"] = pd.read_csv(path("05_algorithm_comparison", "comparison_results.csv"))
    t["ML_Temporal_Validation"] = pd.read_csv(path("05_algorithm_comparison", "temporal_validation_results.csv"))
    t["ML_Partition_Metrics"] = pd.read_csv(path("08_performance_metrics", "partition_metrics.csv"))
    fpr, tpr, _ = roc_curve(fact["target_is_win"], fact["raw_prob"])
    t["ML_ROC_Curve"] = pd.DataFrame({"model": "XGBoost (champion)", "false_positive_rate": fpr.round(4), "true_positive_rate": tpr.round(4)})
    t["ML_Feature_Importance"] = pd.read_csv(path("06_classification_algorithm", "feature_importance.csv"))
    t["ML_Association_Rules"] = pd.read_csv(path("04_pattern_mining", "association_rules.csv"))
    t["ML_Frequent_Itemsets"] = pd.read_csv(path("04_pattern_mining", "frequent_itemsets.csv"))
    t["ML_Support_Sweep"] = pd.read_csv(path("04_pattern_mining", "support_sweep_benchmark.csv"))

    # Dashboard 3: unsupervised learning
    t["CL_Driver_Season_Clusters"] = pd.read_csv(path("11_clustering_algorithm", "driver_season_clusters.csv"))
    t["CL_Cluster_Profiles"] = pd.read_csv(path("11_clustering_algorithm", "cluster_profiles.csv"))
    t["CL_Algorithm_Comparison"] = pd.read_csv(path("10_clustering_comparison", "comparison_results.csv"))

    # KPI sheet, every value read from the outputs above
    bench = json.load(open(path("04_pattern_mining", "pattern_mining_benchmark.json")))
    sig = pd.read_csv(path("05_algorithm_comparison", "significance_test.csv")).iloc[0]
    cm = json.load(open(path("12_clustering_metrics", "clustering_metrics.json")))
    ho = t["ML_Partition_Metrics"].set_index("partition").loc["Combined Holdout (2022–2024)"]
    wins = int(hist["target_is_win"].sum())
    t["Executive_KPI_Summary"] = pd.DataFrame([
        ("Dataset", "Labelled race entries", f"{len(hist):,}", f"{hist['race_id'].nunique()} Grands Prix, {hist['season'].min()}–{hist['season'].max()}"),
        ("Dataset", "Class imbalance", f"{(len(hist) - wins) / wins:.1f} : 1", f"{wins} winners"),
        ("Classifier", "Holdout ROC-AUC", f"{ho['roc_auc']:.4f}", "Cost-sensitive XGBoost, 2022–2024"),
        ("Classifier", "Holdout PR-AUC", f"{ho['pr_auc']:.4f}", "Random baseline ≈ 0.05"),
        ("Classifier", "Race winner picked", f"{int(ho['top1_hits'])} / {int(ho['total_gps'])}", f"{ho['top1_winner_hit_pct']:.1f}% of unseen Grands Prix"),
        ("Classifier", "Gain over grid-only baseline", f"{sig['mean_delta']:+.4f} ROC-AUC", f"95% CI [{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}], race-level bootstrap"),
        ("Pattern mining", "Frequent itemsets", f"{bench['itemsets_count']}", "Identical in Apriori and FP-Growth"),
        ("Pattern mining", "Association rules", f"{bench['rules_count']:,}", f"min_support {bench['min_support']}, min_confidence {bench['min_confidence']}"),
        ("Clustering", "Driver-season profiles", f"{cm['n_profiles']}", f"{cm['n_features']} standardised features"),
        ("Clustering", "Champion", f"{cm['algorithm']} (k = {cm['k']})", f"silhouette {cm['silhouette']:.4f}, Davies-Bouldin {cm['davies_bouldin']:.4f}"),
    ], columns=["Area", "Metric", "Value", "Context"])

    t["DAX_Measures_Reference"] = pd.DataFrame([
        ("Grands Prix", "Grands Prix = DISTINCTCOUNT(Fact_Holdout_Predictions[race_id])"),
        ("Winners Picked", "Winners Picked = SUM(Fact_Holdout_Predictions[is_winner_hit])"),
        ("Winner Hit Rate %", "Winner Hit Rate % = DIVIDE([Winners Picked], [Grands Prix]) * 100"),
        ("Winner In Top 3 %", "Winner In Top 3 % = DIVIDE(SUM(Fact_Holdout_Predictions[winner_in_top3]), [Grands Prix]) * 100"),
        ("Pole To Win %", "Pole To Win % = DIVIDE(CALCULATE(SUM(Fact_Holdout_Predictions[target_is_win]), Fact_Holdout_Predictions[grid_position] = 1), CALCULATE(COUNTROWS(Fact_Holdout_Predictions), Fact_Holdout_Predictions[grid_position] = 1)) * 100"),
        ("Avg Win Probability", "Avg Win Probability = AVERAGE(Fact_Holdout_Predictions[norm_prob])"),
        ("Contender Seasons", "Contender Seasons = CALCULATE(COUNTROWS(CL_Driver_Season_Clusters), CL_Driver_Season_Clusters[cluster_name] = \"Title Contenders\")"),
    ], columns=["Measure", "DAX"])
    return t


SHEET_ORDER = ["Executive_KPI_Summary", "Fact_Holdout_Predictions", "Dim_Drivers", "Dim_Constructors", "Dim_Circuits", "Dim_Races",
               "ML_Model_Comparison", "ML_Temporal_Validation", "ML_Partition_Metrics", "ML_ROC_Curve", "ML_Feature_Importance",
               "ML_Association_Rules", "ML_Frequent_Itemsets", "ML_Support_Sweep",
               "CL_Driver_Season_Clusters", "CL_Cluster_Profiles", "CL_Algorithm_Comparison", "DAX_Measures_Reference"]

THEME = {
    "name": "ApexIQ Classification Sheet",
    "dataColors": ["#7B2CBF", "#1A9E55", "#C99700", "#15181D", "#9AA1AB", "#D50F1F", "#2F6FDB"],
    "background": "#FFFFFF",
    "foreground": "#15181D",
    "tableAccent": "#7B2CBF",
}

if __name__ == "__main__":
    tables = build_tables()
    assert set(tables) == set(SHEET_ORDER), set(tables) ^ set(SHEET_ORDER)
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            tables[name].to_excel(writer, sheet_name=name[:31], index=False)
    json.dump(THEME, open(OUTPUT_THEME, "w", encoding="utf-8"), indent=2)
    for name in SHEET_ORDER:
        print(f"  {name:<28} {len(tables[name]):>6,} rows")
    print(f"[+] {OUTPUT_XLSX} ({os.path.getsize(OUTPUT_XLSX) / 1048576:.1f} MB) and {OUTPUT_THEME}")
