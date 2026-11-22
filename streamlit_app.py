"""
ApexIQ · Formula 1 Race Intelligence: dashboard router.
Pages are grouped into Dashboard 1 (warehouse),
Dashboard 2 (supervised), Dashboard 3 (unsupervised), plus extras.
The previous landing page is kept at pages/legacy_platform_hub.py.
"""

import streamlit as st

st.set_page_config(page_title="ApexIQ · F1 Race Intelligence", page_icon=":material/sports_score:", layout="wide", initial_sidebar_state="expanded")

P = st.Page
nav = st.navigation({
    "Overview": [P("pages/00_Jury_Home.py", title="Project overview", icon=":material/flag:", default=True)],
    "Dashboard 1: Data warehouse": [
        P("pages/20_D1_Warehouse_Design.py", title="Warehouse Design", icon=":material/account_tree:"),
        P("pages/21_D1_Snowflake_Deployment.py", title="Snowflake Deployment", icon=":material/cloud_upload:"),
        P("pages/14_Snowflake_Showcase.py", title="Snowflake Advanced Features", icon=":material/tune:"),
        P("pages/3_Architecture.py", title="Pipeline Architecture", icon=":material/schema:"),
    ],
    "Dashboard 2: Supervised learning": [
        P("pages/22_D2_Supervised_Dataset.py", title="Dataset (Supervised)", icon=":material/table_rows:"),
        P("pages/23_D2_Pattern_Mining.py", title="Pattern Mining: FP-Growth", icon=":material/hub:"),
        P("pages/24_D2_Classifier_Comparison.py", title="Classifier Comparison & Validation", icon=":material/leaderboard:"),
        P("pages/25_D2_Classification_Algorithm.py", title="Classification Algorithm", icon=":material/sports_score:"),
        P("pages/26_D2_Race_Predictor.py", title="Race Predictor", icon=":material/online_prediction:"),
    ],
    "Dashboard 3: Unsupervised learning": [
        P("pages/16_D3_Unsupervised_Dataset.py", title="Dataset (Unsupervised)", icon=":material/table_rows:"),
        P("pages/17_D3_Clustering_Comparison.py", title="Clustering Comparison", icon=":material/leaderboard:"),
        P("pages/18_D3_KMeans_Clustering.py", title="Clustering Algorithm: K-Means", icon=":material/scatter_plot:"),
        P("pages/19_D3_Clustering_Metrics.py", title="Clustering Performance Metrics", icon=":material/straighten:"),
    ],
    "Extras": [
        P("pages/13_SQL_Playground.py", title="SQL Playground", icon=":material/terminal:"),
    ],
})
nav.run()
