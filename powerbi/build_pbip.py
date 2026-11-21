"""
Builds a Power BI Project (.pbip) from the module output files.
Open powerbi/ApexIQ_F1_Dashboard/ApexIQ_F1_Dashboard.pbip in Power BI Desktop (Windows),
then File -> Save as -> .pbix.

Data is embedded in each table the same way Power BI's "Enter data" stores it
(deflate-compressed JSON rows in the M query), so the project opens on any PC
without fixing file paths.
Usage: .venv/bin/python powerbi/build_pbip.py
"""

import base64
import json
import os
import shutil
import uuid
import zlib

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NAME = "ApexIQ_F1_Dashboard"
OUT = os.path.join(ROOT, "powerbi", NAME)
SM, RP = f"{NAME}.SemanticModel", f"{NAME}.Report"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"


def src(*p):
    return pd.read_csv(os.path.join(ROOT, *p))


# ---------------------------------------------------------------- tables
def tables():
    fact = src("06_classification_algorithm", "holdout_predictions.csv")
    fact["predicted_rank"] = fact.groupby("race_id")["norm_prob"].rank(ascending=False, method="first").astype(int)
    fact["is_winner_hit"] = ((fact["predicted_rank"] == 1) & (fact["target_is_win"] == 1)).astype(int)
    fact["winner_in_top3"] = ((fact["predicted_rank"] <= 3) & (fact["target_is_win"] == 1)).astype(int)
    fact["race"] = fact["season"].astype(str) + " " + fact["race_name"]
    fact["win_probability_pct"] = (fact["norm_prob"] * 100).round(2)
    fact = fact[["race_id", "season", "race", "driver_name", "constructor_name", "grid_position",
                 "target_finish_position", "target_is_win", "win_probability_pct", "predicted_rank", "is_winner_hit", "winner_in_top3"]]

    models = src("05_algorithm_comparison", "comparison_results.csv")
    models["model"] = models["algorithm"].str.replace(r"^\d+\.\s*", "", regex=True)
    models = models[["model", "roc_auc", "pr_auc", "recall", "top1_winner_hit_pct", "top3_podium_hit_pct"]]

    folds = src("05_algorithm_comparison", "temporal_validation_results.csv")[["test_season", "roc_auc", "baseline_roc_auc"]]
    feats = src("06_classification_algorithm", "feature_importance.csv")
    feats["importance_pct"] = (feats["importance"] * 100).round(2)
    feats = feats[["feature", "importance_pct"]]

    rules = src("04_pattern_mining", "association_rules.csv")[["antecedents", "consequents", "support", "confidence", "lift"]].round(4)

    clusters = src("11_clustering_algorithm", "driver_season_clusters.csv")
    clusters["driver_season"] = clusters["driver_name"] + " " + clusters["season"].astype(str)
    clusters = clusters[["driver_season", "driver_name", "season", "constructor_name", "cluster_name",
                         "avg_grid", "avg_finish", "win_rate", "podium_rate", "pca_1", "pca_2"]].round(4)

    algos = src("10_clustering_comparison", "comparison_results.csv")[
        ["algorithm", "n_clusters", "noise_pct", "silhouette", "davies_bouldin", "calinski_harabasz", "stability_ari"]]
    return {"Race_Predictions": fact, "Classifier_Comparison": models, "Season_Validation": folds,
            "Feature_Importance": feats, "Association_Rules": rules, "Driver_Season_Tiers": clusters,
            "Clustering_Comparison": algos}


MEASURES = {
    "Race_Predictions": [
        ("Grands Prix", "DISTINCTCOUNT(Race_Predictions[race_id])", "0"),
        ("Winners Picked", "SUM(Race_Predictions[is_winner_hit])", "0"),
        ("Winner Hit Rate %", "DIVIDE([Winners Picked], [Grands Prix]) * 100", "0.0"),
        ("Winner In Top 3 %", "DIVIDE(SUM(Race_Predictions[winner_in_top3]), [Grands Prix]) * 100", "0.0"),
    ],
    "Driver_Season_Tiers": [("Driver Seasons", "COUNTROWS(Driver_Season_Tiers)", "0")],
}


