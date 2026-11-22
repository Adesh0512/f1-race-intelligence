import os
import sys
import json
import math
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, F1_RED, page_header, SEQ_SCALE

apply_f1_theme()

MOD = os.path.join(ROOT, "04_pattern_mining")
sys.path.insert(0, MOD)
from apriori_analysis import build_race_transactions
bench = json.load(open(os.path.join(MOD, "pattern_mining_benchmark.json")))
sweep = pd.read_csv(os.path.join(MOD, "support_sweep_benchmark.csv"))
rules = pd.read_csv(os.path.join(MOD, "association_rules.csv"))
itemsets = pd.read_csv(os.path.join(MOD, "frequent_itemsets.csv"))

page_header('Dashboard 2', 'Supervised learning', 'Pattern matching: FP-Growth and Apriori',
            f"{bench['transactions']:,} race transactions over {bench['items']} items, with minimum support {bench['min_support']} and minimum confidence {bench['min_confidence']}.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Frequent Itemsets", bench["itemsets_count"], "Identical in both" if bench["is_equivalent"] else "MISMATCH")
c2.metric("Association Rules", f"{bench['rules_count']:,}")
c3.metric("Apriori Candidates", f"{bench['apriori_candidates']:,}", f"{bench['apriori_db_scans']} DB scans", delta_color="off")
c4.metric("FP-Tree Nodes", f"{bench['fp_tree_nodes']:,}", "2 DB scans", delta_color="off")

st.markdown("---")
t0, t1, t2, t3, t4 = st.tabs(["Concepts & Worked Example", "Algorithm Comparison", "Outcome Rules", "Rule Explorer", "Frequent Itemsets"])


@st.cache_data
def load_transactions():
    """The same transactions the miners used: one per driver-race entry (rows and transactions line up 1:1)."""
    df = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), low_memory=False)
    return df[["season", "race_name", "driver_name"]], [frozenset(t) for t in build_race_transactions(df)]


with t0:
    meta, T = load_transactions()
    N = len(T)
    assert N == bench["transactions"], "transactions must match the mined data"
    vocab = sorted(set().union(*T))
    st.markdown(f"""
    #### Frequent itemsets
    Each **transaction** is one driver in one Grand Prix ({N:,} in total). Its **items** describe the entry in words:
    grid slot, team, recent form, career and circuit record, and how the race ended. An **itemset** is any group of items,
    such as {{Grid Pole P1, Outcome Winner}}. Its **support** is the share of transactions that contain all of them.
    An itemset is **frequent** when its support is at least **{bench['min_support']}**, so it appears in at least
    {math.ceil(bench['min_support'] * N):,} transactions.
    """)
    groups = pd.Series(vocab).groupby(pd.Series(vocab).str.split("_").str[0].replace({"Beat": "Qualifying"})).agg(lambda x: ", ".join(i.replace("_", " ") for i in x))
    st.dataframe(pd.DataFrame({"Item group": groups.index, "Items": groups.values}), width="stretch")
    st.markdown("**Three real transactions**")
    sample = [i for i in range(N) if "Outcome_Winner" in T[i]][-1:] + [N - 2, N - 3]
    st.dataframe(pd.DataFrame([(f"{int(meta.season[i])} {meta.race_name[i]}", meta.driver_name[i], ", ".join(sorted(x.replace("_", " ") for x in T[i])))
                               for i in sample], columns=["Race", "Driver", "Items in the transaction"]), width="stretch")
    st.markdown(f"""
    #### How the two algorithms find them
    | Apriori | FP-Growth |
    |---|---|
    | 1. Count single items, keep those with support ≥ {bench['min_support']} | 1. Scan once: count items, drop the infrequent ones |
    | 2. Join frequent k-itemsets into (k+1)-candidates | 2. Scan again: insert every transaction into a compressed prefix tree (FP-tree) |
    | 3. Prune candidates with an infrequent subset (*every subset of a frequent itemset is frequent*) | 3. For each item, take its conditional pattern base and grow patterns recursively |
    | 4. Scan the data to count the rest; repeat until none are left | No candidates are generated |
    | Here: **{bench['apriori_candidates']:,} candidates, {bench['apriori_db_scans']} scans** | Here: **{bench['fp_tree_nodes']:,} tree nodes, 2 scans** |
    """)
    st.code(f"""encoded = TransactionEncoder().fit(transactions).transform(transactions)   # {N:,} × {len(vocab)} true/false matrix
ap = apriori(encoded, min_support={bench['min_support']}, use_colnames=True)          # {bench['apriori_itemsets_count']} itemsets
fp = fpgrowth(encoded, min_support={bench['min_support']}, use_colnames=True)         # {bench['itemsets_count']} itemsets, identical
rules = association_rules(fp, metric="confidence", min_threshold={bench['min_confidence']})   # {bench['rules_count']:,} rules""", language="python")

    st.markdown("#### Support, confidence and lift on a real rule")
    # pre-race conditions => one race outcome read most naturally; strongest first, simplest first on ties
    top = rules[rules["consequents"].str.startswith("Outcome_") & ~rules["consequents"].str.contains(",")
                & ~rules["antecedents"].str.contains("Outcome_") & (rules["antecedents"].str.count(",") <= 1)]
    top = top.assign(n=top["antecedents"].str.count(",")).sort_values(["lift", "n"], ascending=[False, True]).head(20).reset_index(drop=True)
    label = lambda i: f"{top.antecedents[i].replace('_', ' ')}  ⇒  {top.consequents[i].replace('_', ' ')}"
    i = st.selectbox("Rule (pre-race condition ⇒ race outcome)", range(len(top)), format_func=label)
    X, Y = frozenset(top.antecedents[i].split(", ")), frozenset(top.consequents[i].split(", "))
    nX, nY, nXY = sum(X <= t for t in T), sum(Y <= t for t in T), sum((X | Y) <= t for t in T)
    sup, conf, lift = nXY / N, nXY / nX, (nXY / nX) / (nY / N)
    assert abs(sup - top.support[i]) < 1e-9 and abs(lift - top.lift[i]) < 1e-6, "hand count must match the mined rule"
    a, b, c = st.columns(3)
    a.metric("Support", f"{sup:.4f}", f"{nXY:,} of {N:,} transactions", delta_color="off")
    b.metric("Confidence", f"{conf:.1%}", f"{nXY:,} of {nX:,} with the antecedent", delta_color="off")
    c.metric("Lift", f"{lift:.2f}×", f"base rate {nY / N:.1%}", delta_color="off")
    st.markdown(f"""
    | Measure | Formula | Worked out |
    |---|---|---|
    | Support | count(X ∪ Y) / N | {nXY:,} / {N:,} = **{sup:.4f}** |
    | Confidence | count(X ∪ Y) / count(X) | {nXY:,} / {nX:,} = **{conf:.4f}** |
    | Lift | confidence / support(Y) | {conf:.4f} / ({nY:,} / {N:,}) = **{lift:.2f}** |
    """)
    st.success(f"**Reading it:** when a transaction has {label(i).split('  ⇒  ')[0]}, it also has {label(i).split('  ⇒  ')[1]} "
               f"{conf:.0%} of the time, {lift:.1f}× more often than that outcome's base rate of {nY / N:.1%}. "
               "The counts are taken from the transactions right now and match the mined rule exactly.")

