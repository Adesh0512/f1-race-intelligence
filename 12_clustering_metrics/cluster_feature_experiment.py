"""
Clusters -> Classifier Experiment (Dashboard 2 <-> Dashboard 3 bridge)
=====================================================================
Does knowing a driver's performance TIER (from unsupervised K-Means) help the
supervised race-winner classifier?

Leakage-safe design:
- K-Means (k = 3) is fitted ONLY on driver-season profiles from 1994–2021 (training era).
- Each race entry gets the tier of the driver's PREVIOUS season (season - 1), assigned
  with that frozen model. Rookies with no previous season get tier = -1 (unknown).
- Same XGBoost config, same chronological split (train 1994–2021, test 2022–2024).

Output: 12_clustering_metrics/cluster_feature_experiment.csv
"""

import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "..", "09_unsupervised_dataset"))
sys.path.append(os.path.join(BASE_DIR, "..", "06_classification_algorithm"))
from build_unsupervised_dataset import build_driver_season_profiles, CLUSTER_FEATURE_COLS
from feature_engineering import load_or_verify_features, ENGINEERED_FEATURE_COLS

SPLIT = 2022


def previous_season_tiers():
    prof = build_driver_season_profiles()
    train = prof[prof["season"] < SPLIT]
    scaler = StandardScaler().fit(train[CLUSTER_FEATURE_COLS])
    km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(scaler.transform(train[CLUSTER_FEATURE_COLS]))
    # tier 0 = best centroid mean finish
    order = np.argsort(scaler.inverse_transform(km.cluster_centers_)[:, CLUSTER_FEATURE_COLS.index("avg_finish")])
    remap = {old: new for new, old in enumerate(order)}
    prof["tier"] = [remap[c] for c in km.predict(scaler.transform(prof[CLUSTER_FEATURE_COLS]))]
    # this season's tier becomes a feature for NEXT season's races
    return prof[["driver_id", "season", "tier"]].assign(season=lambda d: d["season"] + 1).rename(columns={"tier": "prev_season_tier"})


def evaluate(df, feats):
    tr, te = df[df["season"] < SPLIT], df[df["season"] >= SPLIT].copy()
    clf = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15,
                            subsample=0.85, colsample_bytree=0.85, random_state=42, eval_metric="logloss")
    clf.fit(tr[feats].fillna(0), tr["target_is_win"])
    te["p"] = clf.predict_proba(te[feats].fillna(0))[:, 1]
    top1 = te.loc[te.groupby("race_id")["p"].idxmax(), "target_is_win"].mean() * 100
    return {"roc_auc": roc_auc_score(te["target_is_win"], te["p"]),
            "pr_auc": average_precision_score(te["target_is_win"], te["p"]),
            "top1_winner_hit_pct": top1}


if __name__ == "__main__":
    print("=" * 90)
    print("   DASHBOARD 2 <-> 3 BRIDGE: DOES THE CLUSTER TIER IMPROVE THE WINNER CLASSIFIER?")
    print("=" * 90)
    df = load_or_verify_features().merge(previous_season_tiers(), on=["driver_id", "season"], how="left")
    df["prev_season_tier"] = df["prev_season_tier"].fillna(-1)
    for t in range(3):
        df[f"prev_tier_{t}"] = (df["prev_season_tier"] == t).astype(int)
    tier_feats = ["prev_tier_0", "prev_tier_1", "prev_tier_2"]

    base = evaluate(df, ENGINEERED_FEATURE_COLS)
    plus = evaluate(df, ENGINEERED_FEATURE_COLS + tier_feats)
    only = evaluate(df, ["grid_position"] + tier_feats)
    grid = evaluate(df, ["grid_position"])

    res = pd.DataFrame([
        {"model": "Grid only", **grid},
        {"model": "Grid + previous-season tier", **only},
        {"model": "16 features (champion)", **base},
        {"model": "16 features + previous-season tier", **plus},
    ]).round(4)
    res.to_csv(os.path.join(BASE_DIR, "cluster_feature_experiment.csv"), index=False)
    print(res.to_string(index=False))
    print(f"\n[+] Rookie entries with no previous-season tier: {(df['prev_season_tier'] == -1).mean() * 100:.1f}%")
    print("[+] Saved: cluster_feature_experiment.csv")
