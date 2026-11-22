"""
Formula 1 Snowflake & Streamlit Utility Helper
=============================================
Manages Snowflake Snowpark Session / Local Connector with seamless offline fallback:
- Prioritizes snowflake.snowpark.context.get_active_session() in SiS
- Falls back to snowflake.connector with .env credentials
- Falls back to local CSV/JSON in reports/ and data/ when offline
- Provides F1 dark racing theme Plotly styling and metric cards
"""

import os
import re
import html
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Safe environment loading (optional in Snowflake SiS)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

# Design tokens: an FIA classification sheet read with F1 timing-screen colours
PAPER = "#F6F7F9"
SURFACE = "#FFFFFF"
INK = "#15181D"
GRAPHITE = "#59616C"
RULE = "#D8DCE2"
PURPLE = "#7B2CBF"   # timing purple: best / champion
GREEN = "#1A9E55"    # timing green: improvement, passed check
YELLOW = "#C99700"   # timing yellow: caution, notes
FLAG_RED = "#D50F1F" # FIA stripe only
TIER_COLORS = {"Title Contenders": PURPLE, "Midfield Regulars": GREEN, "Backmarkers": "#9AA1AB"}
DISPLAY_FONT = "'DIN Alternate', 'DIN Condensed', Bahnschrift, 'Roboto Condensed', system-ui, sans-serif"
COLORWAY = [PURPLE, GREEN, YELLOW, INK, "#9AA1AB", FLAG_RED, "#2F6FDB"]
SEQ_SCALE = ["#FFFFFF", "#D9C6EE", PURPLE]            # sequential: heatmaps, colour-by-value
DIV_SCALE = [GREEN, "#FFFFFF", PURPLE]                # diverging: correlations (-1 .. +1)
px.defaults.color_discrete_sequence = COLORWAY        # charts without explicit colours use the house palette
px.defaults.color_continuous_scale = SEQ_SCALE

# Legacy names still imported by older pages
F1_RED = PURPLE
F1_DARK_BG = "#0B0D10"
F1_CARD_BG = "#161B22"
F1_BORDER = "#30363D"
F1_TEXT_MUTED = "#8B949E"

# Readable names for column / metric identifiers shown to reviewers
LABELS = {
    "roc_auc": "ROC-AUC", "pr_auc": "PR-AUC", "f1_score": "F1 score", "f1": "F1",
    "davies_bouldin": "Davies-Bouldin", "calinski_harabasz": "Calinski-Harabasz",
    "stability_ari": "Stability (ARI)", "cluster_name": "Tier", "n_clusters": "Clusters",
    "baseline_roc_auc": "Baseline ROC-AUC", "brier_score": "Brier score",
    "norm_prob": "Win probability", "raw_prob": "Raw probability", "target_finish_position": "Finish position",
    "driver_name": "Driver", "constructor_name": "Team",
}
TOKENS = {"pct": "%", "ms": "(ms)", "sec": "(s)", "id": "ID", "auc": "AUC", "ari": "ARI", "dnf": "DNF",
          "pca": "PCA", "gp": "GP", "avg": "avg", "top1": "top-1", "top3": "top-3", "acc": "accuracy",
          "inf": "inference", "std": "std", "mcc": "MCC", "roc": "ROC", "kpi": "KPI", "sql": "SQL",
          "fp": "FP", "fpgrowth": "FP-Growth", "ci": "CI", "quali": "qualifying", "p": "p", "olap": "OLAP"}


def pretty(name):
    """'top1_winner_hit_pct' -> 'Top-1 winner hit %'; anything that is not a snake_case identifier is returned unchanged."""
    if not isinstance(name, str) or not name or name != name.lower() or " " in name or not any(c.isalpha() for c in name):
        return name
    if name in LABELS:
        return LABELS[name]
    if "_" not in name and name not in TOKENS:
        return name[0].upper() + name[1:]
    words = [TOKENS.get(w, w) for w in name.split("_") if w]
    text = " ".join(words)
    return text[0].upper() + text[1:]


assert pretty("top1_winner_hit_pct") == "Top-1 winner hit %" and pretty("pca_1") == "PCA 1"
assert pretty("Title Contenders") == "Title Contenders" and pretty("silhouette") == "Silhouette" and pretty(0.5) == 0.5


