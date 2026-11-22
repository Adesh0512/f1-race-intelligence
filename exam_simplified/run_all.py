# ============================================================
# FILE: run_all.py
# REAL MODULE: run_all_modules.py
# WHAT IT DOES: runs every simplified module in the right order and prints its output.
# Run with:   .venv/bin/python exam_simplified/run_all.py
# ============================================================

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    "01_data_warehouse/build_star_schema.py",
    "01_data_warehouse/olap_queries.py",
    "02_snowflake/deploy_to_snowflake.py",
    "03_supervised_dataset/class_labels.py",
    "03_supervised_dataset/features_and_split.py",
    "04_pattern_mining/apriori_vs_fpgrowth.py",
    "05_classifier_comparison/compare_classifiers.py",
    "06_champion_model/xgboost_champion.py",
    "07_clustering/driver_season_profiles.py",
    "07_clustering/compare_clustering.py",
    "07_clustering/kmeans_tiers.py",
    "08_race_forecast/forecast_next_race.py",
]

for step in STEPS:
    print("\n" + "#" * 70 + "\n#  " + step + "\n" + "#" * 70)
    result = subprocess.run([sys.executable, os.path.join(HERE, step)])
    if result.returncode != 0:
        print("Stopped: this step failed ->", step)
        sys.exit(1)
print("\nAll steps finished. For the dashboard run: streamlit run exam_simplified/09_dashboard/mini_dashboard.py")
