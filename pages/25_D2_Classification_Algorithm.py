import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "06_classification_algorithm"))
import time
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from feature_engineering import ENGINEERED_FEATURE_COLS as FEATURES
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header, SEQ_SCALE, pretty

apply_f1_theme()

pred = pd.read_csv(os.path.join(ROOT, "06_classification_algorithm", "holdout_predictions.csv"))
imp = pd.read_csv(os.path.join(ROOT, "06_classification_algorithm", "feature_importance.csv"))
parts = pd.read_csv(os.path.join(ROOT, "08_performance_metrics", "partition_metrics.csv"))
innov = pd.read_csv(os.path.join(ROOT, "07_innovation", "innovation_results.csv"))
ho = parts[parts["partition"].str.startswith("Combined")].iloc[0]

page_header('Dashboard 2', 'Supervised learning', 'Classification algorithm: cost-sensitive XGBoost',
            "Predicts each driver's chance of winning. The probabilities in every race add up to 100%.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Holdout ROC-AUC", f"{ho['roc_auc']:.4f}")
c2.metric("Holdout PR-AUC", f"{ho['pr_auc']:.4f}", "base rate ≈ 0.05", delta_color="off")
c3.metric("Winner Recall", f"{ho['recall_class_1'] * 100:.1f}%")
c4.metric("Race Winner Picked (Top-1)", f"{ho['top1_winner_hit_pct']:.1f}%", f"{int(ho['top1_hits'])}/{int(ho['total_gps'])} GPs")

st.markdown("---")
t1, t1b, t2, t3, t4, t5 = st.tabs(["How It Works", "Preprocessing & Training", "Curves & Threshold", "Train / Val / Test", "Innovation", "Race Explorer"])


@st.cache_resource
def train_champion():
    """Fits the champion with its exact settings (same as 06_classification_algorithm/improved_classifier.py)."""
    df = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
    tr, te = df["season"] < 2022, df["season"] >= 2022
    X_tr, X_te = df.loc[tr, FEATURES].fillna(0), df.loc[te, FEATURES].fillna(0)
    y_tr, y_te = df.loc[tr, "target_is_win"].astype(int), df.loc[te, "target_is_win"].astype(int)
    model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, scale_pos_weight=15, subsample=0.85,
                              colsample_bytree=0.85, random_state=42, eval_metric="logloss")
    t0 = time.perf_counter()
    model.fit(X_tr, y_tr, eval_set=[(X_tr, y_tr), (X_te, y_te)], verbose=False)
    secs = time.perf_counter() - t0
    auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
    return model, df, int(df[FEATURES].isna().sum().sum()), int(tr.sum()), int(te.sum()), secs, auc


with t1b:
    model, full, n_missing, n_tr, n_te, fit_secs, auc_live = train_champion()
    st.markdown("#### Preprocessing steps")
    st.dataframe(pd.DataFrame([
        ("1. Load", f"{len(full):,} driver-race entries × {len(full.columns)} columns, 1994–2024"),
        ("2. Select inputs", f"Keep the {len(FEATURES)} pre-race features; drop the 14 identifiers (names, ids, dates) so the model cannot memorise who is famous"),
        ("3. Prevent leakage", "Every feature uses only earlier races (rolling windows shifted by one race); nothing from the race itself"),
        ("4. Missing values", f"{n_missing} missing cells in the features; any gap would be filled with 0 (no history yet)"),
        ("5. Scaling", "None needed: trees split on thresholds, so the units of a feature do not matter"),
        ("6. Split", f"Chronological: train 1994–2021 ({n_tr:,} entries), test 2022–2024 ({n_te:,} entries)"),
        ("7. Class imbalance", "About 20 non-winners per winner: scale_pos_weight = 15 makes a missed winner cost 15× more"),
    ], columns=["Step", "What is done"]), width="stretch")
    st.markdown("#### Training, live")
    a, b, c = st.columns(3)
    a.metric("Trees built", model.n_estimators, "depth 4 each", delta_color="off")
    b.metric("Training time", f"{fit_secs:.2f} s", f"{n_tr:,} entries", delta_color="off")
    c.metric("Test ROC-AUC", f"{auc_live:.4f}", "matches the saved model" if abs(auc_live - ho["roc_auc"]) < 5e-4
             else f"saved model {ho['roc_auc']:.4f} (XGBoost {xgb.__version__} here)",
             delta_color="off")
    ev = model.evals_result()
    curve = pd.DataFrame({"Tree": range(1, len(ev["validation_0"]["logloss"]) + 1),
                          "Training set": ev["validation_0"]["logloss"], "Test set (unseen)": ev["validation_1"]["logloss"]})
    st.plotly_chart(get_plotly_theme(px.line(curve, x="Tree", y=["Training set", "Test set (unseen)"],
                                             color_discrete_sequence=[F1_RED, "#9AA1AB"],
                                             title="Log-loss as trees are added: both fall together, so the model learns without overfitting")
                                     .update_layout(yaxis_title="Log-loss (lower is better)", legend_title_text="")), width="stretch")
    st.code("""model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05,
                      scale_pos_weight=15, subsample=0.85, colsample_bytree=0.85, random_state=42)
model.fit(X_train, y_train)                    # 1994–2021
p = model.predict_proba(X_test)[:, 1]          # 2022–2024, one probability per driver
p_race = softmax(log(p) / 0.8) within each race  # probabilities in a race add up to 1""", language="python")
    st.caption("This tab retrains the model each time the app starts, with the same settings and data as the saved champion, "
               "so the training is demonstrated rather than loaded.")