with t1:
    a, b = st.columns(2)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sweep["min_support"], y=sweep["apriori_candidates"], name="Apriori candidates", mode="lines+markers", line=dict(color="#8B949E")))
    fig.add_trace(go.Scatter(x=sweep["min_support"], y=sweep["fp_tree_nodes"], name="FP-tree nodes", mode="lines+markers", line=dict(color=F1_RED)))
    ticks = dict(tickvals=sweep["min_support"].tolist(), ticktext=[str(v) for v in sweep["min_support"]], minor=dict(showgrid=False))
    fig.update_layout(title="Search-space cost vs. min support", xaxis=dict(title="min_support", autorange="reversed", type="log", **ticks), yaxis_title="count")
    a.plotly_chart(get_plotly_theme(fig), width="stretch")
    long = sweep.rename(columns={"apriori_time_sec": "Apriori", "fpgrowth_time_sec": "FP-Growth"}).melt(
        id_vars="min_support", value_vars=["Apriori", "FP-Growth"], var_name="algorithm", value_name="seconds")
    b.plotly_chart(get_plotly_theme(px.line(long, x="min_support", y="seconds", color="algorithm", markers=True, log_x=True,
                                            color_discrete_map={"Apriori": "#8B949E", "FP-Growth": F1_RED},
                                            title="Wall-clock runtime (mlxtend)").update_xaxes(autorange="reversed", **ticks)), width="stretch")
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
    target = st.radio("Consequent", ["Outcome_Winner", "Outcome_Podium", "Outcome_Points", "Outcome_DNF"], horizontal=True,
                      format_func=lambda t: t.replace("_", " "))
    sub = rules[rules["consequents"].str.contains(target)].sort_values("lift", ascending=False).head(12)
    sub = sub.assign(antecedents=sub["antecedents"].str.replace("_", " "), consequents=sub["consequents"].str.replace("_", " "))
    st.plotly_chart(get_plotly_theme(px.bar(sub, x="lift", y="antecedents", orientation="h", color="confidence",
                                            color_continuous_scale=SEQ_SCALE, title=f"Top rules ⇒ {target.replace('_', ' ')} (by lift)")
                                     .update_yaxes(autorange="reversed")), width="stretch")
    st.dataframe(sub.round(4), width="stretch", hide_index=True)
    st.caption("Lift > 1: the antecedent makes the outcome more likely than its base rate. Example: pole + podium ⇒ winner at 17× the base rate.")

with t3:
    lo, hi = st.slider("Lift range", float(rules["lift"].min()), float(rules["lift"].max()), (2.0, float(rules["lift"].max())))
    conf = st.slider("Minimum confidence", 0.25, 1.0, 0.5)
    view = rules[rules["lift"].between(lo, hi) & (rules["confidence"] >= conf)]
    st.plotly_chart(get_plotly_theme(px.scatter(view, x="support", y="confidence", size="lift", color="lift", hover_data=["antecedents", "consequents"],
                                                color_continuous_scale=SEQ_SCALE, title=f"{len(view)} rules: support vs. confidence")), width="stretch")
    st.dataframe(view.round(4), width="stretch", hide_index=True, height=300)

with t4:
    k = st.select_slider("Itemset length", sorted(itemsets["length"].unique()), value=2)
    st.dataframe(itemsets[itemsets["length"] == k].round(4), width="stretch", hide_index=True, height=380)
