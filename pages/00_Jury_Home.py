import os
import sys
import json
import streamlit as st
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, PURPLE, GREEN, INK, GRAPHITE, RULE, SURFACE, DISPLAY_FONT

apply_f1_theme()


def csv(*p):
    return pd.read_csv(os.path.join(ROOT, *p))


comp = csv("05_algorithm_comparison", "comparison_results.csv")
parts = csv("08_performance_metrics", "partition_metrics.csv")
ho = parts[parts["partition"].str.startswith("Combined")].iloc[0]
sig = csv("05_algorithm_comparison", "significance_test.csv").iloc[0]
bench = json.load(open(os.path.join(ROOT, "04_pattern_mining", "pattern_mining_benchmark.json")))
ccomp = csv("10_clustering_comparison", "comparison_results.csv")
cm = json.load(open(os.path.join(ROOT, "12_clustering_metrics", "clustering_metrics.json")))
prof_n = len(csv("09_unsupervised_dataset", "driver_season_profiles.csv"))
tiers = csv("11_clustering_algorithm", "cluster_profiles.csv")

st.markdown(f"""
<style>
.apx-hero {{ display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 2.5rem; align-items: end;
             border-bottom: 2px solid {INK}; padding-bottom: 1.2rem; margin-bottom: 1.4rem; }}
.apx-hero h1 {{ font-size: 4.2rem !important; line-height: 0.95 !important; margin: 0 !important; }}
.apx-hero p {{ color: {GRAPHITE}; font-size: 1.12rem; max-width: 60ch; margin: 0.7rem 0 0 0; }}
.apx-tower {{ border: 1px solid {RULE}; background: {SURFACE}; border-radius: 4px; }}
.apx-tower div {{ display: flex; justify-content: space-between; align-items: baseline; padding: 7px 14px; border-bottom: 1px solid {RULE}; }}
.apx-tower div:last-child {{ border-bottom: none; }}
.apx-tower span {{ color: {GRAPHITE}; }}
.apx-tower b {{ font-family: {DISPLAY_FONT}; font-size: 1.45rem; color: {INK}; }}
.apx-tower b.best {{ color: {PURPLE}; }}
.st-key-sheet [data-testid="stHorizontalBlock"] {{ border-bottom: 1px solid {RULE}; padding: 10px 0 12px 0; }}
.apx-pos {{ font-family: {DISPLAY_FONT}; font-size: 1.5rem; color: {GRAPHITE}; }}
.apx-item {{ font-weight: 600; color: {INK}; }}
.apx-dash {{ color: {GRAPHITE}; font-size: 0.9rem; }}
.apx-marks-cell {{ font-family: {DISPLAY_FONT}; font-size: 1.35rem; color: {INK}; }}
.apx-result {{ color: {INK}; }}
.apx-result b {{ font-family: {DISPLAY_FONT}; font-size: 1.15rem; }}
.apx-colhead {{ color: {GRAPHITE}; font-size: 0.85rem; border-bottom: 2px solid {INK}; padding-bottom: 4px; }}
@media (max-width: 900px) {{ .apx-hero {{ grid-template-columns: 1fr; }} .apx-hero h1 {{ font-size: 3rem !important; }} }}
</style>
<div class="apx-hero">
  <div>
    <h1>ApexIQ</h1>
    <p>Formula 1 race intelligence: a data warehouse, a race-winner classifier and driver-tier clustering,
       built on 31 seasons of Grand Prix results. Each row below is one item of the end-semester rubric.</p>
  </div>
  <div class="apx-tower">
    <div><span>Race winner picked, 2022–2024</span><b class="best">{int(ho['top1_hits'])} / {int(ho['total_gps'])}</b></div>
    <div><span>Classifier ROC-AUC</span><b>{ho['roc_auc']:.4f}</b></div>
    <div><span>Gain over pole-sitter baseline</span><b>{sig['mean_delta']:+.3f}</b></div>
    <div><span>Driver tiers found by K-Means</span><b>{len(tiers)}</b></div>
  </div>
</div>
""", unsafe_allow_html=True)

