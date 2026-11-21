"""
FP-Growth Frequent Itemset & Association Rule Mining (Parameter 04)
===================================================================
Implements the FP-Tree based FP-Growth algorithm on discretized Formula 1
Grand Prix race transactions (1994–2024).

Compares:
- Runtime performance (FP-Growth vs. Apriori)
- Mathematical equivalence of frequent itemsets
- Association rules generation (Support, Confidence, Lift)
- Exports association rules to association_rules.csv
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, apriori, association_rules

# Import transaction generator from apriori_analysis
sys.path.append(os.path.dirname(__file__))
from apriori_analysis import build_race_transactions

from itertools import combinations


def apriori_candidate_count(frequent_itemsets):
    """Candidates Apriori must count: every k-itemset whose (k-1)-subsets are all frequent (apriori-gen + prune)."""
    levels = {}
    for its in frequent_itemsets:
        levels.setdefault(len(its), set()).add(frozenset(its))
    total, k = len(set().union(*levels.get(1, [set()]))), 2  # level 1: every single item is a candidate
    while levels.get(k - 1):
        prev = levels[k - 1]
        items = sorted(set().union(*prev))
        cands = {frozenset(c) for a in prev for b in prev if len(a | b) == k
                 for c in [a | b] if all(frozenset(x) in prev for x in combinations(c, k - 1))}
        total += len(cands)
        k += 1
    return total


def fp_tree_node_count(encoded_df, min_support):
    """Nodes in the FP-tree: each transaction's frequent items, sorted by global frequency, inserted as a shared prefix path."""
    support = encoded_df.mean()
    order = support[support >= min_support].sort_values(ascending=False).index.tolist()
    root, nodes = {}, 0
    for row in encoded_df[order].itertuples(index=False):
        node = root
        for item, present in zip(order, row):
            if present:
                if item not in node:
                    node[item] = {}
                    nodes += 1
                node = node[item]
    return nodes


