import os
import re
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, get_snowflake_session, query_snowflake, page_header

apply_f1_theme()

page_header('Dashboard 1', 'Data warehouse', 'Snowflake deployment',
            'How the warehouse is built in Snowflake, layer by layer: RAW → CLEAN → DW → ML → ANALYTICS.', marks=3)

SQL_PATH = os.path.join(ROOT, "MASTER_SNOWFLAKE_DEPLOYMENT.sql")
sql_text = open(SQL_PATH, encoding="utf-8").read()

OBJ = re.compile(r"^CREATE\s+(?:OR\s+REPLACE\s+)?(?:SECURE\s+)?(WAREHOUSE|DATABASE|SCHEMA|FILE FORMAT|STAGE|DYNAMIC TABLE|TABLE|VIEW|STREAM|TASK|PROCEDURE)\s+(?:IF NOT EXISTS\s+)?([\w.]+)", re.M | re.I)
objs = pd.DataFrame(OBJ.findall(sql_text), columns=["type", "name"]).drop_duplicates("name", keep="last")
objs["type"] = objs["type"].str.upper()
objs["schema"] = objs["name"].apply(lambda n: n.split(".")[0] if "." in n else "—")

conn_type, _ = get_snowflake_session()
live = conn_type in ("snowpark", "connector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Snowflake Objects Defined", len(objs))
c2.metric("Schemas", int((objs["type"] == "SCHEMA").sum()), "RAW · CLEAN · ML · ANALYTICS · DW")
c3.metric("Tables & Views", int(objs["type"].isin(["TABLE", "VIEW", "DYNAMIC TABLE"]).sum()))
c4.metric("Connection", "Live" if live else "Offline", conn_type, delta_color="normal" if live else "off")

st.markdown("---")
t1, t2, t3, t4 = st.tabs(["Deployment Pipeline", "Object Manifest", "Live Verification", "Deployment SQL"])

with t1:
    st.markdown("""
    `deploy_to_snowflake.py` deploys the whole warehouse in **7 automated steps** from `MASTER_SNOWFLAKE_DEPLOYMENT.sql`:

    | Step | What happens | Snowflake feature |
    |---|---|---|
    | 1 | Create `F1_WH` (X-Small, auto-suspend 60 s), `F1_PREDICTION_DB`, schemas, CSV file format, stages | Virtual warehouse, internal stages |
    | 2 | Create RAW / CLEAN / ML table DDLs | — |
    | 3 | `PUT` CSVs, model artifacts and clustering output to `@RAW.F1_RAW_STAGE` | Internal stage upload |
    | 4 | Bulk `COPY INTO` the RAW tables, then `INSERT OVERWRITE` into CLEAN | Bulk loading |
    | 5 | ELT transform and leakage audit on `CLEAN.F1_MODELING_MASTER` | SQL ELT |
    | 6 | Zero-copy clone, Time Travel, dynamic table, stream + task (CDC auto-scoring), secure view, Cortex AI procedure | Advanced platform features |
    | 6b | Build **DW star schema** (`FACT_RACE_RESULTS_STAR` + 4 dims) and **snowflake schema** (`DIM_CIRCUIT → DIM_COUNTRY`); load `ML.DRIVER_SEASON_CLUSTERS` | Dimensional modelling |
    | 7 | Verification scorecard: row counts for every table | — |
    """)
    st.code("python3 deploy_to_snowflake.py   # reads SNOWFLAKE_ACCOUNT / USER / PASSWORD from .env", language="bash")
    st.markdown("""
    #### Streamlit in Snowflake (SiS)
    The dashboard itself was also deployed **inside Snowflake** as the native Streamlit app `F1_RACE_INTELLIGENCE`,
    served from the stage `F1_PREDICTION_DB.ANALYTICS.F1_STREAMLIT_STAGE` and running on warehouse `F1_WH`:
    `PUT` every app file to the stage → `CREATE STREAMLIT … ROOT_LOCATION = '@F1_STREAMLIT_STAGE' MAIN_FILE = 'streamlit_app.py'`.
    Read-only scripts in `00_data_warehouse/snowflake_streamlit_deployment/` prove what is live
    (`SHOW STREAMLITS`, `DESCRIBE STREAMLIT`, `LIST @F1_STREAMLIT_STAGE`, `GET` the deployed `streamlit_app.py`).
    The app that is currently deployed is the Jury 2 version.
    """)

with t2:
    st.plotly_chart(get_plotly_theme(px.histogram(objs, x="schema", color="type", barmode="stack",
                                                  title="Objects per Schema")), width="stretch")
    st.dataframe(objs.sort_values(["schema", "type"]), width="stretch", hide_index=True, height=360)

with t3:
    if live:
        tables = objs.loc[objs["type"].isin(["TABLE", "DYNAMIC TABLE"]) & objs["name"].str.contains(r"\."), "name"].tolist()
        rows = []
        for t in tables:
            df = query_snowflake(f"SELECT COUNT(*) AS N FROM {t}")
            rows.append((t, int(df.iloc[0, 0]) if "n" in df.columns else None))
        st.success("Connected to Snowflake: live row counts")
        st.dataframe(pd.DataFrame(rows, columns=["table", "rows"]), width="stretch", hide_index=True)
    else:
        st.warning("Not connected. Add Snowflake credentials to `.env` (see `.env.example`) and restart the app to see live row counts. "
                   "Expected counts after deployment are listed below.")
        st.dataframe(pd.DataFrame([
            ("CLEAN.F1_MODELING_MASTER", 8650), ("DW.FACT_RACE_RESULTS_STAR", 8650), ("DW.DIM_RACE_STAR", 412),
            ("DW.DIM_DRIVER", "≈108"), ("DW.DIM_CONSTRUCTOR", "≈35"), ("ML.ASSOCIATION_RULES", 1393),
            ("ML.DRIVER_SEASON_CLUSTERS", 703)], columns=["table", "expected rows"]).astype(str),
            width="stretch", hide_index=True)

with t4:
    section = st.selectbox("Section", re.findall(r"^-- (\d\d_[A-Z_]+\.SQL):", sql_text, re.M))
    m = re.search(rf"-- {re.escape(section)}:.*?(?=\n-- =+\n-- \d\d_[A-Z_]+\.SQL:|\Z)", sql_text, re.S)
    st.code(m.group(0) if m else "", language="sql")