def tmdl_type(s):
    if pd.api.types.is_integer_dtype(s):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(s):
        return "double", "type number"
    return "string", "type text"


def table_tmdl(name, df):
    # Power BI "Enter data" encoding: raw-deflate JSON of all values as text
    rows = df.astype(object).where(df.notna(), None).map(lambda v: None if v is None else str(v)).values.tolist()
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    b64 = base64.b64encode(comp.compress(json.dumps(rows).encode()) + comp.flush()).decode()
    cols = ", ".join(f"{c} = _t" for c in df.columns)
    types = ", ".join(f'{{"{c}", {tmdl_type(df[c])[1]}}}' for c in df.columns)
    lines = [f"table {name}", f"\tlineageTag: {uuid.uuid4()}", ""]
    for m_name, expr, fmt in MEASURES.get(name, []):
        lines += [f"\tmeasure '{m_name}' = {expr}", f"\t\tformatString: {fmt}", f"\t\tlineageTag: {uuid.uuid4()}", ""]
    for c in df.columns:
        lines += [f"\tcolumn '{c}'", f"\t\tdataType: {tmdl_type(df[c])[0]}", f"\t\tlineageTag: {uuid.uuid4()}",
                  "\t\tsummarizeBy: none", f"\t\tsourceColumn: {c}", ""]
    lines += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
              f'\t\t\t\t\tSource = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("{b64}", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [{cols}]),',
              f'\t\t\t\t\t#"Changed Type" = Table.TransformColumnTypes(Source, {{{types}}}, "en-US")',
              "\t\t\t\tin", '\t\t\t\t\t#"Changed Type"', "", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- visuals
def col(t, c):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, "queryRef": f"{t}.{c}", "nativeQueryRef": c}


def agg(t, c, fn=0, label="Sum"):  # fn: 0 = Sum, 1 = Average
    return {"field": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, "Function": fn}},
            "queryRef": f"{label}({t}.{c})", "nativeQueryRef": f"{label} of {c}"}


def meas(t, m):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": m}}, "queryRef": f"{t}.{m}", "nativeQueryRef": m}


def lit(v):
    return {"expr": {"Literal": {"Value": f"'{v}'"}}}


def visual(name, vtype, x, y, w, h, roles, title=None, sort=None):
    v = {"visualType": vtype, "query": {"queryState": {r: {"projections": p} for r, p in roles.items()}}, "drillFilterOtherVisuals": True}
    if sort:
        v["query"]["sortDefinition"] = {"sort": [{"field": sort["field"], "direction": "Descending"}], "isDefaultSort": True}
    if title:
        v["visualContainerObjects"] = {"title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": lit(title)}}]}
    return {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/1.3.0/schema.json", "name": name,
            "position": {"x": x, "y": y, "z": 1000, "height": h, "width": w, "tabOrder": 0}, "visual": v}


