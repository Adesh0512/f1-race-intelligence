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
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED

apply_f1_theme()

pred = pd.read_csv(os.path.join(ROOT, "06_classification_algorithm", "holdout_predictions.csv"))
imp = pd.read_csv(os.path.join(ROOT, "06_classification_algorithm", "feature_importance.csv"))
parts = pd.read_csv(os.path.join(ROOT, "08_performance_metrics", "partition_metrics.csv"))
innov = pd.read_csv(os.path.join(ROOT, "07_innovation", "innovation_results.csv"))
ho = parts[parts["partition"].str.startswith("Combined")].iloc[0]

st.title("🏎️ Dashboard 2 · Classification Algorithm: Cost-Sensitive XGBoost + Race Softmax")
st.markdown("### Predicts P(win) for every driver on the grid · probabilities sum to 100% per race")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Holdout ROC-AUC", f"{ho['roc_auc']:.4f}")
c2.metric("Holdout PR-AUC", f"{ho['pr_auc']:.4f}", "base rate ≈ 0.05", delta_color="off")
c3.metric("Winner Recall", f"{ho['recall_class_1'] * 100:.1f}%")
c4.metric("Race Winner Picked (Top-1)", f"{ho['top1_winner_hit_pct']:.1f}%", f"{int(ho['top1_hits'])}/{int(ho['total_gps'])} GPs")

st.markdown("---")
t1, t2, t3, t4, t5 = st.tabs(["⚙️ How It Works", "📈 Curves & Threshold", "🧮 Train / Val / Test", "💡 Innovation", "🏁 Race Explorer"])

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
    st.plotly_chart(get_plotly_theme(px.imshow([[tn, fp], [fn, tp]], text_auto=True, color_continuous_scale="Reds",
                                               x=["Pred: non-winner", "Pred: winner"], y=["Actual: non-winner", "Actual: winner"],
                                               title=f"Confusion matrix @ threshold {thr:.2f}")), width="stretch")

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
                                            color_discrete_map={"Winner": F1_RED, "Other": "#30363D"},
                                            title=f"Predicted win probability (sum = {g['norm_prob'].sum():.2f})").update_yaxes(autorange="reversed")),
                    width="stretch")
    st.dataframe(g[["driver_name", "constructor_name", "grid_position", "norm_prob", "target_finish_position"]].round(4), width="stretch", hide_index=True)