champ = ccomp[ccomp["champion"]].iloc[0]
ROWS = [
    ("Data warehouse design", "Dashboard 1: data warehouse", 3, "<b>2</b> fact tables, <b>7</b> dimensions, 12 live OLAP queries", "pages/20_D1_Warehouse_Design.py"),
    ("Snowflake deployment", "Dashboard 1: data warehouse", 3, "RAW → CLEAN → DW → ML → ANALYTICS, <b>40</b> objects", "pages/21_D1_Snowflake_Deployment.py"),
    ("Dataset (supervised)", "Dashboard 2: supervised learning", 1, "<b>12,358</b> labelled entries, 16 pre-race features", "pages/22_D2_Supervised_Dataset.py"),
    ("Pattern matching: FP-Growth and Apriori", "Dashboard 2: supervised learning", 1, f"<b>{bench['itemsets_count']}</b> identical itemsets, {bench['rules_count']:,} rules", "pages/23_D2_Pattern_Mining.py"),
    ("Comparison with other classifiers, validation test", "Dashboard 2: supervised learning", 2, f"<b>{len(comp)}</b> models, bootstrap CI [{sig['ci_low']:+.3f}, {sig['ci_high']:+.3f}]", "pages/24_D2_Classifier_Comparison.py"),
    ("Classification algorithm", "Dashboard 2: supervised learning", 2, f"XGBoost, recall <b>{ho['recall_class_1'] * 100:.1f}%</b>", "pages/25_D2_Classification_Algorithm.py"),
    ("Dataset (unsupervised)", "Dashboard 3: unsupervised learning", 5, f"<b>{prof_n}</b> driver-season profiles, 9 features", "pages/16_D3_Unsupervised_Dataset.py"),
    ("Clustering algorithm comparison (at least 4)", "Dashboard 3: unsupervised learning", 10, f"<b>{len(ccomp)}</b> algorithms, {champ['algorithm']} chosen at k = {int(champ['n_clusters'])}", "pages/17_D3_Clustering_Comparison.py"),
    ("Clustering algorithm", "Dashboard 3: unsupervised learning", 5, "K-Means: Contenders, Midfield, Backmarkers", "pages/18_D3_KMeans_Clustering.py"),
    ("Performance metrics", "Dashboard 3: unsupervised learning", 5, f"silhouette <b>{cm['silhouette']:.3f}</b>, stability ARI <b>{cm['seed_stability_ari_mean']:.2f}</b>", "pages/19_D3_Clustering_Metrics.py"),
    ("Report", "Submitted document", 5, "PROJECT_REPORT_DWDM_APEXIQ.pdf, 8 chapters", None),
    ("Oral / Q&A", "Viva", 10, "Prepared answers in JURY_QA_PREP.md", None),
]

widths = [0.5, 3.2, 0.8, 3.4, 1.1]
with st.container(key="sheet"):
    head = st.columns(widths, vertical_alignment="bottom")
    for col, label in zip(head, ["Pos", "Rubric item", "Marks", "Result in this project", ""]):
        col.markdown(f'<div class="apx-colhead">{label}</div>', unsafe_allow_html=True)
    for pos, (item, dash, marks, result, page) in enumerate(ROWS, 1):
        c = st.columns(widths, vertical_alignment="center")
        c[0].markdown(f'<span class="apx-pos">{pos}</span>', unsafe_allow_html=True)
        c[1].markdown(f'<div class="apx-item">{item}</div><div class="apx-dash">{dash}</div>', unsafe_allow_html=True)
        c[2].markdown(f'<span class="apx-marks-cell">{marks}</span>', unsafe_allow_html=True)
        c[3].markdown(f'<div class="apx-result">{result}</div>', unsafe_allow_html=True)
        if page:
            c[4].page_link(page, label="Open page", icon=":material/arrow_outward:")

st.caption("Every result on this page is read from the module output files, so the dashboards, the report and the code "
           "always agree. Run `python3 run_all_modules.py` to regenerate them.")
