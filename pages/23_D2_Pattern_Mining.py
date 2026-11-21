import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header

apply_f1_theme()

MOD = os.path.join(ROOT, "04_pattern_mining")
bench = json.load(open(os.path.join(MOD, "pattern_mining_benchmark.json")))
sweep = pd.read_csv(os.path.join(MOD, "support_sweep_benchmark.csv"))
rules = pd.read_csv(os.path.join(MOD, "association_rules.csv"))
itemsets = pd.read_csv(os.path.join(MOD, "frequent_itemsets.csv"))

page_header('Dashboard 2', 'Supervised learning', 'Pattern matching: FP-Growth and Apriori',
            f"{bench['transactions']:,} race transactions over {bench['items']} items, with minimum support {bench['min_support']} and minimum confidence {bench['min_confidence']}.", marks=1)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Frequent Itemsets", bench["itemsets_count"], "Identical in both" if bench["is_equivalent"] else "MISMATCH")
c2.metric("Association Rules", f"{bench['rules_count']:,}")
c3.metric("Apriori Candidates", f"{bench['apriori_candidates']:,}", f"{bench['apriori_db_scans']} DB scans", delta_color="off")
c4.metric("FP-Tree Nodes", f"{bench['fp_tree_nodes']:,}", "2 DB scans", delta_color="off")

st.markdown("---")
t1, t2, t3, t4 = st.tabs(["Algorithm Comparison", "Outcome Rules", "Rule Explorer", "Frequent Itemsets"])

with t1:
    a, b = st.columns(2)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sweep["min_support"], y=sweep["apriori_candidates"], name="Apriori candidates", mode="lines+markers", line=dict(color="#8B949E")))
    fig.add_trace(go.Scatter(x=sweep["min_support"], y=sweep["fp_tree_nodes"], name="FP-tree nodes", mode="lines+markers", line=dict(color=F1_RED)))
    fig.update_layout(title="Search-space cost vs. min_support", xaxis=dict(title="min_support", autorange="reversed", type="log"), yaxis_title="count")
    a.plotly_chart(get_plotly_theme(fig), width="stretch")
    long = sweep.melt(id_vars="min_support", value_vars=["apriori_time_sec", "fpgrowth_time_sec"], var_name="algorithm", value_name="seconds")
    b.plotly_chart(get_plotly_theme(px.line(long, x="min_support", y="seconds", color="algorithm", markers=True, log_x=True,
                                            color_discrete_map={"apriori_time_sec": "#8B949E", "fpgrowth_time_sec": F1_RED},
                                            title="Wall-clock runtime (mlxtend)").update_xaxes(autorange="reversed")), width="stretch")
    st.dataframe(sweep, width="stretch", hide_index=True)
    st.markdown(f"""
    | | Apriori | FP-Growth |
    |---|---|---|
    | Strategy | Level-wise **candidate generation** + support counting | **Divide & conquer** on a compressed prefix tree, no candidates |
    | Database scans | k scans (here **{bench['apriori_db_scans']}**) | Exactly **2** |
    | Search cost as support drops | Candidates grow **{sweep['apriori_candidates'].iloc[-1] / sweep['apriori_candidates'].iloc[0]:.0f}×** ({sweep['apriori_candidates'].iloc[0]:,} → {sweep['apriori_candidates'].iloc[-1]:,}) | Tree size stays bounded ({sweep['fp_tree_nodes'].iloc[-1]:,} nodes) |
    | Output | {bench['apriori_itemsets_count']} itemsets | {bench['itemsets_count']} itemsets: **identical** |

    """)
    cross = sweep[sweep["fpgrowth_time_sec"] < sweep["apriori_time_sec"]]
    st.info("**Runtime crossover:** at high support the basket is tiny (24 items), so Apriori's vectorised level-wise counting is fastest. "
            + (f"As min_support drops to **{cross['min_support'].max()}**, Apriori's candidate explosion makes it slower and **FP-Growth wins**. "
               if len(cross) else "FP-Growth's advantage would appear at lower support or with more items. ")
            + "FP-Growth's cost is bounded by the FP-tree size and 2 database scans, not by the number of candidates.")

with t2:
    target = st.radio("Consequent", ["Outcome_Winner", "Outcome_Podium", "Outcome_Points", "Outcome_DNF"], horizontal=True)
    sub = rules[rules["consequents"].str.contains(target)].sort_values("lift", ascending=False).head(12)
    st.plotly_chart(get_plotly_theme(px.bar(sub, x="lift", y="antecedents", orientation="h", color="confidence",
                                            color_continuous_scale="Reds", title=f"Top rules ⇒ {target} (by lift)")
                                     .update_yaxes(autorange="reversed")), width="stretch")
    st.dataframe(sub.round(4), width="stretch", hide_index=True)
    st.caption("Lift > 1: the antecedent makes the outcome more likely than its base rate. Example: pole + podium ⇒ winner at 17× the base rate.")

with t3:
    lo, hi = st.slider("Lift range", float(rules["lift"].min()), float(rules["lift"].max()), (2.0, float(rules["lift"].max())))
    conf = st.slider("Minimum confidence", 0.25, 1.0, 0.5)
    view = rules[rules["lift"].between(lo, hi) & (rules["confidence"] >= conf)]
    st.plotly_chart(get_plotly_theme(px.scatter(view, x="support", y="confidence", size="lift", color="lift", hover_data=["antecedents", "consequents"],
                                                color_continuous_scale="Reds", title=f"{len(view)} rules: support vs. confidence")), width="stretch")
    st.dataframe(view.round(4), width="stretch", hide_index=True, height=300)

with t4:
    k = st.select_slider("Itemset length", sorted(itemsets["length"].unique()), value=2)
    st.dataframe(itemsets[itemsets["length"] == k].round(4), width="stretch", hide_index=True, height=380)
