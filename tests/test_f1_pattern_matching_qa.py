"""
Automated Verification Suite for PATTERN MATCHING Mining Engine (Parameter 04)
==============================================================================
Validates the Module 04 deliverable against its documented parameters
(min_support = 0.02, min_confidence = 0.25, 414 itemsets, 1,393 rules):
1. Script, rules CSV and report exist
2. Apriori and FP-Growth produce identical frequent itemsets on the race transactions
3. Association rules respect the support / confidence thresholds and have valid lift
4. High-lift outcome rules exist for Winner, Podium, Points and DNF
"""

import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import find, ROOT
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, fpgrowth

sys.path.insert(0, os.path.join(ROOT, "04_pattern_mining"))
from apriori_analysis import build_race_transactions

MIN_SUPPORT = 0.02
MIN_CONFIDENCE = 0.25


class TestF1PatternMatchingQAEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rules_csv = find("04_pattern_mining/association_rules.csv")
        cls.script_path = find("04_pattern_mining/fp_growth_analysis.py")
        cls.doc_path = find("04_pattern_mining/pattern_mining_report.md")
        cls.df_rules = pd.read_csv(cls.rules_csv)

    def test_01_pattern_mining_files_presence(self):
        """Verify pattern mining script, rules CSV and report exist."""
        for path in [self.script_path, self.rules_csv, self.doc_path]:
            self.assertTrue(os.path.exists(path), f"{path} missing")

    def test_02_apriori_fpgrowth_equivalence(self):
        """Verify Apriori and FP-Growth discover the exact same 414 frequent itemsets."""
        df = pd.read_csv(find("data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
        tx = build_race_transactions(df)
        te = TransactionEncoder()
        encoded = pd.DataFrame(te.fit(tx).transform(tx), columns=te.columns_)
        ap = apriori(encoded, min_support=MIN_SUPPORT, use_colnames=True)
        fp = fpgrowth(encoded, min_support=MIN_SUPPORT, use_colnames=True)
        self.assertEqual(set(ap["itemsets"]), set(fp["itemsets"]))
        self.assertEqual(len(fp), 414)
        self.assertTrue((fp["support"] >= MIN_SUPPORT).all())

    def test_03_association_rules_volume_and_metrics_validity(self):
        """Verify 1,393 rules within the documented support / confidence thresholds."""
        r = self.df_rules
        self.assertEqual(len(r), 1393)
        self.assertTrue((r["support"] >= MIN_SUPPORT).all(), "Support must be >= min_support (0.02)")
        self.assertTrue(r["confidence"].between(MIN_CONFIDENCE, 1.0).all(), "Confidence must be in [0.25, 1.0]")
        self.assertTrue((r["lift"] > 0).all(), "Lift must be strictly positive")

    def test_04_high_lift_winner_association_rules(self):
        """Verify high-lift rules predicting race winners (documented lift 17.19x)."""
        winner_rules = self.df_rules[self.df_rules["consequents"].str.contains("Outcome_Winner")]
        self.assertGreater(len(winner_rules), 0, "No winner association rules found")
        self.assertGreater(winner_rules["lift"].max(), 5.0)

    def test_05_high_lift_podium_and_points_rules(self):
        """Verify rules exist for podiums and points scorers."""
        self.assertGreater(self.df_rules["consequents"].str.contains("Outcome_Podium").sum(), 0, "No podium rules found")
        self.assertGreater(self.df_rules["consequents"].str.contains("Outcome_Points").sum(), 0, "No points rules found")

    def test_06_dnf_risk_association_rules(self):
        """Verify DNF rules exist and show positive association (lift > 1)."""
        dnf_rules = self.df_rules[self.df_rules["consequents"].str.contains("Outcome_DNF")]
        self.assertGreater(len(dnf_rules), 0, "No DNF risk association rules found")
        self.assertGreater(dnf_rules["lift"].max(), 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
