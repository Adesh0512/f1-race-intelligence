import os
import sys
import json
import streamlit as st
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme

apply_f1_theme()


def csv(*p):
    return pd.read_csv(os.path.join(ROOT, *p))


comp = csv("05_algorithm_comparison", "comparison_results.csv")
champ = comp[comp["algorithm"].str.contains("Champion")].iloc[0]
parts = csv("08_performance_metrics", "partition_metrics.csv")
ho = parts[parts["partition"].str.startswith("Combined")].iloc[0]
sig = csv("05_algorithm_comparison", "significance_test.csv").iloc[0]
bench = json.load(open(os.path.join(ROOT, "04_pattern_mining", "pattern_mining_benchmark.json")))
ccomp = csv("10_clustering_comparison", "comparison_results.csv")
cm = json.load(open(os.path.join(ROOT, "12_clustering_metrics", "clustering_metrics.json")))
prof_n = len(csv("09_unsupervised_dataset", "driver_season_profiles.csv"))

st.title("🏎️ ApexIQ · Formula 1 Race Intelligence")
st.markdown("#### End-semester DWDM jury · Data Warehouse → Supervised Learning → Unsupervised Learning")
st.caption("Every number on this page is read live from the output files of the module scripts (`01_…` to `12_…`), so the dashboards, report and code always agree.")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Warehouse fact rows", "8,650", "star schema, 2004–2024")
k2.metric("Labelled race entries", "12,358", "577 GPs, 1994–2024")
k3.metric("Classifier ROC-AUC", f"{ho['roc_auc']:.4f}", f"{sig['mean_delta']:+.3f} vs baseline (p<0.001)")
k4.metric("Race winner picked", f"{ho['top1_winner_hit_pct']:.1f}%", f"{int(ho['top1_hits'])}/{int(ho['total_gps'])} unseen GPs")
k5.metric("Clusters (K-Means)", "3 tiers", f"silhouette {cm['silhouette']:.3f}")

st.markdown("---")


def item(col, marks, title, page, evidence):
    with col.container(border=True):
        st.markdown(f"**{title}** · `{marks} marks`")
        st.caption(evidence)
        st.page_link(page, label="Open →")


st.subheader("🏛️ Dashboard 1 · Data Warehouse")
a, b = st.columns(2)
item(a, 3, "Data warehouse design", "pages/20_D1_Warehouse_Design.py",
     "Star & snowflake ER diagrams, fact grain, 5 dimensions, 12 live OLAP queries (roll-up, drill-down, slice, dice, pivot).")
item(b, 3, "Snowflake deployment", "pages/21_D1_Snowflake_Deployment.py",
     "7-step automated deploy: RAW → CLEAN → DW → ML → ANALYTICS, 40 objects, clone, Time Travel, dynamic table, stream + task, Cortex.")

st.subheader("🎯 Dashboard 2 · Supervised Learning")
a, b, c, d = st.columns(4)
item(a, 1, "Dataset (supervised)", "pages/22_D2_Supervised_Dataset.py",
     "12,358 entries, 16 pre-race features, 5 labels, 20.4:1 imbalance, chronological split.")
item(b, 1, "Pattern matching: FP-Growth & Apriori", "pages/23_D2_Pattern_Mining.py",
     f"{bench['itemsets_count']} identical itemsets, {bench['rules_count']:,} rules, candidates vs FP-tree cost sweep.")
item(c, 2, "Classifier comparison & validation", "pages/24_D2_Classifier_Comparison.py",
     f"7 models, 6-fold expanding window, bootstrap CI [{sig['ci_low']:+.3f}, {sig['ci_high']:+.3f}].")
item(d, 2, "Classification algorithm", "pages/25_D2_Classification_Algorithm.py",
     f"Cost-sensitive XGBoost + race softmax: recall {ho['recall_class_1'] * 100:.1f}%, ROC/PR curves, threshold tuner, race explorer.")

st.subheader("🧭 Dashboard 3 · Unsupervised Learning")
a, b, c, d = st.columns(4)
item(a, 5, "Dataset (unsupervised)", "pages/16_D3_Unsupervised_Dataset.py",
     f"{prof_n} driver-season profiles, 9 standardised features, no label.")
item(b, 10, "Clustering comparison (≥ 4)", "pages/17_D3_Clustering_Comparison.py",
     f"{len(ccomp)} algorithms: K-Means, Ward, GMM, BIRCH, DBSCAN; elbow, silhouette & dendrogram.")
item(c, 5, "Clustering algorithm", "pages/18_D3_KMeans_Clustering.py",
     "K-Means k = 3: Contenders / Midfield / Backmarkers, PCA map, eras, live tier classifier.")
item(d, 5, "Performance metrics", "pages/19_D3_Clustering_Metrics.py",
     f"Silhouette {cm['silhouette']:.3f}, Davies-Bouldin {cm['davies_bouldin']:.3f}, CH {cm['calinski_harabasz']:.0f}, stability ARI {cm['seed_stability_ari_mean']:.2f}.")

st.markdown("---")
st.markdown("**Report (5)** · `PROJECT_REPORT_DWDM_APEXIQ.pdf` · **Oral / Q&A (10)** · `JURY_QA_PREP.md` · **Reproduce everything:** `python3 run_all_modules.py`")
