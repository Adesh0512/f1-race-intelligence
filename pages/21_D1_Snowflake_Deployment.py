import os
import re
import sys
import time
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, get_plotly_theme, get_snowflake_session, query_snowflake, page_header

apply_f1_theme()

page_header('Dashboard 1', 'Data warehouse', 'Snowflake deployment',
            'How the warehouse is built in Snowflake, layer by layer: RAW → CLEAN → DW → ML → ANALYTICS.')

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
c2.metric("Schemas", int((objs["type"] == "SCHEMA").sum()), "RAW to ANALYTICS", delta_color="off")
c3.metric("Tables & Views", int(objs["type"].isin(["TABLE", "VIEW", "DYNAMIC TABLE"]).sum()))
c4.metric("Connection", "Live" if live else "Offline", conn_type, delta_color="normal" if live else "off")

st.markdown("---")
t0, t1, t4, t3, t5, t6, t2 = st.tabs(["Environment", "Deployment Pipeline", "Deployment SQL", "Live Verification",
                                       "Design → Snowflake", "Run SQL", "Object Manifest"])
OFFLINE = "Not connected to Snowflake. Inside Snowflake, or with credentials in `.env`, this tab reads the live account."


def live_query(sql, cols):
    """Live result, or None when offline or the query failed (query_snowflake falls back to unrelated local data)."""
    if not live:
        return None
    df = query_snowflake(sql)
    return df if set(cols) <= set(df.columns) else None


with t0:
    env = live_query("SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() AS account, CURRENT_REGION() AS region, CURRENT_ROLE() AS role, "
                     "CURRENT_WAREHOUSE() AS warehouse, CURRENT_DATABASE() AS database, CURRENT_VERSION() AS version",
                     ["account", "region", "warehouse"])
    if env is not None:
        e = env.iloc[0]
        a, b, c = st.columns(3)
        a.metric("Account", e["account"], e["region"], delta_color="off")
        b.metric("Database", e["database"] or "F1_PREDICTION_DB", f"role {e['role']}", delta_color="off")
        c.metric("Warehouse", e["warehouse"] or "F1_WH", "X-Small · auto-suspend 60 s", delta_color="off")
        sch = live_query("SELECT table_schema, COUNT_IF(table_type = 'BASE TABLE') AS tables, COUNT_IF(table_type = 'VIEW') AS views "
                         "FROM F1_PREDICTION_DB.INFORMATION_SCHEMA.TABLES WHERE table_schema IN ('RAW','CLEAN','DW','ML','ANALYTICS') "
                         "GROUP BY 1", ["table_schema", "tables"])
        if sch is not None:
            purpose = {"RAW": "Files exactly as loaded from the stage", "CLEAN": "Typed, validated modelling data",
                       "DW": "Star and snowflake dimensional model", "ML": "Model results, rules and clusters",
                       "ANALYTICS": "What users see: secure view, dynamic table"}
            order = list(purpose)
            sch = sch.assign(purpose=sch["table_schema"].map(purpose)).sort_values("table_schema", key=lambda c: c.map(order.index))
            st.markdown("#### Database `F1_PREDICTION_DB`: schemas created")
            st.dataframe(sch.rename(columns={"table_schema": "Schema"}), width="stretch")
        st.caption(f"Snowflake {e['version']}. Snowflake separates storage (the database, billed per TB) from compute (the virtual warehouse, billed per "
                   "second while running). F1_WH is X-Small and suspends after 60 s idle, so it costs nothing between queries.")
    else:
        st.info(OFFLINE)