def pages():
    rp, ct, sv, fi, ar, dt, cc = ("Race_Predictions", "Classifier_Comparison", "Season_Validation", "Feature_Importance",
                                  "Association_Rules", "Driver_Season_Tiers", "Clustering_Comparison")
    prob = agg(rp, "win_probability_pct", 1, "Avg")
    return [
        ("race_predictor", "Race predictor (Dashboard 2)", [
            visual("card_hit", "card", 20, 20, 300, 110, {"Values": [meas(rp, "Winner Hit Rate %")]}, "Race winner picked (%)"),
            visual("card_top3", "card", 340, 20, 300, 110, {"Values": [meas(rp, "Winner In Top 3 %")]}, "Winner in model's top 3 (%)"),
            visual("card_gps", "card", 660, 20, 300, 110, {"Values": [meas(rp, "Grands Prix")]}, "Unseen Grands Prix (2022–2024)"),
            visual("slicer_race", "slicer", 980, 20, 280, 680, {"Values": [col(rp, "race")]}, "Pick a race"),
            visual("bar_prob", "clusteredBarChart", 20, 150, 460, 550, {"Category": [col(rp, "driver_name")], "Y": [prob]},
                   "Predicted win probability (%)", sort=prob),
            visual("table_race", "tableEx", 500, 150, 460, 550, {"Values": [col(rp, "race"), col(rp, "driver_name"), col(rp, "grid_position"),
                   col(rp, "win_probability_pct"), col(rp, "target_finish_position")]}, "Grid, prediction and result"),
        ]),
        ("classifier_comparison", "Classifier comparison (Dashboard 2)", [
            visual("bar_auc", "clusteredBarChart", 20, 20, 610, 330, {"Category": [col(ct, "model")], "Y": [agg(ct, "roc_auc")]},
                   "ROC-AUC on 2022–2024 holdout", sort=agg(ct, "roc_auc")),
            visual("bar_top1", "clusteredBarChart", 650, 20, 610, 330, {"Category": [col(ct, "model")], "Y": [agg(ct, "top1_winner_hit_pct")]},
                   "Race winner picked (%)", sort=agg(ct, "top1_winner_hit_pct")),
            visual("line_folds", "lineChart", 20, 370, 610, 330, {"Category": [col(sv, "test_season")],
                   "Y": [agg(sv, "roc_auc"), agg(sv, "baseline_roc_auc")]}, "ROC-AUC per unseen season: XGBoost vs grid-only baseline"),
            visual("bar_features", "clusteredBarChart", 650, 370, 610, 330, {"Category": [col(fi, "feature")], "Y": [agg(fi, "importance_pct")]},
                   "XGBoost feature importance (gain %)", sort=agg(fi, "importance_pct")),
        ]),
        ("pattern_mining", "Pattern mining (Dashboard 2)", [
            visual("slicer_cons", "slicer", 20, 20, 300, 680, {"Values": [col(ar, "consequents")]}, "Filter by outcome"),
            visual("table_rules", "tableEx", 340, 20, 920, 680, {"Values": [col(ar, "antecedents"), col(ar, "consequents"),
                   col(ar, "support"), col(ar, "confidence"), col(ar, "lift")]}, "Association rules (FP-Growth = Apriori), sorted by lift",
                   sort=col(ar, "lift")),
        ]),
        ("driver_tiers", "Driver tiers (Dashboard 3)", [
            visual("scatter_pca", "scatterChart", 20, 20, 760, 420, {"Category": [col(dt, "driver_season")], "Series": [col(dt, "cluster_name")],
                   "X": [agg(dt, "pca_1")], "Y": [agg(dt, "pca_2")]}, "K-Means tiers: 703 driver-seasons on 2 PCA axes"),
            visual("bar_algos", "clusteredBarChart", 800, 20, 460, 420, {"Category": [col(cc, "algorithm")], "Y": [agg(cc, "silhouette")]},
                   "Silhouette by clustering algorithm", sort=agg(cc, "silhouette")),
            visual("col_eras", "clusteredColumnChart", 20, 460, 760, 240, {"Category": [col(dt, "season")], "Series": [col(dt, "cluster_name")],
                   "Y": [meas(dt, "Driver Seasons")]}, "Drivers per tier, each season"),
            visual("table_algos", "tableEx", 800, 460, 460, 240, {"Values": [col(cc, "algorithm"), col(cc, "silhouette"), col(cc, "davies_bouldin"),
                   col(cc, "calinski_harabasz"), col(cc, "stability_ari")]}, "Clustering comparison"),
        ]),
    ]


# ---------------------------------------------------------------- write
def write(rel, content):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content if isinstance(content, str) else json.dumps(content, indent=2, ensure_ascii=False))


def platform(kind, display):
    return {"$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": kind, "displayName": display}, "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}}