def _cell(v):
    """Formats one table cell: thousands separators, at most 4 decimals, a dash for missing."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if isinstance(v, (bool, np.bool_)):
        return "Yes" if v else "No"
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}" if abs(int(v)) >= 10000 else str(int(v))
    if isinstance(v, (float, np.floating)):
        return (f"{v:,.4f}".rstrip("0").rstrip(".") if abs(v) < 10000 else f"{v:,.0f}")
    return html.escape(str(v))


def html_table(df, hide_index=True):
    """Results-sheet table: small header, right-aligned figures, bold first column, champion row highlighted."""
    if not hide_index:
        df = df.reset_index()
    num = [pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c]) for c in df.columns]
    head = "".join(f'<th class="{"n" if n else ""}">{html.escape(str(c))}</th>' for c, n in zip(df.columns, num))
    rows = []
    for r in df.itertuples(index=False):
        hot = any(isinstance(v, str) and "(Champion)" in v for v in r)
        cells = "".join(f'<td class="{"n" if n else ""}">{_cell(v)}</td>' for v, n in zip(r, num))
        rows.append(f'<tr class="{"hot" if hot else ""}">{cells}</tr>')
    return f'<div class="apx-table"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


assert "<b>" not in html_table(pd.DataFrame({"a": ["<b>"]})) and _cell(0.12345) == "0.1235" and _cell(12358) == "12,358"
assert 'class="hot"' not in html_table(pd.DataFrame({"a": ["Championship points"]}))


def _pretty_dataframe(original):
    """Wraps st.dataframe: snake_case headers read as plain words, and small tables render as a styled results sheet."""
    def dataframe(self, data=None, *args, **kwargs):
        if isinstance(data, pd.DataFrame) and kwargs.get("column_config") is None:
            data = data.rename(columns=lambda c: pretty(c) if isinstance(c, str) else c)
            if data.index.name is None and pd.api.types.is_integer_dtype(data.index):  # unnamed row numbers (even re-sorted) mean nothing to a reviewer
                kwargs.setdefault("hide_index", True)
            if len(data) <= 25 and len(data.columns) <= 16 and kwargs.get("height") is None:  # bigger tables stay scrollable grids
                return self.markdown(html_table(data, kwargs.get("hide_index", False)), unsafe_allow_html=True)
        return original(self, data, *args, **kwargs)
    return dataframe


if not getattr(st, "_apx_pretty", False):  # patch once per process
    from streamlit.delta_generator import DeltaGenerator
    DeltaGenerator.dataframe = _pretty_dataframe(DeltaGenerator.dataframe)
    st.dataframe = DeltaGenerator.dataframe.__get__(st.dataframe.__self__)
    st._apx_pretty = True


def apply_f1_theme():
    """Applies the light classification-sheet theme to every page."""
    st.markdown(f"""
        <style>
        /* Base: light classification-sheet layout */
        .stApp {{ background: {PAPER}; color: {INK}; }}
        [data-testid="stHeader"] {{ background: transparent; border-top: 4px solid {FLAG_RED}; }}
        .stApp, .stApp p, .stApp li, .stApp label {{ font-variant-numeric: tabular-nums; }}
        .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
            font-family: {DISPLAY_FONT}; color: {INK}; letter-spacing: -0.005em; font-weight: 700;
        }}
        .stApp h1 {{ font-size: 2.35rem; line-height: 1.1; }}
        .stApp h3 {{ font-size: 1.25rem; }}
        .block-container {{ max-width: 1280px; padding-top: 5.2rem; }}

        /* Sidebar */
        [data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {RULE}; }}
        [data-testid="stSidebarNav"] a span {{ color: {INK}; }}
        /* Title text only: the collapse arrow is an icon-font ligature and must keep its own font */
        [data-testid="stNavSectionHeader"] p {{ font-family: {DISPLAY_FONT}; color: {GRAPHITE}; font-size: 0.95rem;
            white-space: normal; overflow: visible; text-overflow: clip; }}

        /* Metrics read like timing-tower cells */
        [data-testid="stMetric"] {{
            background: {SURFACE}; border: 1px solid {RULE}; border-left: 3px solid {INK};
            border-radius: 4px; padding: 10px 14px;
        }}
        [data-testid="stMetricValue"] {{ font-family: {DISPLAY_FONT}; font-size: 2rem; color: {INK}; }}
        [data-testid="stMetricLabel"] p {{ color: {GRAPHITE}; font-size: 0.85rem; }}

        /* Tabs */
        [data-baseweb="tab"] p {{ font-family: {DISPLAY_FONT}; font-size: 1.02rem; }}

        /* Tables: results sheet in a card (markdown tables and small dataframes) */
        .apx-table {{ background: {SURFACE}; border: 1px solid {RULE}; border-radius: 10px; overflow-x: auto; margin: 0.2rem 0 1rem 0; }}
        .apx-table table, .stMarkdown table {{ border-collapse: collapse; width: 100%; background: {SURFACE}; font-size: 0.92rem; }}
        .stApp th {{ background: {SURFACE}; color: {GRAPHITE}; text-align: left; font-weight: 600; font-size: 0.74rem;
            text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid {RULE}; padding: 10px 12px; white-space: nowrap; }}
        .stApp td {{ border-bottom: 1px solid #EEF0F3; padding: 8px 12px; color: {INK}; }}
        .stApp tbody tr:last-child td {{ border-bottom: none; }}
        .stApp tbody tr:hover td {{ background: #F7F3FC; }}
        .apx-table th, .apx-table td {{ border-left: none !important; border-right: none !important; border-top: none !important; }}
        .apx-table td:first-child {{ font-weight: 600; white-space: nowrap; }}
        .apx-table .n {{ text-align: right; font-variant-numeric: tabular-nums; }}
        .apx-table tr.hot td {{ background: #F3EBFA; }}
        .apx-table tr.hot td:first-child {{ box-shadow: inset 3px 0 0 {PURPLE}; color: {PURPLE}; }}
        [data-testid="stDataFrame"] {{ border: 1px solid {RULE}; border-radius: 10px; overflow: hidden; }}

        /* Charts and diagrams sit in their own card */
        [data-testid="stPlotlyChart"], [data-testid="stGraphVizChart"] {{
            background: {SURFACE}; border: 1px solid {RULE}; border-radius: 10px; padding: 8px 10px; }}

        /* Radios become a segmented control (selectors cover Streamlit 1.52 in Snowflake and 1.67 locally) */
        [data-testid="stRadio"] [role="radiogroup"] {{
            display: inline-flex; flex-wrap: wrap; gap: 2px; background: #EAECEF; border-radius: 9px; padding: 3px; }}
        [data-testid="stRadio"] [role="radiogroup"] label {{ margin: 0; padding: 4px 11px; border-radius: 7px; cursor: pointer; white-space: nowrap; }}
        [data-testid="stRadio"] [role="radiogroup"] label div:not(:has(p)) {{ display: none; }}  /* the radio circle */
        [data-testid="stRadio"] [role="radiogroup"] label p {{ font-size: 0.88rem; color: {GRAPHITE}; }}
        [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {{ background: {SURFACE}; box-shadow: 0 1px 2px rgba(21,24,29,.12); }}
        [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p {{ color: {PURPLE}; font-weight: 600; }}

        /* Dropdowns and widget labels */
        [data-baseweb="select"] > div {{ background: {SURFACE}; border: 1px solid {RULE}; border-radius: 8px; min-height: 40px; }}
        [data-baseweb="select"] > div:hover {{ border-color: {PURPLE}; }}
        [data-testid="stWidgetLabel"] p {{ color: {GRAPHITE}; font-size: 0.82rem; font-weight: 600; }}

        /* Page header component */
        .apx-head {{ border-bottom: 2px solid {INK}; padding-bottom: 0.6rem; margin-bottom: 1.2rem; }}
        .apx-ref {{ display: flex; gap: 0.9rem; align-items: baseline; color: {GRAPHITE}; font-size: 0.95rem; }}
        .apx-ref b {{ font-family: {DISPLAY_FONT}; color: {INK}; font-size: 1.05rem; }}
        .apx-head h1 {{ margin: 0.25rem 0 0.35rem 0; padding: 0; }}
        .apx-sum {{ color: {GRAPHITE}; font-size: 1.05rem; max-width: 75ch; margin: 0; }}

        /* Power BI Visual Card & KPI Design System */
        .pbi-card {{
            background-color: #242424 !important;
            border: 1px solid #383838 !important;
            border-radius: 6px !important;
            padding: 16px 20px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.45) !important;
            transition: all 0.25s ease !important;
        }}
        .pbi-card:hover {{
            border-color: #00BDAE !important;
            box-shadow: 0 6px 18px rgba(0, 189, 174, 0.15) !important;
        }}
        .pbi-header-ribbon {{
            background: linear-gradient(135deg, #1A1A1A 0%, #242424 50%, #1A1A1A 100%) !important;
            border-bottom: 2px solid #00BDAE !important;
            border-radius: 8px !important;
            padding: 14px 22px !important;
            margin-bottom: 18px !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            box-shadow: 0 4px 14px rgba(0,0,0,0.5) !important;
        }}
        .pbi-slicer-panel {{
            background: #1C1C1C !important;
            border: 1px solid #383838 !important;
            border-radius: 8px !important;
            padding: 16px 20px !important;
            margin-bottom: 20px !important;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5) !important;
        }}
        .pbi-kpi-container {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: #242424;
            border: 1px solid #383838;
            border-top: 4px solid #00BDAE;
            border-radius: 6px;
            padding: 14px 18px;
            min-height: 110px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.35);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .pbi-kpi-container:hover {{
            transform: translateY(-2px);
            border-top-color: #00E676;
            box-shadow: 0 6px 16px rgba(0, 230, 118, 0.15);
        }}
        .pbi-kpi-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .pbi-kpi-label {{
            font-size: 11px !important;
            font-weight: 700 !important;
            color: #CCCCCC !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            font-family: 'Segoe UI', sans-serif !important;
        }}
        .pbi-kpi-val {{
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            font-family: 'Segoe UI', -apple-system, sans-serif !important;
            margin: 6px 0 2px 0 !important;
            line-height: 1.1 !important;
        }}
        .pbi-kpi-sub {{
            font-size: 11px !important;
            color: #A0A0A0 !important;
            font-weight: 500 !important;
        }}
        .pbi-pill-filter {{
            display: inline-block;
            background: #2E2E2E;
            color: #00BDAE !important;
            border: 1px solid #4A4A4A;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 4px;
        }}
        .pbi-visual-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333333;
            padding-bottom: 8px;
            margin-bottom: 12px;
        }}
        .pbi-visual-title {{
            font-size: 14px !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        .pbi-visual-actions {{
            color: #888888;
            font-size: 13px;
            display: flex;
            gap: 8px;
        }}
        </style>
    """, unsafe_allow_html=True)

def get_plotly_theme(fig):
    """Formats a Plotly figure in the light classification-sheet style, with readable axis, legend and hover labels."""
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        colorway=COLORWAY,
        font=dict(color=INK, family="system-ui, -apple-system, 'Segoe UI', sans-serif", size=13),
        title=dict(font=dict(size=16, color=INK, family=DISPLAY_FONT), x=0, xanchor="left"),
        margin=dict(l=40, r=30, t=56, b=40),
        xaxis=dict(gridcolor="#E6E9EE", zerolinecolor=RULE, linecolor=RULE),
        yaxis=dict(gridcolor="#E6E9EE", zerolinecolor=RULE, linecolor=RULE),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                    font=dict(size=12, color=GRAPHITE), itemsizing="constant", title=dict(side="left")),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=RULE, font=dict(color=INK)),
        bargap=0.3,
    )
    fig.update_xaxes(gridcolor="#EEF0F3", tickfont=dict(color=GRAPHITE), title_font=dict(color=GRAPHITE, size=12))
    fig.update_yaxes(gridcolor="#EEF0F3", tickfont=dict(color=GRAPHITE), title_font=dict(color=GRAPHITE, size=12))
    if fig.layout.showlegend is not False and sum(1 for tr in fig.data if tr.showlegend is not False) > 1:
        fig.update_layout(margin=dict(t=84))  # room for the title and the legend row under it
    lay = fig.layout
    if lay.title.text:
        lay.title.text = " ".join(pretty(w) if "_" in w else w for w in lay.title.text.split(" "))
    for ax in [k for k in lay.to_plotly_json() if k.startswith(("xaxis", "yaxis"))]:
        if lay[ax].title.text:
            lay[ax].title.text = "" if lay[ax].title.text in ("variable", "index") else pretty(lay[ax].title.text)
    if lay.legend.title.text:
        lay.legend.title.text = "" if lay.legend.title.text in ("color", "variable") else pretty(lay.legend.title.text)
    if lay.coloraxis.colorbar.title.text:
        lay.coloraxis.colorbar.title.text = pretty(lay.coloraxis.colorbar.title.text)
    for axis, attr in (("xaxis", "x"), ("yaxis", "y")):  # display-only relabel of snake_case category ticks
        cats = {v for tr in fig.data for v in (getattr(tr, attr, None) if getattr(tr, attr, None) is not None else []) if isinstance(v, str)}
        alias = {c: pretty(c) for c in cats if pretty(c) != c}
        if alias:
            fig.update_layout({axis: dict(labelalias=alias)})
    for tr in fig.data:  # radar charts label their spokes from theta
        if getattr(tr, "theta", None) is not None:
            tr.theta = [pretty(t) for t in tr.theta]
    for tr in fig.data:  # plotly express hover text reads "col_name=%{x}"
        if getattr(tr, "hovertemplate", None):
            tr.hovertemplate = re.sub(r"([a-z0-9_]+)=%", lambda m: pretty(m.group(1)) + "=%", tr.hovertemplate)
    return fig


def page_header(dashboard: str, area: str, title: str, summary: str):
    """Shared page heading: which dashboard and area this page belongs to, then the title."""
    st.markdown(f"""<div class="apx-head">
        <div class="apx-ref"><b>{dashboard}</b><span>{area}</span></div>
        <h1>{title}</h1><p class="apx-sum">{summary}</p></div>""", unsafe_allow_html=True)


def get_pbi_plotly_theme(fig):
    """Formats Plotly figure with authentic Microsoft Power BI Dark Visual styling."""
    fig.update_layout(
        paper_bgcolor="#242424",
        plot_bgcolor="#1E1E1E",
        font=dict(color="#FFFFFF", family="'Segoe UI', -apple-system, sans-serif", size=11),
        title=dict(font=dict(size=14, color="#FFFFFF", family="'Segoe UI', sans-serif")),
        margin=dict(l=35, r=35, t=45, b=35),
        xaxis=dict(
            gridcolor="#333333",
            zerolinecolor="#4A4A4A",
            tickfont=dict(color="#CCCCCC", size=10)
        ),
        yaxis=dict(
            gridcolor="#333333",
            zerolinecolor="#4A4A4A",
            tickfont=dict(color="#CCCCCC", size=10)
        ),
        colorway=["#00BDAE", "#E10600", "#F2C811", "#118DFF", "#00E676", "#E66C37", "#A05BF5", "#8B949E"],
        legend=dict(
            bgcolor="rgba(36,36,36,0.85)",
            bordercolor="#383838",
            font=dict(color="#CCCCCC", size=10)
        )
    )
    return fig

def render_pbi_header(title: str, subtitle: str, page_name: str = "Page 1", filters_summary: str = ""):
    """Renders a Power BI Desktop / Service top ribbon bar."""
    st.markdown(f"""
        <div class="pbi-header-ribbon">
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #F2C811; color: #121212; padding: 2px 7px; border-radius: 3px; font-weight: 900; font-size: 11px; letter-spacing: 0.5px;">POWER BI</span>
                    <h2 style="margin: 0; color: #FFFFFF; font-size: 20px; font-weight: 700;">{title}</h2>
                </div>
                <div style="color: #A0A0A0; font-size: 12px; margin-top: 3px;">
                    {subtitle}
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: #2E2E2E; color: #00BDAE; border: 1px solid #4A4A4A; padding: 4px 12px; border-radius: 14px; font-size: 11px; font-weight: 600;">
                    📊 {page_name}
                </span>
                <div style="color: #00E676; font-size: 10px; margin-top: 4px; font-weight: 600;">
                    ● Slicers Connected &bull; Real-Time Cross-Filtering
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    if filters_summary:
        st.markdown(f"""
            <div style="background: #1A1A1A; border: 1px solid #333333; padding: 6px 14px; border-radius: 6px; margin-top: -10px; margin-bottom: 16px; font-size: 11px; color: #AAAAAA;">
                <b style="color: #F2C811;">Active Slicers:</b> {filters_summary}
            </div>
        """, unsafe_allow_html=True)

def render_pbi_kpi(label: str, value: str, delta: str = None, delta_color: str = "#00E676", subtext: str = "", accent: str = "#00BDAE", icon: str = "📊"):
    """Renders a high-contrast Power BI KPI Card visual."""
    delta_html = f'<span style="color: {delta_color}; font-size: 11px; font-weight: 700; margin-left: 8px;">{delta}</span>' if delta else ''
    st.markdown(f"""
        <div class="pbi-kpi-container" style="border-top-color: {accent};">
            <div class="pbi-kpi-header">
                <span class="pbi-kpi-label">{label}</span>
                <span style="font-size: 14px; opacity: 0.85;">{icon}</span>
            </div>
            <div>
                <div class="pbi-kpi-val" style="color: {accent};">
                    {value} {delta_html}
                </div>
                <div class="pbi-kpi-sub">{subtext}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_snowflake_session():
    """Returns active Snowpark session, local connector, or None."""
    # 1. Check for active Streamlit in Snowflake (SiS) context
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        if session:
            return ("snowpark", session)
    except Exception:
        pass

    # 2. Check for local connector using credentials in .env
    acc = os.getenv("SNOWFLAKE_ACCOUNT", "")
    usr = os.getenv("SNOWFLAKE_USER", "")
    pwd = os.getenv("SNOWFLAKE_PASSWORD", "")
    if acc and acc != "your_snowflake_account_identifier" and usr and pwd:
        try:
            import snowflake.connector
            conn = snowflake.connector.connect(
                user=usr,
                password=pwd,
                account=acc,
                warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "F1_WH"),
                database=os.getenv("SNOWFLAKE_DATABASE", "F1_PREDICTION_DB"),
                schema=os.getenv("SNOWFLAKE_SCHEMA", "CLEAN")
            )
            return ("connector", conn)
        except Exception:
            pass

    return ("offline", None)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes all DataFrame column names to lowercase for seamless cross-compatibility."""
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

@st.cache_data(ttl=600)
def query_snowflake(sql_query: str) -> pd.DataFrame:
    """Executes SQL against Snowflake with column normalization, or falls back to local data."""
    conn_type, session = get_snowflake_session()
    
    if conn_type == "snowpark" and session:
        try:
            df = session.sql(sql_query).to_pandas()
            return normalize_columns(df)
        except Exception as e:
            st.warning(f"Snowpark SQL execution error: {e}. Falling back to cached data.")

    elif conn_type == "connector" and session:
        try:
            df = pd.read_sql(sql_query, session)
            return normalize_columns(df)
        except Exception as e:
            st.warning(f"Snowflake connector query error: {e}. Falling back to cached data.")

    # Fallback to local clean master dataset
    return get_local_data("clean_f1_modeling_master.csv")

@st.cache_data
def get_local_data(filename: str) -> pd.DataFrame:
    """Loads CSV from data/ or reports/ safely across all candidate project directories."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "data", filename),
        os.path.join(os.path.dirname(__file__), "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "reports", filename),
        os.path.join(os.path.dirname(__file__), "04_pattern_mining", filename),
        os.path.join(os.path.dirname(__file__), "..", filename)
    ]

    # Handle common filename variations
    if "association_rules" in filename:
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "reports", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "04_pattern_mining", "association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", "f1_association_rules.csv"),
            os.path.join(os.path.dirname(__file__), "..", "ASSOC_RULES.csv")
        ])
    elif "frequent_itemsets" in filename:
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "reports", "f1_frequent_itemsets.csv"),
            os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", "f1_frequent_itemsets.csv")
        ])

    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, low_memory=False)
                return normalize_columns(df)
            except Exception:
                pass

    # If clean_f1_modeling_master.csv is requested and not found locally, query Snowflake directly
    if "modeling_master" in filename:
        try:
            return query_snowflake("SELECT * FROM CLEAN.F1_MODELING_MASTER")
        except Exception:
            pass

    return pd.DataFrame()

@st.cache_data
def get_local_json(filename: str) -> dict:
    """Loads JSON file from reports/ safely across candidate directories."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "reports", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "reports", filename),
        os.path.join(os.path.dirname(__file__), "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "snowflake_f1", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", filename)
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}