with t5:
    st.markdown("Every table of the designed warehouse (`f1_warehouse.db`, Dashboard 1) has a counterpart in Snowflake's `DW` schema, "
                "built by `deploy_to_snowflake.py` step 6b. Row counts are compared live.")
    PAIRS = [("FACT_RACE_RESULTS_STAR", "DW.FACT_RACE_RESULTS_STAR", "Star"), ("DIM_DRIVER", "DW.DIM_DRIVER", "Star"),
             ("DIM_CONSTRUCTOR", "DW.DIM_CONSTRUCTOR", "Star"), ("DIM_RACE_STAR", "DW.DIM_RACE_STAR", "Star"),
             ("DIM_DATE", "DW.DIM_DATE", "Star"), ("FACT_RACE_RESULTS_SNOWFLAKE", "DW.FACT_RACE_RESULTS_SNOWFLAKE", "Snowflake"),
             ("DIM_RACE_SNOWFLAKE", "DW.DIM_RACE_SNOWFLAKE", "Snowflake"), ("DIM_CIRCUIT_SNOWFLAKE", "DW.DIM_CIRCUIT", "Snowflake"),
             ("DIM_COUNTRY", "DW.DIM_COUNTRY", "Snowflake")]
    with sqlite3.connect(os.path.join(ROOT, "f1_warehouse.db")) as db:
        local = {t: db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t, _, _ in PAIRS}
    sf = live_query(" UNION ALL ".join(f"SELECT '{s}' AS tbl, COUNT(*) AS n FROM {s}" for _, s, _ in PAIRS), ["tbl", "n"])
    sf_n = dict(zip(sf["tbl"], sf["n"])) if sf is not None else {}
    st.dataframe(pd.DataFrame([(sch, t, local[t], s, sf_n.get(s), ("✓ match" if sf_n.get(s) == local[t] else "✗ differs") if sf_n else "—")
                               for t, s, sch in PAIRS],
                              columns=["Schema", "Designed table (SQLite)", "Rows", "Snowflake table", "Snowflake rows", "Check"]), width="stretch")
    st.markdown("#### Data loading: `COPY INTO` history")
    loads = live_query("SELECT schema_name || '.' || table_name AS target_table, SPLIT_PART(file_name, '/', -1) AS staged_file, "
                       "row_count AS rows_loaded, error_count AS errors, status, TO_VARCHAR(CONVERT_TIMEZONE('Asia/Kolkata', last_load_time), 'YYYY-MM-DD HH24:MI') AS loaded_at_ist "
                       "FROM F1_PREDICTION_DB.INFORMATION_SCHEMA.LOAD_HISTORY ORDER BY last_load_time", ["target_table", "rows_loaded"])
    if loads is not None:
        st.dataframe(loads, width="stretch")
        st.caption("Files are uploaded with `PUT` to the internal stage `@RAW.F1_RAW_STAGE` (gzip-compressed), then bulk-loaded with "
                   "`COPY INTO`. Snowflake keeps this load history for 14 days.")
    else:
        st.info(OFFLINE)

with t6:
    demo = open(os.path.join(ROOT, "SNOWFLAKE_DEMO_QUERIES.sql"), encoding="utf-8").read()
    blocks = re.findall(r"^-- (\d+)\. ([^\n]+)\n(SELECT.*?;)", demo, re.S | re.M)
    pick = st.selectbox("Query", range(len(blocks)), format_func=lambda i: f"{blocks[i][0]}. {blocks[i][1]}")
    st.code(blocks[pick][2], language="sql")
    if st.button("Run on Snowflake", type="primary", width="stretch"):
        if live:
            t_start = time.perf_counter()
            res = query_snowflake(blocks[pick][2].rstrip(";"))
            st.success(f"Executed on Snowflake warehouse F1_WH in {(time.perf_counter() - t_start) * 1000:.0f} ms: {len(res)} rows")
            st.dataframe(res, width="stretch")
        else:
            st.info(OFFLINE)

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
    This dashboard is also deployed **inside Snowflake** as the native Streamlit app `F1_RACE_INTELLIGENCE`,
    served from the stage `F1_PREDICTION_DB.ANALYTICS.F1_STREAMLIT_STAGE` and running on warehouse `F1_WH`:
    `deploy_streamlit_app.py` uploads every app file with `PUT` → `CREATE STREAMLIT … FROM '@F1_STREAMLIT_STAGE' MAIN_FILE = 'streamlit_app.py'`.
    Inside Snowflake the pages read live tables through the app's own Snowpark session, with no password stored.
    Read-only scripts in `00_data_warehouse/snowflake_streamlit_deployment/` show what is live
    (`SHOW STREAMLITS`, `DESCRIBE STREAMLIT`, `LIST @F1_STREAMLIT_STAGE`, `GET` the deployed `streamlit_app.py`).
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