with t1:
    a, b = st.columns([3, 2])
    a.markdown(r"""
    **1. Cost-sensitive gradient boosting**: 100 trees, depth 4, learning rate 0.05, subsample/colsample 0.85.
    `scale_pos_weight = 15` makes a missed winner cost 15× more than a false alarm:

    $\mathcal{L} = -\sum_i \big[15\,y_i \log \hat p_i + (1-y_i)\log(1-\hat p_i)\big] + \Omega(\text{trees})$

    **2. Race-level softmax** (temperature 0.8) turns independent per-driver probabilities into one distribution per Grand Prix:

    $P(\text{win}_i \mid \text{race}) = \dfrac{\exp(\log \hat p_i / T)}{\sum_{k \in \text{race}} \exp(\log \hat p_k / T)}$, so that $\sum_i P = 1$

    **3. Prediction** = the driver with the highest race probability.
    """)
    b.plotly_chart(get_plotly_theme(px.bar(imp.head(10), x="importance", y="feature", orientation="h", color_discrete_sequence=[F1_RED],
                                           title="Top-10 feature importance (gain)").update_yaxes(autorange="reversed")), width="stretch")

with t2:
    y, p = pred["target_is_win"], pred["raw_prob"]
    fpr, tpr, _ = roc_curve(y, p)
    prec, rec, _ = precision_recall_curve(y, p)
    a, b = st.columns(2)
    a.plotly_chart(get_plotly_theme(go.Figure([go.Scatter(x=fpr, y=tpr, name="XGBoost", line=dict(color=F1_RED)),
                                               go.Scatter(x=[0, 1], y=[0, 1], name="random", line=dict(dash="dash", color="#8B949E"))])
                                    .update_layout(title=f"ROC curve (AUC {ho['roc_auc']:.4f})", xaxis_title="FPR", yaxis_title="TPR")), width="stretch")
    b.plotly_chart(get_plotly_theme(go.Figure([go.Scatter(x=rec, y=prec, line=dict(color=F1_RED))])
                                    .update_layout(title=f"Precision-Recall curve (AP {ho['pr_auc']:.4f})", xaxis_title="Recall", yaxis_title="Precision")), width="stretch")
    thr = st.slider("Decision threshold on raw P(win)", 0.05, 0.95, 0.50, 0.05)
    tn, fp, fn, tp = confusion_matrix(y, (p >= thr).astype(int)).ravel()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precision", f"{tp / max(tp + fp, 1):.3f}")
    m2.metric("Recall", f"{tp / max(tp + fn, 1):.3f}")
    m3.metric("F1", f"{2 * tp / max(2 * tp + fp + fn, 1):.3f}")
    m4.metric("Accuracy", f"{(tp + tn) / len(y) * 100:.2f}%")
    st.plotly_chart(get_plotly_theme(px.imshow([[tn, fp], [fn, tp]], text_auto=True, color_continuous_scale=SEQ_SCALE,
                                               x=["Pred: non-winner", "Pred: winner"], y=["Actual: non-winner", "Actual: winner"],
                                               title=f"Confusion matrix @ threshold {thr:.2f}")), width="stretch")
    st.markdown("#### Reading the metrics at this threshold")
    n_all = int(tn + fp + fn + tp)
    st.dataframe(pd.DataFrame([
        ("Accuracy", f"{(tp + tn) / n_all:.1%}", "(TP + TN) / all",
         f"Share of all {n_all:,} driver-races labelled correctly. Misleading here: calling everyone a non-winner already scores {(tn + fp) / n_all:.0%}."),
        ("Precision", f"{tp / max(tp + fp, 1):.1%}", "TP / (TP + FP)",
         f"Of the {int(tp + fp)} drivers flagged as likely winners, {int(tp)} won. Several real contenders are flagged per race but only one can win."),
        ("Recall", f"{tp / max(tp + fn, 1):.1%}", "TP / (TP + FN)",
         f"Of the {int(tp + fn)} actual winners, {int(tp)} were flagged; only {int(fn)} winners were missed. This is what the 15× cost weight protects."),
        ("F1-score", f"{2 * tp / max(2 * tp + fp + fn, 1):.3f}", "2·P·R / (P + R)", "Balances precision and recall in one number."),
        ("Confusion matrix", f"TN {int(tn):,} · FP {int(fp)} · FN {int(fn)} · TP {int(tp)}", "counts above",
         "Missed winners (FN) are the costly mistake; false alarms (FP) are cheap because the race softmax then picks one driver."),
    ], columns=["Metric", "Value", "Formula", "What it means here"]), width="stretch")
    st.caption("Move the threshold: a lower threshold catches more winners (recall up) but flags more non-winners (precision down). "
               "The race-level top-1 rate (58.8%) does not depend on the threshold, because it simply takes the highest probability in each race.")

