import os
import sys
import json
import streamlit as st
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, page_header

apply_f1_theme()

page_header("Dashboard 1", "Data warehouse", "Pipeline architecture",
            "How data flows from the source files through the warehouse into pattern mining, classification and clustering, and out to the dashboards.")


def out(*p):
    return os.path.join(ROOT, *p)


bench = json.load(open(out("04_pattern_mining", "pattern_mining_benchmark.json")))
cm = json.load(open(out("12_clustering_metrics", "clustering_metrics.json")))
ho = pd.read_csv(out("08_performance_metrics", "partition_metrics.csv")).set_index("partition").loc["Combined Holdout (2022–2024)"]
n_algos = len(pd.read_csv(out("10_clustering_comparison", "comparison_results.csv")))
n_models = len(pd.read_csv(out("05_algorithm_comparison", "comparison_results.csv")))

dot = f"""digraph P {{
  rankdir=TB; bgcolor="transparent"; nodesep=0.5; ranksep=0.45;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, color="#D8DCE2", fillcolor="#FFFFFF", fontcolor="#15181D", margin="0.18,0.10"];
  edge [color="#59616C", arrowsize=0.7];
  subgraph cluster_src {{ label="Sources"; fontname="Helvetica"; fontcolor="#59616C"; color="#D8DCE2";
    src [label="Ergast F1 results\\nCSV files"]; }}
  subgraph cluster_dw {{ label="Data warehouse (Dashboard 1)"; fontname="Helvetica"; fontcolor="#59616C"; color="#D8DCE2";
    etl [label="ETL\\nclean, conform keys"];
    dw [label="Star + snowflake schemas\\n2 facts, 7 dimensions\\nf1_warehouse.db", fillcolor="#15181D", fontcolor="#FFFFFF"];
    sf [label="Snowflake\\nRAW → CLEAN → DW\\n→ ML → ANALYTICS"]; }}
  fs [label="Feature store 1994–2024\\n12,358 race entries\\n16 pre-race features"];
  subgraph cluster_ml {{ label="Data mining (Dashboards 2 and 3)"; fontname="Helvetica"; fontcolor="#59616C"; color="#D8DCE2";
    pm [label="Pattern mining\\nApriori = FP-Growth\\n{bench['itemsets_count']} itemsets, {bench['rules_count']:,} rules"];
    clf [label="Classification\\n{n_models} models, XGBoost champion\\nROC-AUC {ho['roc_auc']:.4f}, {int(ho['top1_hits'])}/{int(ho['total_gps'])} winners", fillcolor="#7B2CBF", fontcolor="#FFFFFF"];
    cl [label="Clustering\\n{cm['n_profiles']} driver-seasons, {n_algos} algorithms\\nK-Means k = {cm['k']}", fillcolor="#1A9E55", fontcolor="#FFFFFF"]; }}
  subgraph cluster_out {{ label="Outputs"; fontname="Helvetica"; fontcolor="#59616C"; color="#D8DCE2";
    app [label="Streamlit dashboards"]; pbi [label="Power BI\\nworkbook + project"]; rep [label="Report + tests"]; }}
  src -> etl -> dw -> sf; dw -> fs; fs -> pm; fs -> clf; fs -> cl;
  pm -> app; clf -> app; cl -> app; clf -> pbi; cl -> pbi; app -> rep [style=invis];
  sf -> app [style=dashed, label=" live SQL", fontname="Helvetica", fontsize=9, fontcolor="#59616C"];
}}"""
st.graphviz_chart(dot, width="stretch")

a, b = st.columns(2)
a.markdown(f"""
#### Warehouse
* **Grain:** one row per driver per Grand Prix. Star schema for fast dashboard queries, snowflake schema for normalised reference data.
* **Snowflake:** `deploy_to_snowflake.py` loads RAW, transforms to CLEAN, builds the DW star and snowflake tables and the ML result tables.
* **Feature store:** every feature uses only races before the one being predicted, so nothing from the race itself leaks in.
""")
b.markdown(f"""
#### Mining and learning
* **Pattern mining:** Apriori and FP-Growth find the same {bench['itemsets_count']} itemsets; FP-Growth scales better as support drops.
* **Classification:** cost-sensitive XGBoost, trained on 1994–2021 and tested on unseen 2022–2024 races; probabilities sum to 1 per race.
* **Clustering:** {n_algos} algorithms compared on {cm['n_profiles']} driver-season profiles; K-Means finds 3 performance tiers.
* **One command** (`run_all_modules.py`) regenerates every number shown in the app, the report and Power BI.
""")
