"""
Automated Verification Suite for DASHBOARD 3 — Unsupervised Clustering
======================================================================
Validates:
1. Unsupervised dataset: no labels, no nulls, unique driver-season grain
2. Clustering comparison: >= 4 algorithms benchmarked, exactly one champion
3. Champion K-Means: 3 named clusters ordered best -> worst finish
4. Metrics: values within mathematical bounds; contenders align with title standings
"""

import os
import sys
import json
import unittest
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "09_unsupervised_dataset"))
from build_unsupervised_dataset import build_driver_season_profiles, CLUSTER_FEATURE_COLS


class TestF1ClusteringQA(unittest.TestCase):

    def test_01_unsupervised_dataset_has_no_labels_or_nulls(self):
        prof = build_driver_season_profiles()
        self.assertGreater(len(prof), 500)
        self.assertFalse(any(c.startswith("target_") for c in prof.columns))
        self.assertEqual(prof[CLUSTER_FEATURE_COLS].isna().sum().sum(), 0)
        self.assertFalse(prof.duplicated(["driver_id", "season"]).any())

    def test_02_comparison_has_at_least_4_algorithms_and_one_champion(self):
        res = pd.read_csv(os.path.join(ROOT, "10_clustering_comparison", "comparison_results.csv"))
        self.assertGreaterEqual(len(res), 4)
        self.assertEqual(int(res["champion"].sum()), 1)
        self.assertTrue(res["silhouette"].between(-1, 1).all())
        self.assertTrue((res["davies_bouldin"] >= 0).all())

    def test_03_champion_clusters_are_ordered_and_named(self):
        cent = pd.read_csv(os.path.join(ROOT, "11_clustering_algorithm", "cluster_profiles.csv"))
        self.assertEqual(list(cent["cluster_name"]), ["Title Contenders", "Midfield Regulars", "Backmarkers"])
        self.assertTrue(cent["avg_finish"].is_monotonic_increasing)
        cl = pd.read_csv(os.path.join(ROOT, "11_clustering_algorithm", "driver_season_clusters.csv"))
        self.assertEqual(int(cent["size"].sum()), len(cl))

    def test_05_kmedoids_finds_separated_groups_with_real_medoids(self):
        sys.path.insert(0, os.path.join(ROOT, "10_clustering_comparison"))
        from clustering_comparison import KMedoids
        import numpy as np
        rng = np.random.default_rng(1)
        X = np.vstack([rng.normal(c, 0.2, size=(30, 2)) for c in ((0, 0), (5, 5), (0, 5))])
        km = KMedoids(n_clusters=3, random_state=0)
        labels = km.fit_predict(X)
        self.assertEqual(len(set(labels)), 3)
        for g in range(3):  # each generated blob lands in exactly one cluster
            self.assertEqual(len(set(labels[g * 30:(g + 1) * 30])), 1)
        self.assertTrue(all(0 <= i < len(X) for i in km.medoid_indices_))  # medoids are actual rows

    def test_04_metrics_within_bounds_and_sane(self):
        with open(os.path.join(ROOT, "12_clustering_metrics", "clustering_metrics.json")) as f:
            m = json.load(f)
        self.assertTrue(0 < m["silhouette"] <= 1)
        self.assertGreater(m["calinski_harabasz"], 0)
        self.assertGreater(m["seed_stability_ari_mean"], 0.7)
        self.assertGreater(m["contenders_in_top3_standing_pct"], 50)


if __name__ == "__main__":
    unittest.main()