def run_fpgrowth_analysis(min_support=0.02, min_confidence=0.25, export_csv=True):
    print("=" * 80)
    print("   PARAMETER 04: FP-GROWTH ASSOCIATION MINING & APRIORI COMPARISON")
    print("=" * 80)

    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(__file__), "..", "..", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    
    df = pd.read_csv(data_path, low_memory=False)
    print(f"[+] Loaded {len(df):,} race records.")
    
    transactions = build_race_transactions(df)
    print(f"[+] Discretized into {len(transactions):,} transaction itemsets.")

    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    encoded_df = pd.DataFrame(te_ary, columns=te.columns_)
    print(f"[+] Binary Transaction Matrix: {encoded_df.shape[0]} transactions x {encoded_df.shape[1]} unique items.")

    # 1. Benchmark Apriori
    print(f"\n[*] Benchmarking Apriori (min_support={min_support})...")
    t0_ap = time.perf_counter()
    ap_itemsets = apriori(encoded_df, min_support=min_support, use_colnames=True)
    t_ap = time.perf_counter() - t0_ap
    print(f"[+] Apriori runtime: {t_ap:.4f} s | Itemsets: {len(ap_itemsets):,}")

    # 2. Benchmark FP-Growth
    print(f"\n[*] Benchmarking FP-Growth (min_support={min_support})...")
    t0_fp = time.perf_counter()
    fp_itemsets = fpgrowth(encoded_df, min_support=min_support, use_colnames=True)
    t_fp = time.perf_counter() - t0_fp
    print(f"[+] FP-Growth runtime: {t_fp:.4f} s | Itemsets: {len(fp_itemsets):,}")

    speedup = (t_ap / t_fp) if t_fp > 0 else 1.0

    # Implementation-independent cost: Apriori's candidate generation vs. FP-Growth's compressed tree
    n_candidates = apriori_candidate_count(list(ap_itemsets["itemsets"]))
    n_tree_nodes = fp_tree_node_count(encoded_df, min_support)
    print(f"[+] Apriori candidates generated & counted: {n_candidates:,} over {int(ap_itemsets['itemsets'].apply(len).max())} database scans")
    print(f"[+] FP-tree nodes: {n_tree_nodes:,} built in exactly 2 database scans "
          f"({len(encoded_df):,} transactions compressed {len(encoded_df) / n_tree_nodes:.1f}x)")

    # Runtime vs. support sweep: how each algorithm scales as the threshold drops
    sweep = []
    for s_ in [0.05, 0.02, 0.01, 0.005]:
        t0 = time.perf_counter(); a_ = apriori(encoded_df, min_support=s_, use_colnames=True); ta_ = time.perf_counter() - t0
        t0 = time.perf_counter(); f_ = fpgrowth(encoded_df, min_support=s_, use_colnames=True); tf_ = time.perf_counter() - t0
        sweep.append({"min_support": s_, "itemsets": len(f_), "apriori_candidates": apriori_candidate_count(list(a_["itemsets"])),
                      "fp_tree_nodes": fp_tree_node_count(encoded_df, s_),
                      "apriori_time_sec": round(ta_, 4), "fpgrowth_time_sec": round(tf_, 4)})
    sweep_df = pd.DataFrame(sweep)
    print(sweep_df.to_string(index=False))
    faster = "FP-Growth" if t_fp < t_ap else "Apriori"
    print(f"[+] Wall-clock winner: {faster} ({max(t_ap, t_fp) / min(t_ap, t_fp):.1f}x). See support_sweep_benchmark.csv for how the gap changes as min_support drops.")

    # 3. Equivalence Verification
    ap_set = set(frozenset(x) for x in ap_itemsets['itemsets'])
    fp_set = set(frozenset(x) for x in fp_itemsets['itemsets'])
    is_identical = (ap_set == fp_set)
    print(f"[+] Mathematical Itemset Equivalence Check: {'PASSED (100% Identical)' if is_identical else 'FAILED'}")

    # 4. Association Rules Generation
    rules = association_rules(fp_itemsets, metric="confidence", min_threshold=min_confidence)
    rules["antecedents_str"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(list(x))))
    rules["consequents_str"] = rules["consequents"].apply(lambda x: ", ".join(sorted(list(x))))
    print(f"[+] Generated {len(rules):,} association rules (min_confidence={min_confidence}).")

    # Format for export
    export_df = rules[[
        "antecedents_str", "consequents_str", "support", "confidence", "lift", "leverage", "conviction"
    ]].rename(columns={
        "antecedents_str": "antecedents",
        "consequents_str": "consequents"
    }).sort_values(by="lift", ascending=False)

    if export_csv:
        output_csv = os.path.join(os.path.dirname(__file__), "association_rules.csv")
        export_df.to_csv(output_csv, index=False)
        itemsets_out = fp_itemsets.assign(
            itemsets=fp_itemsets["itemsets"].apply(lambda x: ", ".join(sorted(x))),
            length=fp_itemsets["itemsets"].apply(len)).sort_values("support", ascending=False)
        sweep_df.to_csv(os.path.join(os.path.dirname(__file__), "support_sweep_benchmark.csv"), index=False)
        itemsets_out.to_csv(os.path.join(os.path.dirname(__file__), "frequent_itemsets.csv"), index=False)
        with open(os.path.join(os.path.dirname(__file__), "pattern_mining_benchmark.json"), "w") as f:
            json.dump({"transactions": int(len(encoded_df)), "items": int(encoded_df.shape[1]),
                       "min_support": min_support, "min_confidence": min_confidence,
                       "apriori_time_sec": round(t_ap, 4), "fpgrowth_time_sec": round(t_fp, 4),
                       "speedup": round(speedup, 2), "itemsets_count": int(len(fp_itemsets)),
                       "apriori_candidates": int(n_candidates), "fp_tree_nodes": int(n_tree_nodes),
                       "apriori_db_scans": int(ap_itemsets["itemsets"].apply(len).max()), "fpgrowth_db_scans": 2,
                       "apriori_itemsets_count": int(len(ap_itemsets)),
                       "rules_count": int(len(rules)), "is_equivalent": bool(is_identical)}, f, indent=2)
        print(f"[+] Exported association rules to: {output_csv}")

    # Inspect top outcome-predicting rules
    print("\n--- TOP HIGH-LIFT RULES DISCOVERED ---")
    for i, (_, r) in enumerate(export_df.head(5).iterrows(), 1):
        print(f"  {i}. {{{r['antecedents']}}} => {{{r['consequents']}}}")
        print(f"     Support: {r['support']:.4f} | Conf: {r['confidence']:.4f} | Lift: {r['lift']:.2f}x")

    winner_rules = export_df[export_df["consequents"].str.contains("Outcome_Winner", na=False)]
    if len(winner_rules) > 0:
        print("\n--- TOP RULES FOR OUTCOME_WINNER ---")
        for i, (_, r) in enumerate(winner_rules.head(3).iterrows(), 1):
            print(f"  {i}. {{{r['antecedents']}}} => {{{r['consequents']}}}")
            print(f"     Support: {r['support']:.4f} | Conf: {r['confidence']:.4f} | Lift: {r['lift']:.2f}x")

    return {
        "apriori_time": round(t_ap, 4),
        "fpgrowth_time": round(t_fp, 4),
        "speedup": round(speedup, 2),
        "itemsets_count": len(fp_itemsets),
        "rules_count": len(rules),
        "is_equivalent": is_identical
    }

if __name__ == "__main__":
    run_fpgrowth_analysis()
