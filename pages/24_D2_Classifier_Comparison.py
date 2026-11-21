import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header

apply_f1_theme()

MOD = os.path.join(ROOT, "05_algorithm_comparison")
res = pd.read_csv(os.path.join(MOD, "comparison_results.csv"))
res["model"] = res["algorithm"].str.replace(r"^\d+\.\s*", "", regex=True)
folds = pd.read_csv(os.path.join(MOD, "temporal_validation_results.csv"))
sig = pd.read_csv(os.path.join(MOD, "significance_test.csv")).iloc[0]
champ = res[res["algorithm"].str.contains("Champion")].iloc[0]

page_header('Dashboard 2', 'Supervised learning', 'Comparing seven classifiers',
            'Trained on 1994–2021 and tested on 68 unseen Grands Prix from 2022–2024, with expanding-window validation and a significance test.')

c1, c2, c3, c4 = st.columns(4)
c1.metric("Algorithms Compared", len(res))
c2.metric("Champion ROC-AUC", f"{champ['roc_auc']:.4f}", "XGBoost")
c3.metric("Expanding-Window Mean AUC", f"{folds['roc_auc'].mean():.4f}", f"{len(folds)} folds")
c4.metric("AUC Gain vs. Baseline", f"{sig['mean_delta']:+.4f}", f"95% CI [{sig['ci_low']:+.3f}, {sig['ci_high']:+.3f}]")

st.markdown("---")
t1, t2, t3, t4 = st.tabs(["Holdout Benchmark", "Expanding-Window Validation", "Significance Test", "Why These Models"])

with t1:
    metric = st.radio("Metric", ["roc_auc", "pr_auc", "balanced_acc_pct", "recall", "f1_score", "top1_winner_hit_pct", "top3_podium_hit_pct", "brier_score"], horizontal=True)
    order = res.sort_values(metric, ascending=(metric == "brier_score"))
    fig = px.bar(order, x=metric, y="model", orientation="h", title=f"{metric} on 2022–2024 holdout",
                 color=order["algorithm"].str.contains("Champion").map({True: "Champion", False: "Other"}),
                 color_discrete_map={"Champion": F1_RED, "Other": "#C3C8CF"})
    st.plotly_chart(get_plotly_theme(fig.update_yaxes(autorange="reversed")), width="stretch")
    st.dataframe(res.drop(columns=["model"]), width="stretch", hide_index=True)
    st.caption("Accuracy is misleading at 20:1 imbalance: the grid-only baseline scores 95% accuracy by predicting 'no win' for everyone (recall 0). "
               "We rank on ROC-AUC, PR-AUC, recall and race-level top-1 hit rate.")

with t2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=folds["test_season"], y=folds["roc_auc"], name="XGBoost", mode="lines+markers", line=dict(color=F1_RED, width=3)))
    fig.add_trace(go.Scatter(x=folds["test_season"], y=folds["baseline_roc_auc"], name="Grid-only baseline", mode="lines+markers", line=dict(color="#8B949E", dash="dash")))
    fig.update_layout(title="ROC-AUC per unseen season (train on all prior seasons)", xaxis_title="test season", yaxis_title="ROC-AUC")
    st.plotly_chart(get_plotly_theme(fig), width="stretch")
    st.dataframe(folds.drop(columns=["wilcoxon_w", "wilcoxon_p"]), width="stretch", hide_index=True)
    st.markdown("Each fold trains on **1994 → season−1** and tests on the next season only, which mimics real deployment. An assertion in "
                "`temporal_validation.py` fails the run if any training season ≥ test season.")

with t3:
    st.markdown(f"""
    **Question:** is XGBoost genuinely better than the grid-only baseline, or did it get lucky on 68 races?

    **1. Race-level paired bootstrap (primary):** resample the 68 holdout Grands Prix with replacement 1,000 times and recompute both models' ROC-AUC each time.
    - Mean gain: **{sig['mean_delta']:+.4f}** · 95% CI **[{sig['ci_low']:+.4f}, {sig['ci_high']:+.4f}]** · one-sided p = **{sig['p_value']:.4f}**
    - The CI excludes 0, so the improvement is **statistically significant**.

    **2. Wilcoxon signed-rank on the 6 expanding-window folds:** W = {folds['wilcoxon_w'].iat[0]:.0f}, p = {folds['wilcoxon_p'].iat[0]:.4f}.
    - XGBoost wins 4 of 6 folds. With only 6 pairs the smallest achievable p is 0.016, so this test has low power; the bootstrap over 1,359 entries is the stronger evidence.
    """)

with t4:
    st.markdown("""
    | Model | Inductive bias | Role |
    |---|---|---|
    | Dummy (uniform) | None | Floor: any real model must beat it |
    | Logistic Regression (grid only) | Linear in one feature | "Pole sitter wins" domain baseline |
    | Decision Tree (depth 5) | Axis-aligned splits | Interpretable, high variance |
    | Random Forest | Bagged trees | Variance reduction |
    | Gradient Boosting (GBDT) | Sequential residual fitting | Strong tabular learner |
    | LightGBM | Leaf-wise histogram boosting | Fast boosting |
    | **XGBoost** | Regularised 2nd-order boosting + `scale_pos_weight` | **Champion**: best ROC-AUC and top-1 hit rate |
    """)
