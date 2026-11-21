"""
Regenerates every number shown in the dashboards, in dependency order.
Usage: .venv/bin/python run_all_modules.py
"""

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = [
    "03_class_labels/label_generation.py",
    "04_pattern_mining/fp_growth_analysis.py",
    "05_algorithm_comparison/train_comparison.py",
    "05_algorithm_comparison/temporal_validation.py",
    "06_classification_algorithm/improved_classifier.py",
    "07_innovation/baseline_vs_improved.py",
    "08_performance_metrics/calculate_metrics.py",
    "09_unsupervised_dataset/build_unsupervised_dataset.py",
    "10_clustering_comparison/clustering_comparison.py",
    "11_clustering_algorithm/kmeans_clustering.py",
    "12_clustering_metrics/clustering_metrics.py",
    "12_clustering_metrics/cluster_feature_experiment.py",
]

if __name__ == "__main__":
    for s in SCRIPTS:
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, os.path.join(ROOT, s)], cwd=ROOT, capture_output=True, text=True)
        status = "OK  " if r.returncode == 0 else "FAIL"
        print(f"[{status}] {s:<55} {time.perf_counter() - t0:6.1f}s")
        if r.returncode != 0:
            print(r.stderr[-2000:])
            sys.exit(1)
    print("\nAll modules regenerated. Restart the Streamlit app to see the new numbers.")
