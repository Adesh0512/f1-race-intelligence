import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header, pretty

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
t0, t1, t2, t3, t4 = st.tabs(["Setup & Findings", "Holdout Benchmark", "Expanding-Window Validation", "Significance Test", "Why These Models"])


@st.cache_data
def split_sizes():
    d = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), usecols=["season", "race_id"])
    part = lambda m: (f"{m.sum():,}", d.loc[m, "race_id"].nunique())
    return part(d["season"] <= 2021), part(d["season"] >= 2022)


with t0:
    (tr_n, tr_gp), (te_n, te_gp) = split_sizes()
    st.markdown("#### Training and testing strategy")
    st.dataframe(pd.DataFrame([("Training set", "1994–2021", tr_n, tr_gp, "Every model is fitted here"),
                               ("Test set (holdout)", "2022–2024", te_n, te_gp, "Never seen during training; all results below")],
                              columns=["Partition", "Seasons", "Entries", "Grands Prix", "Use"]), width="stretch")
    st.markdown("The split is **chronological, not random**: the model is always tested on races that happen after everything it "
                "learned from, exactly as it would be used on a future race. Random splitting would let a 2024 race help predict "
                "a 2019 race. Validation is repeated with an **expanding window** (6 folds) and checked with a **significance test**.")
    st.markdown("#### Fair comparison: what every model shares")
    st.dataframe(pd.DataFrame([
        ("Data", "The same 12,358 entries and the same train/test split"),
        ("Inputs", "The same 16 pre-race features (the grid-only baseline deliberately sees only grid position)"),
        ("Metrics", "The same 10 metrics on the same test set, including race-level top-1: the highest-probability driver in each race"),
        ("Reproducibility", "random_state = 42 for every model"),
        ("Class imbalance (20 : 1)", "Each model uses its own built-in weighting where it has one"),
    ], columns=["Kept identical", "How"]), width="stretch")
    st.dataframe(pd.DataFrame([
        ("Dummy Classifier", "uniform random guess", "—"),
        ("Logistic Regression (grid only)", "max_iter = 300", "—"),
        ("Decision Tree", "max_depth = 5", "class_weight = balanced"),
        ("Random Forest", "150 trees, max_depth = 6", "class_weight = balanced"),
        ("Gradient Boosting (GBDT)", "100 trees, depth 3, learning rate 0.05", "—"),
        ("LightGBM", "100 trees, depth 4, learning rate 0.05", "is_unbalance = True"),
        ("XGBoost (Champion)", "100 trees, depth 4, learning rate 0.05, subsample 0.85", "scale_pos_weight = 15"),
    ], columns=["Model", "Settings", "Imbalance handling"]), width="stretch")
    best = lambda c: res.loc[res[c].idxmax()]
    base = res[res["algorithm"].str.contains("Grid Only")].iloc[0]
    st.markdown("#### What the comparison shows")
    st.markdown(f"""
    1. **XGBoost is the strongest overall:** best ROC-AUC ({champ['roc_auc']:.4f}), best PR-AUC ({champ['pr_auc']:.4f}) and it picks the
       race winner in **{int(champ['top1_hits'])} of {te_gp}** Grands Prix, against {int(base['top1_hits'])} for "back the pole-sitter".
    2. **Accuracy is misleading here:** the grid-only baseline scores {base['accuracy_pct']:.1f}% accuracy with recall {base['recall']:.0f},
       because predicting "no win" for everyone is right 95% of the time. That is why the ranking uses ROC-AUC, PR-AUC, recall and top-1.
    3. **Boosting beats single trees:** the Decision Tree's ROC-AUC is {best('roc_auc')['roc_auc'] - res.loc[res['model'] == 'Decision Tree', 'roc_auc'].iat[0]:.3f}
       lower than the best model; ensembles (Random Forest, GBDT, LightGBM, XGBoost) all reach about 0.96.
    4. **Highest recall is not the best model:** {best('recall')['model']} flags the most winners (recall {best('recall')['recall']:.3f})
       but ranks them less precisely, so it picks fewer actual winners.
    5. **The gain is real:** across 1,000 race-level resamples XGBoost's ROC-AUC beats the baseline by {sig['mean_delta']:+.3f}
       (95% CI {sig['ci_low']:+.3f} to {sig['ci_high']:+.3f}), which excludes zero.
    """)

with t1:
    metric = st.radio("Metric", ["roc_auc", "pr_auc", "balanced_acc_pct", "recall", "f1_score", "top1_winner_hit_pct", "top3_podium_hit_pct", "brier_score"], horizontal=True, format_func=pretty)
    order = res.sort_values(metric, ascending=(metric == "brier_score"))
    fig = px.bar(order, x=metric, y="model", orientation="h", title=f"{pretty(metric)} on 2022–2024 holdout",
                 color=order["algorithm"].str.contains("Champion").map({True: "Champion", False: "Other"}),
                 color_discrete_map={"Champion": F1_RED, "Other": "#C3C8CF"}, text_auto=".3~f")
    lo, hi = order[metric].min(), order[metric].max()
    fig.update_xaxes(range=[max(0, lo - 0.15 * (hi - lo) - 0.02 * hi), hi * 1.06])  # zoom so small gaps between models are visible
    fig.update_traces(textposition="outside", cliponaxis=False).update_layout(showlegend=False, yaxis_title=None)
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
