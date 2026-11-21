import os
import re
import sys
import sqlite3
import streamlit as st
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db_utils import apply_f1_theme, page_header

apply_f1_theme()

DW = os.path.join(ROOT, "00_data_warehouse")
DB = os.path.join(ROOT, "f1_warehouse.db")

page_header('Dashboard 1', 'Data warehouse', 'Warehouse design',
            'Star and snowflake models over 8,650 race results (2004–2024), with OLAP queries running live on the warehouse.', marks=3)


def mermaid_er_to_dot(path):
    """Converts a Mermaid erDiagram file into Graphviz DOT (renders offline in Streamlit)."""
    text = open(path, encoding="utf-8").read()
    entities = re.findall(r"^\s*(\w+)\s*\{(.*?)^\s*\}", text, re.S | re.M)
    rels = re.findall(r"^\s*(\w+)\s+\S+--\S+\s+(\w+)\s*:\s*\"?([\w\s]+)\"?", text, re.M)
    lines = ['digraph ER { rankdir=LR; bgcolor="transparent"; nodesep=0.3; ranksep=1.2;',
             'node [shape=record, style=filled, fontname="Helvetica", fontsize=11, fontcolor="white", color="#30363D"];',
             'edge [color="#59616C", fontcolor="#59616C", fontname="Helvetica", fontsize=10, arrowhead=crow, arrowtail=tee, dir=both];']
    for name, body in entities:
        cols = [c.split() for c in body.strip().splitlines() if c.strip()]
        shown = [f"{c[1]}{'  [' + c[2] + ']' if len(c) > 2 else ''}" for c in cols[:12]]
        if len(cols) > 12:
            shown.append(f"… +{len(cols) - 12} more")
        fill = "#15181D" if name.startswith("FACT") else "#3B5B8A"
        fields = "".join(s + "\\l" for s in shown)  # \l = left-justified line break in a Graphviz record
        lines.append(f'{name} [fillcolor="{fill}", label="{{{name}|{fields}}}"];')
    for a, b, label in rels:
        lines.append(f'{a} -> {b} [label="{label.strip()} (1:N)"];')
    lines.append("}")
    return "\n".join(lines)


@st.cache_data
def table_counts():
    with sqlite3.connect(DB) as c:
        names = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return pd.DataFrame([(n, c.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]) for n in names], columns=["table", "rows"])


@st.cache_data
def olap_queries():
    content = open(os.path.join(DW, "olap_queries.sql"), encoding="utf-8").read()
    out = []
    for block in re.findall(r"(-- QUERY \d+:.*?)(?=(?:-- QUERY \d+:|\Z))", content, re.S):
        lines = block.strip().splitlines()
        title = lines[0].replace("--", "").strip()
        desc = " ".join(l.replace("--", "").strip() for l in lines[1:4] if l.startswith("--") and "----" not in l)
        sql = "\n".join(l for l in lines if not l.strip().startswith("--")).strip()
        out.append((title, desc, sql))
    return out


counts = table_counts()
star_fact = int(counts.loc[counts["table"] == "FACT_RACE_RESULTS_STAR", "rows"].iat[0])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Warehouse Tables", len(counts))
c2.metric("Fact Rows (Star)", f"{star_fact:,}", "1 row = driver × Grand Prix")
c3.metric("Lap-Time Fact Rows", f"{int(counts.loc[counts['table'] == 'FACT_LAP_TIMES', 'rows'].iat[0]):,}")
c4.metric("OLAP Queries", len(olap_queries()), "Roll-up · Drill-down · Slice · Dice · Pivot")

st.markdown("---")
t1, t2, t3, t4, t5 = st.tabs(["Star Schema", "Snowflake Schema", "Star vs. Snowflake", "Live OLAP Queries", "Tables & ETL"])

with t1:
    st.markdown("**Fact constellation (galaxy) schema:** two fact tables share conformed dimensions. "
                "`FACT_RACE_RESULTS` (grain: 1 driver × 1 Grand Prix, 8,650 rows) and `FACT_LAP_TIMES` (grain: 1 driver × 1 lap, 296,727 rows), "
                "joined directly (1 hop) to 7 dimensions. Generated from `create_star_schema.sql`.")
    st.graphviz_chart(mermaid_er_to_dot(os.path.join(DW, "er_diagram_star.mmd")), width="stretch")