def build():
    shutil.rmtree(OUT, ignore_errors=True)
    t = tables()
    os.makedirs(OUT)
    shutil.copy(os.path.join(ROOT, "powerbi", "HOW_TO_OPEN.md"), OUT)
    write(f"{NAME}.pbip", {"version": "1.0", "artifacts": [{"report": {"path": RP}}], "settings": {"enableAutoRecovery": True}})

    write(f"{SM}/.platform", platform("SemanticModel", NAME))
    write(f"{SM}/definition.pbism", {"version": "4.0", "settings": {}})
    write(f"{SM}/definition/database.tmdl", "database\n\tcompatibilityLevel: 1567\n\n")
    write(f"{SM}/definition/model.tmdl", "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
          "\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
          "annotation __PBI_TimeIntelligenceEnabled = 0\n\n" + "".join(f"ref table {n}\n" for n in t))
    for n, df in t.items():
        write(f"{SM}/definition/tables/{n}.tmdl", table_tmdl(n, df))

    write(f"{RP}/.platform", platform("Report", NAME))
    write(f"{RP}/definition.pbir", {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{SM}"}, "byConnection": None}})
    write(f"{RP}/definition/version.json", {"$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    theme = json.load(open(os.path.join(ROOT, "F1_PowerBI_Theme.json")))
    write(f"{RP}/StaticResources/RegisteredResources/ApexIQ_Theme.json", theme)
    base_dir = os.path.join(OUT, RP, "StaticResources", "SharedResources", "BaseThemes")
    os.makedirs(base_dir, exist_ok=True)
    shutil.copy(os.path.join(ROOT, "powerbi", "assets", "CY24SU10.json"), base_dir)  # Microsoft's stock base theme
    write(f"{RP}/definition/report.json", {
        "$schema": f"{SCHEMA}/item/report/definition/report/1.2.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.59", "type": "SharedResources"},
                            "customTheme": {"name": "ApexIQ_Theme.json", "reportVersionAtImport": "5.59", "type": "RegisteredResources"}},
        "layoutOptimization": "None",
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources", "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": "ApexIQ_Theme.json", "path": "ApexIQ_Theme.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useDefaultAggregateDisplayName": True}})
    pg = pages()
    write(f"{RP}/definition/pages/pages.json", {"$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
                                                 "pageOrder": [p[0] for p in pg], "activePageName": pg[0][0]})
    for pid, title, visuals in pg:
        write(f"{RP}/definition/pages/{pid}/page.json", {"$schema": f"{SCHEMA}/item/report/definition/page/1.2.0/schema.json",
                                                          "name": pid, "displayName": title, "displayOption": "FitToPage", "height": 720, "width": 1280})
        for v in visuals:
            write(f"{RP}/definition/pages/{pid}/visuals/{v['name']}/visual.json", v)
    return t, pg


if __name__ == "__main__":
    t, pg = build()
    # Self-check: every projected table/column/measure exists, and embedded data round-trips exactly
    known = {n: set(df.columns) | {m[0] for m in MEASURES.get(n, [])} for n, df in t.items()}
    for _, _, visuals in pg:
        for v in visuals:
            for role in v["visual"]["query"]["queryState"].values():
                for p in role["projections"]:
                    f = p["field"]
                    node = f.get("Column") or f.get("Measure") or f["Aggregation"]["Expression"]["Column"]
                    ent, prop = node["Expression"]["SourceRef"]["Entity"], node["Property"]
                    assert prop in known[ent], f"{v['name']}: {ent}.{prop} not in model"
    for n, df in t.items():
        text = open(os.path.join(OUT, SM, "definition", "tables", f"{n}.tmdl"), encoding="utf-8").read()
        b64 = text.split('Binary.FromText("')[1].split('"')[0]
        rows = json.loads(zlib.decompress(base64.b64decode(b64), -15))
        assert len(rows) == len(df) and len(rows[0]) == df.shape[1], n
    print(f"[+] {OUT}")
    print(f"    {len(t)} tables ({sum(len(d) for d in t.values()):,} rows), {sum(len(v) for _, _, v in pg)} visuals on {len(pg)} pages; self-check passed")
