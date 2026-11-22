"""
Race predictor engine (06_classification_algorithm/future_race.py): the rules behind every dashboard filter.
"""

import os
import sys
import unittest

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "06_classification_algorithm"))
import future_race as fr  # noqa: E402


class TestRacePredictor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.store, cls.dob = fr.load_history(include_recent=False)
        cls.history, _ = fr.load_history()
        cls.history = fr.add_recent_features(cls.history, cls.dob)
        cls.model = fr.full_history_model(cls.history)
        cls.lineup = fr.latest_lineup(cls.history)
        cls.lineup["grid_position"] = fr.projected_grid(cls.history, cls.lineup)
        cls.race = fr.upcoming_calendar().iloc[0]

    def run_forecast(self, lineup=None, overrides=None):
        return fr.forecast(self.history, self.dob, self.model, self.lineup if lineup is None else lineup,
                           self.race["circuit_id"], self.race["race_date"], overrides)

    def test_feature_rebuild_matches_the_feature_store(self):
        worst = fr.self_check(self.store, self.dob)
        self.assertTrue(all(v <= 0.011 for v in worst.values()), worst)

    def test_probabilities_sum_to_100_and_are_deterministic(self):
        a, b = self.run_forecast(), self.run_forecast()
        self.assertAlmostEqual(a["win_probability"].sum(), 100, places=4)
        np.testing.assert_allclose(a["win_probability"], b["win_probability"])

    def test_grid_moves_keep_a_valid_grid(self):
        driver = self.lineup["driver_id"].iloc[-1]
        moved = fr.move_to_grid(self.lineup, driver, 1)
        self.assertEqual(int(moved.loc[moved["driver_id"] == driver, "grid_position"].iat[0]), 1)
        self.assertEqual(sorted(moved["grid_position"]), sorted(self.lineup["grid_position"]))

    def test_pole_raises_a_drivers_chance(self):
        driver = self.lineup.sort_values("grid_position")["driver_id"].iloc[9]  # starts P10 in the projection
        before = self.run_forecast().set_index("driver_id").at[driver, "win_probability"]
        after = self.run_forecast(fr.move_to_grid(self.lineup, driver, 1)).set_index("driver_id").at[driver, "win_probability"]
        self.assertGreater(after, before)

    def test_team_move_uses_the_new_teams_form(self):
        driver = self.lineup["driver_id"].iloc[0]
        other = self.lineup[self.lineup["constructor_id"] != self.lineup["constructor_id"].iloc[0]].iloc[0]
        moved = fr.move_to_team(self.lineup, driver, other["constructor_id"], other["constructor_name"])
        f = self.run_forecast(moved).set_index("driver_id")
        teammate = f[(f["constructor_id"] == other["constructor_id"]) & (f.index != driver)].iloc[0]
        self.assertEqual(f.at[driver, "constructor_rolling_points_10"], teammate["constructor_rolling_points_10"])

    def test_form_override_updates_the_derived_feature(self):
        driver = self.lineup["driver_id"].iloc[0]
        f = self.run_forecast(overrides={driver: {"driver_rolling_finish_5": 1.0}}).set_index("driver_id")
        self.assertEqual(f.at[driver, "driver_rolling_finish_5"], 1.0)
        self.assertEqual(f.at[driver, "grid_vs_form_gap"], f.at[driver, "grid_position"] - 1.0)


if __name__ == "__main__":
    unittest.main()