with t2:
    st.markdown("Dimensions are **normalised** into 15 tables: e.g. `DIM_RACE_SNOWFLAKE → DIM_CIRCUIT_SNOWFLAKE → DIM_COUNTRY`, "
                "`DIM_CONSTRUCTOR_SNOWFLAKE → DIM_ENGINE_SUPPLIER / DIM_TEAM_PRINCIPAL / DIM_LIVERY_SPONSOR`, plus slowly-changing history "
                "(`DIM_DRIVER_NUMBER_HISTORY`, `DIM_CIRCUIT_LAYOUT_HISTORY`). Generated from `create_snowflake_schema.sql`.")
    st.graphviz_chart(mermaid_er_to_dot(os.path.join(DW, "er_diagram_snowflake.mmd")), width="stretch")

with t3:
    st.markdown("""
    | | ⭐ Star Schema | ❄️ Snowflake Schema |
    |---|---|---|
    | Tables | 9 (2 facts + 7 dimensions) | 15 (2 facts + 13 dimensions / sub-dimensions) |
    | Dimension design | Denormalised (circuit inlined in `DIM_RACE`) | Normalised (circuit, country, nationality, engine supplier, team principal, sponsor split out) |
    | Joins per query | 1 hop | 2–3 hops |
    | Query latency | **Lower**: best for dashboards & OLAP cubes | Higher |
    | Storage / redundancy | Higher (repeated text) | **Lower**: each attribute stored once |
    | Update anomalies | Possible | **Avoided** |
    | Our use | Power BI / Streamlit analytics, OLAP cube | Reference data integrity, Snowflake Cloud |

    **Measures** in the fact: grid, finish, points, laps, pit-stop count & duration, fastest lap, standings, flags (`is_win`, `is_podium`, `is_dnf`).
    **Dimensions:** Driver, Constructor, Race (+ Circuit), Status, Date (day → month → quarter → season hierarchy for roll-up), Session, Tyre Compound.
    **Slowly changing dimensions (snowflake side):** driver number history and circuit layout history keep past versions instead of overwriting them (SCD Type 2 style).
    """)
    st.code(open(os.path.join(DW, "create_star_schema.sql"), encoding="utf-8").read(), language="sql")

with t4:
    queries = olap_queries()
    choice = st.selectbox("OLAP operation", range(len(queries)), format_func=lambda i: queries[i][0])
    title, desc, sql = queries[choice]
    st.caption(desc)
    st.code(sql, language="sql")
    try:
        with sqlite3.connect(DB) as c:
            res = pd.read_sql(sql, c)
        st.success(f"Executed live against f1_warehouse.db: {len(res):,} rows")
        st.dataframe(res, width="stretch", height=360)
    except Exception as e:
        st.error(f"Query failed: {e}")

with t5:
    st.dataframe(counts, width="stretch", hide_index=True, height=360)
    st.markdown("**ETL lineage:** Ergast CSVs → `etl_master_ingestion.py` (extract, clean, conform keys) → "
                "`F1_Warehouse_Master_65_Columns_2004_2024.csv` → star & snowflake loads → `f1_warehouse.db` → Snowflake (`MASTER_SNOWFLAKE_DEPLOYMENT.sql`).")
    # The mapping file has unquoted commas inside types like DECIMAL(9,6): split the first 4 fields, then peel the type off the end
    rows = []
    for line in open(os.path.join(DW, "source_to_target_mapping.csv"), encoding="utf-8").read().splitlines()[1:]:
        head, rest = line.split(",", 4)[:4], line.split(",", 4)[4]
        m = re.match(r"^(.*),([A-Z]+(?:\(\d+(?:,\d+)?\))?)$", rest)
        rows.append(head + ([m.group(1), m.group(2)] if m else [rest, ""]))
    st.dataframe(pd.DataFrame(rows, columns=["source_file", "source_column", "target_table", "target_column", "transformation", "data_type"]),
                 width="stretch", height=300)
