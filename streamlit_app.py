"""
ApexIQ · Formula 1 Race Intelligence: jury dashboard router.
Pages are grouped exactly as the end-semester rubric: Dashboard 1 (warehouse),
Dashboard 2 (supervised), Dashboard 3 (unsupervised), plus extras.
The previous landing page is kept at pages/legacy_platform_hub.py.
"""

import streamlit as st

st.set_page_config(page_title="ApexIQ · F1 Race Intelligence", page_icon="🏎️", layout="wide", initial_sidebar_state="expanded")

P = st.Page
nav = st.navigation({
    "Jury Overview": [P("pages/00_Jury_Home.py", title="Rubric Scorecard", icon="🏁", default=True)],
    "Dashboard 1 · Data Warehouse": [
        P("pages/20_D1_Warehouse_Design.py", title="Warehouse Design", icon="🏛️"),
        P("pages/21_D1_Snowflake_Deployment.py", title="Snowflake Deployment", icon="❄️"),
        P("pages/14_Snowflake_Showcase.py", title="Snowflake Advanced Features", icon="🧊"),
        P("pages/3_Architecture.py", title="Pipeline Architecture", icon="🗺️"),
    ],
    "Dashboard 2 · Supervised Learning": [
        P("pages/22_D2_Supervised_Dataset.py", title="Dataset (Supervised)", icon="📊"),
        P("pages/23_D2_Pattern_Mining.py", title="Pattern Matching: FP-Growth & Apriori", icon="🧩"),
        P("pages/24_D2_Classifier_Comparison.py", title="Classifier Comparison & Validation", icon="⚖️"),
        P("pages/25_D2_Classification_Algorithm.py", title="Classification Algorithm", icon="🏎️"),
    ],
    "Dashboard 3 · Unsupervised Learning": [
        P("pages/16_D3_Unsupervised_Dataset.py", title="Dataset (Unsupervised)", icon="🗂️"),
        P("pages/17_D3_Clustering_Comparison.py", title="Clustering Comparison", icon="⚖️"),
        P("pages/18_D3_KMeans_Clustering.py", title="Clustering Algorithm: K-Means", icon="🎯"),
        P("pages/19_D3_Clustering_Metrics.py", title="Clustering Performance Metrics", icon="📏"),
    ],
    "Extras": [
        P("pages/13_SQL_Playground.py", title="SQL Playground", icon="💻"),
        P("pages/5_Data_Explorer.py", title="Warehouse Data Explorer", icon="🔎"),
        P("pages/15_Power_BI_Race_Predictor_Dashboard.py", title="Race Predictor (Power BI style)", icon="📈"),
    ],
})
nav.run()