with t3:
    st.dataframe(parts, width="stretch", hide_index=True)
    long = parts.melt(id_vars="partition", value_vars=["roc_auc", "pr_auc", "recall_class_1", "brier_score"])
    st.plotly_chart(get_plotly_theme(px.bar(long, x="variable", y="value", color="partition", barmode="group",
                                            title="Train vs. validation vs. test: small gap = little overfitting")), width="stretch")

with t4:
    st.markdown("**Baseline:** logistic regression on grid position only. **Improved:** 16 leakage-safe features (rolling form, circuit affinity, teammate delta) + cost-sensitive XGBoost + race softmax.")
    st.dataframe(innov, width="stretch", hide_index=True)
    show = innov[innov["metric"].isin(["ROC-AUC", "PR-AUC", "Winner Recall", "Winner F1"])].melt(id_vars="metric", value_vars=["baseline", "improved"])
    st.plotly_chart(get_plotly_theme(px.bar(show, x="metric", y="value", color="variable", barmode="group",
                                            color_discrete_map={"baseline": "#8B949E", "improved": F1_RED})), width="stretch")

with t5:
    races = pred.drop_duplicates("race_id").sort_values(["season", "round"])
    rid = st.selectbox("Grand Prix", races["race_id"], format_func=lambda r: f"{int(races.loc[races.race_id == r, 'season'].iat[0])} {races.loc[races.race_id == r, 'race_name'].iat[0]}",
                       index=int(np.argmax(races["race_name"].str.contains("British") & (races["season"] == 2024))))
    g = pred[pred["race_id"] == rid].sort_values("norm_prob", ascending=False)
    g["result"] = np.where(g["target_is_win"] == 1, "🏆 Actual winner", "")
    st.plotly_chart(get_plotly_theme(px.bar(g.head(10), x="norm_prob", y="driver_name", orientation="h", text=g.head(10)["result"],
                                            color=g.head(10)["target_is_win"].map({1: "Winner", 0: "Other"}),
                                            color_discrete_map={"Winner": F1_RED, "Other": "#C3C8CF"},
                                            title=f"Predicted win probability (sum = {g['norm_prob'].sum():.2f})")
                                     .update_yaxes(categoryorder="array", categoryarray=g.head(10)["driver_name"].tolist(), autorange="reversed")
                                     .update_layout(yaxis_title=None)),
                    width="stretch")
    st.dataframe(g[["driver_name", "constructor_name", "grid_position", "norm_prob", "target_finish_position"]].round(4), width="stretch", hide_index=True)

    st.markdown("#### Why the model ranked them this way")
    who = st.selectbox("Driver", g["driver_name"].head(10).tolist())
    model, full = train_champion()[:2]
    row = full[(full["race_id"] == rid) & (full["driver_name"] == who)]
    contrib = model.get_booster().predict(xgb.DMatrix(row[FEATURES].fillna(0)), pred_contribs=True)[0]
    expl = pd.DataFrame({"feature": FEATURES, "value": row[FEATURES].iloc[0].values, "push": contrib[:-1]})
    expl = expl.reindex(expl["push"].abs().sort_values(ascending=False).index).head(8)
    expl["label"] = [f"{pretty(f)} = {v:g}" for f, v in zip(expl["feature"], expl["value"].round(2))]
    expl["direction"] = np.where(expl["push"] > 0, "Raises win chance", "Lowers win chance")
    st.plotly_chart(get_plotly_theme(px.bar(expl, x="push", y="label", orientation="h", color="direction",
                                            color_discrete_map={"Raises win chance": F1_RED, "Lowers win chance": "#9AA1AB"},
                                            title=f"{who}: what moved the prediction (log-odds contribution per feature)")
                                     .update_yaxes(autorange="reversed").update_layout(yaxis_title=None, xaxis_title="Push on log-odds", legend_title_text="")),
                    width="stretch")
    top = expl.iloc[0]
    st.info(f"Every driver starts from the same base log-odds ({contrib[-1]:+.2f}); each feature then pushes it up or down. "
            f"For {who} the biggest push came from **{pretty(top['feature']).lower()} = {top['value']:g}** "
            f"({top['push']:+.2f}). The pushes add up to the model's score, which the race softmax turns into the win probability above.")
