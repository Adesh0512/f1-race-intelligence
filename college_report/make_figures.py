"""Charts and diagrams for the college-format project report, drawn from the module output files.

Usage: python college_report/make_figures.py   (writes college_report/figures/*.png)
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "college_report", "figures")
PURPLE, GREY, GREEN, INK = "#6A2C9E", "#9AA1AB", "#3E8E41", "#222222"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#555555", "axes.titlesize": 10})


def src(*p):
    return os.path.join(ROOT, *p)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200)
    plt.close(fig)


def box(ax, x, y, w, h, text, fill="white", edge=INK, color=INK, size=7.2, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fill, ec=edge, lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=color, weight="bold" if bold else "normal",
            wrap=True)


def arrow(ax, x1, y1, x2, y2, text=None):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, text, ha="center", fontsize=7.5, color="#444444")


def canvas(w, h, xmax, ymax):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xmax), ax.set_ylim(0, ymax), ax.axis("off")
    return fig, ax


def pipeline():
    fig, ax = canvas(7.2, 2.6, 15, 5.2)
    steps = [("f1.zip\n14 CSV files\n1950–2024", "white"), ("RAW\nfiles loaded\nas-is", "#F2F2F2"),
             ("CLEAN\ntyped and\nvalidated", "#F2F2F2"), ("DW\nstar and\nsnowflake", "#EDE3F6"),
             ("ML\nfeatures and\npredictions", "#EDE3F6"), ("ANALYTICS\nviews and\ndashboards", "#E3ECD6")]
    for i, (t, f) in enumerate(steps):
        box(ax, 0.2 + i * 2.5, 1.6, 2.0, 2.0, t, fill=f, size=7.5)
        if i:
            arrow(ax, 0.2 + i * 2.5 - 0.5, 2.6, 0.2 + i * 2.5, 2.6)
    ax.text(7.5, 0.6, "Locally: Python ETL into SQLite (f1_warehouse.db).   In Snowflake: PUT + COPY INTO RAW, then SQL ELT inside the warehouse.",
            ha="center", fontsize=8, color="#444444")
    save(fig, "f_pipeline")


def architecture():
    fig, ax = canvas(7.2, 4.6, 15, 9.6)
    box(ax, 0.3, 7.6, 3.2, 1.4, "Source data\nf1.zip (1950–2024)\nJolpica-F1 (2025–26)", "#F2F2F2")
    box(ax, 4.6, 7.6, 4.4, 1.4, "Data warehouse (SQLite)\n33 tables, star + snowflake\n12 OLAP queries", "#EDE3F6")
    box(ax, 10.1, 7.6, 4.6, 1.4, "Snowflake cloud\nF1_PREDICTION_DB, 5 schemas\n42 objects", "#EDE3F6")
    arrow(ax, 3.5, 8.3, 4.6, 8.3, "ETL")
    arrow(ax, 9.0, 8.3, 10.1, 8.3, "deploy")
    box(ax, 0.3, 4.4, 4.4, 1.9, "Supervised learning\n12,358 labelled entries, 16 features\nFP-Growth + Apriori, 7 classifiers,\ncost-sensitive XGBoost", "white")
    box(ax, 5.3, 4.4, 4.4, 1.9, "Unsupervised learning\n703 driver-season profiles\n6 clustering algorithms,\nK-Means k = 3 tiers", "white")
    box(ax, 10.3, 4.4, 4.4, 1.9, "Race forecaster\n16 features rebuilt up to the\nlatest race; next Grand Prix\nwin probability per driver", "white")
    for x in (2.5, 7.5, 12.5):
        arrow(ax, 6.8 if x == 7.5 else x, 7.6, x, 6.3)
    box(ax, 0.3, 1.0, 4.4, 1.8, "Streamlit dashboard\n3 dashboards, 15 pages\n(local and inside Snowflake)", "#E3ECD6")
    box(ax, 5.3, 1.0, 4.4, 1.8, "Power BI report\n13 pages, 116 visuals,\nslicers and KPI cards", "#E3ECD6")
    box(ax, 10.3, 1.0, 4.4, 1.8, "Snowsight worksheets\nread-only SQL for\nthe examiner", "#E3ECD6")
    for x in (2.5, 7.5, 12.5):
        arrow(ax, x, 4.4, x, 2.8)
    save(fig, "f_architecture")


def use_cases():
    fig, ax = canvas(7.2, 4.4, 15, 9)
    for (x, y, name) in [(1.1, 5.6, "Examiner /\nanalyst"), (13.9, 5.6, "Data\nengineer")]:
        ax.add_patch(plt.Circle((x, y + 1.3), 0.35, fc="white", ec=INK))
        ax.plot([x, x], [y + 0.95, y + 0.1], color=INK), ax.plot([x - 0.5, x + 0.5], [y + 0.7, y + 0.7], color=INK)
        ax.plot([x, x - 0.4], [y + 0.1, y - 0.5], color=INK), ax.plot([x, x + 0.4], [y + 0.1, y - 0.5], color=INK)
        ax.text(x, y - 1.2, name, ha="center", fontsize=8.5)
    ax.add_patch(FancyBboxPatch((3.0, 0.4), 9.0, 8.2, boxstyle="round,pad=0.02", fc="none", ec="#888888", ls="--"))
    ax.text(7.5, 8.25, "ApexIQ", ha="center", fontsize=9, weight="bold")
    left = ["Explore the warehouse (OLAP)", "Review mining rules", "Compare classifiers", "Forecast the next race",
            "Change race parameters", "Explore driver tiers"]
    right = ["Run the ETL pipeline", "Deploy to Snowflake", "Retrain all modules", "Run automated tests"]
    for i, t in enumerate(left):
        y = 7.2 - i * 1.15
        ax.add_patch(matplotlib.patches.Ellipse((6.0, y), 4.6, 0.85, fc="#F6F1FA", ec=PURPLE))
        ax.text(6.0, y, t, ha="center", va="center", fontsize=8)
        ax.plot([1.6, 3.7], [6.4, y], color="#888888", lw=0.7)
    for i, t in enumerate(right):
        y = 6.6 - i * 1.3
        ax.add_patch(matplotlib.patches.Ellipse((10.0, y), 3.6, 0.85, fc="#EEF4E6", ec=GREEN))
        ax.text(10.0, y, t, ha="center", va="center", fontsize=8)
        ax.plot([13.4, 11.8], [6.4, y], color="#888888", lw=0.7)
    save(fig, "f_use_cases")


def sequence():
    fig, ax = canvas(7.2, 4.2, 15, 9)
    actors = ["User", "Dashboard", "Forecast engine", "History store", "XGBoost model"]
    xs = [1.2, 4.3, 7.4, 10.5, 13.6]
    for x, a in zip(xs, actors):
        box(ax, x - 1.2, 7.9, 2.4, 0.8, a, "#F2F2F2", size=8)
        ax.plot([x, x], [0.3, 7.9], color="#AAAAAA", ls="--", lw=0.8)
    msgs = [(0, 1, "pick race, pole, driver parameters"), (1, 2, "forecast(lineup, circuit, date)"),
            (2, 3, "results before race date"), (3, 2, "driver, team and circuit history"),
            (2, 2, "rebuild 16 features per driver"), (2, 4, "predict_proba(features)"), (4, 2, "raw win scores"),
            (2, 2, "race softmax: sum = 100%"), (2, 1, "ranked win probabilities"), (1, 0, "podium, chart, reasons")]
    for i, (a, b, t) in enumerate(msgs):
        y = 7.3 - i * 0.68
        if a == b:
            ax.annotate("", (xs[a] + 0.05, y - 0.3), (xs[a] + 0.05, y), arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-1.2", color="#555555"))
            ax.text(xs[a] + 0.6, y - 0.15, t, fontsize=7.5)
        else:
            ax.annotate("", (xs[b], y), (xs[a], y), arrowprops=dict(arrowstyle="-|>", color=PURPLE if b > a else "#555555",
                                                                    ls="-" if b > a else "--"))
            ax.text((xs[a] + xs[b]) / 2, y + 0.08, t, ha="center", fontsize=7.5)
    save(fig, "f_sequence")


def dev_model():
    fig, ax = canvas(6.4, 2.6, 13, 5)
    steps = ["Requirements\n(rubric + jury)", "Design\n(schema, features)", "Build\n(module code)", "Validate\n(tests, holdout)", "Review\n(guide, jury)"]
    for i, s in enumerate(steps):
        box(ax, 0.2 + i * 2.55, 2.0, 2.1, 1.4, s, "#F2F2F2" if i % 2 else "#EDE3F6", size=8)
        if i:
            arrow(ax, 0.2 + i * 2.55 - 0.45, 2.7, 0.2 + i * 2.55, 2.7)
    ax.annotate("", (1.25, 2.0), (11.65, 2.0), arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-0.25", color=PURPLE))
    ax.text(6.4, 0.35, "repeated for each of the three dashboards", ha="center", fontsize=8, color=PURPLE)
    save(fig, "f_dev_model")


def gantt():
    tasks = [("Dataset study and class labels", "2026-08-03", "2026-08-23"), ("Warehouse design and ETL", "2026-08-17", "2026-09-13"),
             ("OLAP queries and Snowflake deployment", "2026-09-07", "2026-10-04"), ("Pattern mining", "2026-09-28", "2026-10-11"),
             ("Classifier comparison and champion", "2026-10-05", "2026-10-30"), ("Clustering (Dashboard 3)", "2026-10-26", "2026-11-15"),
             ("Dashboards and Power BI", "2026-10-19", "2026-11-22"), ("Next-race forecaster", "2026-11-09", "2026-11-22"),
             ("Testing and report", "2026-11-02", "2026-11-23")]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    for i, (t, a, b) in enumerate(tasks[::-1]):
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        ax.barh(i, (b - a).days, left=matplotlib.dates.date2num(a), color=PURPLE if i % 2 else "#A57BC8", height=0.55)
    ax.set_yticks(range(len(tasks)), [t[0] for t in tasks[::-1]])
    ax.xaxis_date(), ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    ax.grid(axis="x", color="#DDDDDD", lw=0.6)
    save(fig, "f_gantt")


def mining_sweep():
    s = pd.read_csv(src("04_pattern_mining", "support_sweep_benchmark.csv")).sort_values("min_support", ascending=False)
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8))
    x = s["min_support"].astype(str)
    a.plot(x, s["apriori_candidates"], "o-", color=GREY, label="Apriori candidates")
    a.plot(x, s["fp_tree_nodes"], "s-", color=PURPLE, label="FP-tree nodes")
    a.set_xlabel("Minimum support"), a.set_ylabel("Count"), a.set_title("Search space"), a.legend(frameon=False, fontsize=7.5)
    b.plot(x, s["apriori_time_sec"] * 1000, "o-", color=GREY, label="Apriori")
    b.plot(x, s["fpgrowth_time_sec"] * 1000, "s-", color=PURPLE, label="FP-Growth")
    b.set_xlabel("Minimum support"), b.set_ylabel("Runtime (ms)"), b.set_title("Runtime"), b.legend(frameon=False, fontsize=7.5)
    save(fig, "f_mining_sweep")


def classifiers():
    c = pd.read_csv(src("05_algorithm_comparison", "comparison_results.csv"))
    c["name"] = c["algorithm"].str.replace(r"^\d+\.\s*", "", regex=True).str.replace(" Classifier", "").str.replace(" (Champion)", "")
    c = c.sort_values("pr_auc")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    col = [PURPLE if "XGBoost" in n else GREY for n in c["name"]]
    a.barh(c["name"], c["pr_auc"], color=col), a.set_title("PR-AUC (higher is better)"), a.set_xlim(0, 0.75)
    b.barh(c["name"], c["top1_winner_hit_pct"], color=col), b.set_title("Winner picked, % of 68 races"), b.set_xlim(0, 70)
    for ax, k, f in ((a, "pr_auc", "{:.3f}"), (b, "top1_winner_hit_pct", "{:.1f}")):
        for i, v in enumerate(c[k]):
            ax.text(v + 0.5 if k != "pr_auc" else v + 0.01, i, f.format(v), va="center", fontsize=7.5)
    save(fig, "f_classifiers")


def confusion():
    m = pd.read_csv(src("08_performance_metrics", "confusion_matrix.csv"), index_col=0).values
    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    ax.imshow(m, cmap="Purples", vmax=m.max() * 1.4)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{m[i, j]:,}", ha="center", va="center", fontsize=12, color="white" if i == j == 0 else INK)
    ax.set_xticks([0, 1], ["Predicted\nnon-winner", "Predicted\nwinner"]), ax.set_yticks([0, 1], ["Actual\nnon-winner", "Actual\nwinner"])
    ax.spines[:].set_visible(False)
    save(fig, "f_confusion")


def importance():
    f = pd.read_csv(src("06_classification_algorithm", "feature_importance.csv")).sort_values("importance")
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.barh(f["feature"], f["importance"] * 100, color=[PURPLE if v > 0.09 else GREY for v in f["importance"]])
    ax.set_xlabel("Importance (% of total gain)")
    save(fig, "f_importance")


def temporal_cv():
    t = pd.read_csv(src("05_algorithm_comparison", "temporal_validation_results.csv"))
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    ax.plot(t["test_season"], t["roc_auc"], "o-", color=PURPLE, label="Cost-sensitive XGBoost")
    ax.plot(t["test_season"], t["baseline_roc_auc"], "s--", color=GREY, label="Grid-only logistic baseline")
    ax.set_xlabel("Test season (trained on 1994 to the season before)"), ax.set_ylabel("ROC-AUC"), ax.legend(frameon=False)
    save(fig, "f_temporal_cv")


def k_selection():
    k = pd.read_csv(src("10_clustering_comparison", "k_selection.csv"))
    fig, a = plt.subplots(figsize=(6.0, 2.8))
    a.plot(k["k"], k["inertia"], "o-", color=PURPLE), a.set_xlabel("Number of clusters k"), a.set_ylabel("Inertia (WCSS)", color=PURPLE)
    b = a.twinx()
    b.plot(k["k"], k["silhouette"], "s--", color=GREY), b.set_ylabel("Silhouette", color="#666666")
    b.spines["right"].set_visible(True)
    a.axvline(3, color=GREEN, lw=1, ls=":"), a.text(3.1, k["inertia"].max() * 0.97, "chosen k = 3", color=GREEN, fontsize=8)
    save(fig, "f_k_selection")


def championship():
    c = pd.read_csv(src("12_clustering_metrics", "championship_contingency.csv"), index_col=0)
    fig, ax = plt.subplots(figsize=(6.0, 2.6))
    left = 0
    for col, colour in zip(c.columns, [PURPLE, "#A57BC8", "#D9D9D9"]):
        ax.barh(c.index[::-1], c[col][::-1], left=left, color=colour, label=f"Championship {col}")
        left = left + c[col][::-1].values
    ax.set_xlabel("Driver-seasons"), ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    save(fig, "f_championship")


def real_world():
    t = pd.read_csv(src("06_classification_algorithm", "real_world_test.csv"))
    g = t.groupby("season")[["model_correct", "pole_correct"]].sum()
    n = t.groupby("season").size()
    fig, ax = plt.subplots(figsize=(5.4, 2.8))
    x = range(len(g))
    ax.bar([i - 0.18 for i in x], g["model_correct"], 0.36, color=PURPLE, label="Model")
    ax.bar([i + 0.18 for i in x], g["pole_correct"], 0.36, color=GREY, label="Pole-sitter")
    for i, s in enumerate(g.index):
        ax.text(i - 0.18, g.loc[s, "model_correct"] + 0.3, f"{g.loc[s, 'model_correct']}/{n[s]}", ha="center", fontsize=8)
        ax.text(i + 0.18, g.loc[s, "pole_correct"] + 0.3, f"{g.loc[s, 'pole_correct']}/{n[s]}", ha="center", fontsize=8)
    ax.set_xticks(list(x), g.index.astype(str)), ax.set_ylabel("Winners called"), ax.set_ylim(0, 21)
    ax.legend(frameon=False, ncol=2, loc="upper center")
    save(fig, "f_real_world")


def forecast():
    f = pd.read_csv(src("06_classification_algorithm", "forecast_upcoming.csv"))
    q = f[f["round"] == f["round"].min()].sort_values("win_probability").tail(10)
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    ax.barh(q["driver_name"], q["win_probability"], color=[PURPLE if r == 1 else GREY for r in q["predicted_rank"]])
    for i, v in enumerate(q["win_probability"]):
        ax.text(v + 0.4, i, f"{v:.1f}%", va="center", fontsize=8)
    ax.set_xlabel(f"Win probability (%), {q['race_name'].iat[0]} {q['season'].iat[0]}")
    save(fig, "f_forecast")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fn in (pipeline, architecture, use_cases, sequence, dev_model, gantt, mining_sweep, classifiers, confusion, importance,
               temporal_cv, k_selection, championship, real_world, forecast):
        fn()
    print(f"[+] {len(os.listdir(OUT))} figures in {OUT}")
    assert json.load(open(src("12_clustering_metrics", "clustering_metrics.json")))["k"] == 3
