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

import sqlite3

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

    # Dashboard 1: the star schema itself, so Power BI filters the fact through its dimensions
    with sqlite3.connect(os.path.join(ROOT, "f1_warehouse.db")) as db:
        q = lambda sql: pd.read_sql(sql, db)
        star_fact = q("SELECT result_id, race_id, driver_id, constructor_id, grid_position, finish_position, race_points, "
                      "is_win, is_podium FROM FACT_RACE_RESULTS_STAR")
        dim_race = q("SELECT race_id, season_year AS season, round, race_name, circuit_name, circuit_country FROM DIM_RACE_STAR")
        dim_driver = q("SELECT driver_id, driver_name, driver_code, driver_nationality FROM DIM_DRIVER")
        dim_team = q("SELECT constructor_id, constructor_name, constructor_nationality FROM DIM_CONSTRUCTOR")
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'FACT%' OR name LIKE 'DIM%') ORDER BY name")]
        wh = pd.DataFrame([(n, "Fact" if n.startswith("FACT") else "Dimension", db.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0])
                           for n in names], columns=["table_name", "table_role", "row_count"])

    snow = pd.read_csv(os.path.join(ROOT, "powerbi", "assets", "snowflake_snapshot.csv"))  # taken from the live account
    snow["row_count"] = snow["row_count"].astype("Int64")

    feat_store = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"),
                             usecols=["season", "race_id", "target_is_win"])
    seasons = (feat_store.assign(split=lambda d: d["season"].map(lambda y: "Train (1994-2021)" if y <= 2021 else "Test (2022-2024)"))
               .groupby(["season", "split"]).agg(entries=("race_id", "size"), grands_prix=("race_id", "nunique"),
                                                 winners=("target_is_win", "sum")).reset_index())

    sweep = src("04_pattern_mining", "support_sweep_benchmark.csv")
    conf = src("08_performance_metrics", "confusion_matrix.csv").rename(columns={"Unnamed: 0": "actual"}).melt(
        id_vars="actual", var_name="predicted", value_name="driver_races")
    conf[["actual", "predicted"]] = conf[["actual", "predicted"]].replace(
        {"Actual_Non_Winner_0": "Actual: did not win", "Actual_Winner_1": "Actual: won",
         "Predicted_Non_Winner_0": "Predicted: not winner", "Predicted_Winner_1": "Predicted: winner"})
    ho = src("08_performance_metrics", "partition_metrics.csv").iloc[-1]
    cls_metrics = pd.DataFrame([("Accuracy %", ho["accuracy_pct"]), ("Precision", ho["precision_class_1"]), ("Recall", ho["recall_class_1"]),
                                ("F1-score", ho["f1_class_1"]), ("ROC-AUC", ho["roc_auc"]), ("PR-AUC", ho["pr_auc"]),
                                ("Winner picked %", ho["top1_winner_hit_pct"])], columns=["metric", "value"])
    ks = src("10_clustering_comparison", "k_selection.csv")[["k", "inertia", "silhouette"]]
    profiles = src("11_clustering_algorithm", "cluster_profiles.csv").round(3)
    cm = json.load(open(os.path.join(ROOT, "12_clustering_metrics", "clustering_metrics.json")))
    clu_metrics = pd.DataFrame([("Silhouette (higher is better)", cm["silhouette"]), ("Davies-Bouldin (lower is better)", cm["davies_bouldin"]),
                                ("Calinski-Harabasz (higher is better)", cm["calinski_harabasz"]),
                                ("Seed stability ARI", cm["seed_stability_ari_mean"]),
                                ("ARI vs championship tier", cm["external_ari_vs_championship_tier"]),
                                ("Contenders in championship top 3 %", cm["contenders_in_top3_standing_pct"])], columns=["metric", "value"])
    champ = src("12_clustering_metrics", "championship_contingency.csv").melt(id_vars="cluster_name", var_name="championship_position",
                                                                              value_name="driver_seasons")
    rules["rule"] = rules["antecedents"] + " => " + rules["consequents"]
    era = lambda y: "1994-2005" if y <= 2005 else ("2006-2013 (V8)" if y <= 2013 else "2014-2024 (Hybrid)")
    dim_season = pd.DataFrame({"season": range(1994, 2025)})
    dim_season["era"] = dim_season["season"].map(era)
    global POLE_BASELINE_PCT
    POLE_BASELINE_PCT = float(src("05_algorithm_comparison", "comparison_results.csv")
                              .set_index("algorithm").filter(like="Grid Only", axis=0)["top1_winner_hit_pct"].iat[0])
    forecast = src("06_classification_algorithm", "forecast_2025.csv").rename(columns={"grid_position": "projected_grid"})
    forecast["race"] = "Round " + forecast["round"].astype(str).str.zfill(2) + ": " + forecast["race_name"]
    return {"Forecast_2025": forecast, "Dim_Season": dim_season, "Race_Predictions": fact, "Classifier_Comparison": models, "Season_Validation": folds,
            "Feature_Importance": feats, "Association_Rules": rules, "Driver_Season_Tiers": clusters,
            "Clustering_Comparison": algos, "Fact_Race_Results": star_fact, "Dim_Race": dim_race, "Dim_Driver": dim_driver,
            "Dim_Constructor": dim_team, "Warehouse_Tables": wh, "Snowflake_Objects": snow, "Season_Entries": seasons,
            "Mining_Sweep": sweep, "Confusion_Matrix": conf, "Classification_Metrics": cls_metrics, "K_Selection": ks,
            "Tier_Profiles": profiles, "Clustering_Metrics": clu_metrics, "Championship_Check": champ}


# Star schema: many fact rows to one dimension row
RELATIONSHIPS = [("Fact_Race_Results", "race_id", "Dim_Race"), ("Fact_Race_Results", "driver_id", "Dim_Driver"),
                 ("Fact_Race_Results", "constructor_id", "Dim_Constructor"),
                 # one shared season dimension, so a synced Season slicer filters every page
                 ("Dim_Race", "season", "Dim_Season"), ("Race_Predictions", "season", "Dim_Season"),
                 ("Driver_Season_Tiers", "season", "Dim_Season"), ("Season_Entries", "season", "Dim_Season")]
POLE_BASELINE_PCT = None  # set by tables(): the grid-only baseline's winner hit rate


MEASURES = {
    "Race_Predictions": [
        ("Grands Prix", "DISTINCTCOUNT(Race_Predictions[race_id])", "0"),
        ("Gauge Max", "100", "0"),
        ("Pole Baseline %", "POLE_BASELINE", "0.0"),
        ("Predicted Winner", 'IF(HASONEVALUE(Race_Predictions[race]), CALCULATE(MAX(Race_Predictions[driver_name]), Race_Predictions[predicted_rank] = 1), "Pick one race")', None),
        ("Predicted Win %", 'IF(HASONEVALUE(Race_Predictions[race]), CALCULATE(MAX(Race_Predictions[win_probability_pct]), Race_Predictions[predicted_rank] = 1))', "0.0"),
        ("Actual Winner", 'IF(HASONEVALUE(Race_Predictions[race]), CALCULATE(MAX(Race_Predictions[driver_name]), Race_Predictions[target_is_win] = 1), "Pick one race")', None),
        ("Prediction Result", 'IF(HASONEVALUE(Race_Predictions[race]), IF([Predicted Winner] = [Actual Winner], "Correct", "Missed"), "Pick one race")', None),
        ("Winners Picked", "SUM(Race_Predictions[is_winner_hit])", "0"),
        ("Winner Hit Rate %", "DIVIDE([Winners Picked], [Grands Prix]) * 100", "0.0"),
        ("Winner In Top 3 %", "DIVIDE(SUM(Race_Predictions[winner_in_top3]), [Grands Prix]) * 100", "0.0"),
    ],
    "Driver_Season_Tiers": [("Driver Seasons", "COUNTROWS(Driver_Season_Tiers)", "0"),
                            ("Tiers", "DISTINCTCOUNT(Driver_Season_Tiers[cluster_name])", "0"),
                            ("Title Contender Seasons", 'CALCULATE(COUNTROWS(Driver_Season_Tiers), Driver_Season_Tiers[cluster_name] = "Title Contenders")', "0"),
                            ("Avg Win Rate %", "AVERAGE(Driver_Season_Tiers[win_rate]) * 100", "0.0"),
                            ("Avg Finish Position", "AVERAGE(Driver_Season_Tiers[avg_finish])", "0.0")],
    "Forecast_2025": [
        ("Forecast Winner", 'IF(HASONEVALUE(Forecast_2025[race]), CALCULATE(MAX(Forecast_2025[driver_name]), Forecast_2025[predicted_rank] = 1), "Pick one race")', None),
        ("Forecast Win %", 'IF(HASONEVALUE(Forecast_2025[race]), CALCULATE(MAX(Forecast_2025[win_probability]), Forecast_2025[predicted_rank] = 1))', "0.0"),
        ("Main Rival", 'IF(HASONEVALUE(Forecast_2025[race]), CALCULATE(MAX(Forecast_2025[driver_name]), Forecast_2025[predicted_rank] = 2), "Pick one race")', None),
        ("Expected Wins", "SUM(Forecast_2025[win_probability]) / 100", "0.0"),
        ("Races Forecast", "DISTINCTCOUNT(Forecast_2025[round])", "0"),
    ],
    "Fact_Race_Results": [("Race Results", "COUNTROWS(Fact_Race_Results)", "#,0"), ("Wins", "SUM(Fact_Race_Results[is_win])", "0"),
                          ("Podiums", "SUM(Fact_Race_Results[is_podium])", "0"),
                          ("Win Rate %", "DIVIDE([Wins], [Race Results]) * 100", "0.0"),
                          ("Drivers", "DISTINCTCOUNT(Fact_Race_Results[driver_id])", "0"),
                          ("Teams", "DISTINCTCOUNT(Fact_Race_Results[constructor_id])", "0")],
    "Classifier_Comparison": [("Champion ROC-AUC", 'CALCULATE(SUM(Classifier_Comparison[roc_auc]), CONTAINSSTRING(Classifier_Comparison[model], "Champion"))', "0.0000"),
                              ("Models", "COUNTROWS(Classifier_Comparison)", "0"),
                              ("Best ROC-AUC", "MAX(Classifier_Comparison[roc_auc])", "0.0000"),
                              ("Best Winner Pick %", "MAX(Classifier_Comparison[top1_winner_hit_pct])", "0.0")],
    "Association_Rules": [("Rules", "COUNTROWS(Association_Rules)", "#,0"), ("Max Lift", "MAX(Association_Rules[lift])", "0.00"),
                          ("Avg Confidence %", "AVERAGE(Association_Rules[confidence]) * 100", "0.0")],
    "Snowflake_Objects": [("Snowflake Objects", "COUNTROWS(Snowflake_Objects)", "0")],
    "Season_Entries": [("Labelled Entries", "SUM(Season_Entries[entries])", "#,0"),
                       ("Dataset Grands Prix", "SUM(Season_Entries[grands_prix])", "0")],
    "Clustering_Comparison": [("Algorithms", "COUNTROWS(Clustering_Comparison)", "0"),
                              ("Best Silhouette", "MAX(Clustering_Comparison[silhouette])", "0.000")],
}


def tmdl_type(s):
    if pd.api.types.is_bool_dtype(s):
        return "int64", "Int64.Type"
    if pd.api.types.is_integer_dtype(s):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(s):
        return "double", "type number"
    return "string", "type text"


def table_tmdl(name, df):
    # Power BI "Enter data" encoding: raw-deflate JSON of all values as text
    # blanks must be JSON null: pandas' nullable Int64 turns NA into NaN, which Power BI rejects as invalid JSON
    rows = [[None if pd.isna(v) else str(v) for v in r] for r in df.astype(object).itertuples(index=False)]
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    b64 = base64.b64encode(comp.compress(json.dumps(rows).encode()) + comp.flush()).decode()
    cols = ", ".join(f"{c} = _t" for c in df.columns)
    types = ", ".join(f'{{"{c}", {tmdl_type(df[c])[1]}}}' for c in df.columns)
    lines = [f"table {name}", f"\tlineageTag: {uuid.uuid4()}", ""]
    for m_name, expr, fmt in MEASURES.get(name, []):
        expr = expr.replace("POLE_BASELINE", f"{POLE_BASELINE_PCT:.2f}")
        lines += [f"\tmeasure '{m_name}' = {expr}"] + ([f"\t\tformatString: {fmt}"] if fmt else []) + [f"\t\tlineageTag: {uuid.uuid4()}", ""]
    for c in df.columns:
        lines += [f"\tcolumn '{c}'", f"\t\tdataType: {tmdl_type(df[c])[0]}", f"\t\tlineageTag: {uuid.uuid4()}",
                  "\t\tsummarizeBy: none", f"\t\tsourceColumn: {c}", ""]
    lines += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
              f'\t\t\t\t\tSource = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("{b64}", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [{cols}]),',
              f'\t\t\t\t\t#"Changed Type" = Table.TransformColumnTypes(Source, {{{types}}}, "en-US")',
              "\t\t\t\tin", '\t\t\t\t\t#"Changed Type"', "", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- visuals
# Every formatting property below also appears in a report saved by Power BI Desktop (Oct 2026); the
# theme (assets/ApexIQ_PitWall_Theme.json) styles backgrounds, borders, axes, tables and card values.
INK, MUTED, PURPLE, GREEN, PANEL = "#FFFFFF", "#8B95A5", "#A66CFF", "#2ECC71", "#131823"


def col(t, c):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, "queryRef": f"{t}.{c}", "nativeQueryRef": c}


def agg(t, c, fn=0, label="Sum"):  # fn: 0 = Sum, 1 = Average
    return {"field": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, "Function": fn}},
            "queryRef": f"{label}({t}.{c})", "nativeQueryRef": f"{label} of {c}"}


def meas(t, m):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": m}}, "queryRef": f"{t}.{m}", "nativeQueryRef": m}


def lit(v):
    return {"expr": {"Literal": {"Value": f"'{v}'"}}}


def raw(v):
    return {"expr": {"Literal": {"Value": v}}}


def color(c):
    return {"solid": {"color": lit(c)}}


SHOW_LABELS = {"labels": [{"properties": {"show": raw("true"), "color": color(INK), "fontSize": raw("9D")}}]}


def visual(name, vtype, x, y, w, h, roles, title=None, sort=None, objects=None, extra=None):
    v = {"visualType": vtype, "query": {"queryState": {r: {"projections": p} for r, p in roles.items()}}, "drillFilterOtherVisuals": True}
    if sort:
        v["query"]["sortDefinition"] = {"sort": [{"field": sort["field"], "direction": "Descending"}], "isDefaultSort": True}
    if objects:
        v["objects"] = objects
    if title:
        v["visualContainerObjects"] = {"title": [{"properties": {"show": raw("true"), "text": lit(title), "fontColor": color(INK),
                                                                 "fontSize": raw("11D")}}]}
    v.update(extra or {})
    return {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.0.0/schema.json", "name": name,
            "position": {"x": x, "y": y, "z": 1000, "height": h, "width": w, "tabOrder": 0}, "visual": v}


def chart(name, vtype, x, y, w, h, roles, title, sort=None):
    """Bar, column and line charts with value labels on."""
    return visual(name, vtype, x, y, w, h, roles, title, sort, objects=SHOW_LABELS)


def card(name, x, y, t, m, title, w=230, accent=INK):
    return visual(name, "card", x, y, w, 100, {"Values": [meas(t, m)]}, title, objects={
        "labels": [{"properties": {"color": color(accent), "fontSize": raw("26D")}}],
        "categoryLabels": [{"properties": {"show": raw("false")}}]})


def slicer(name, x, y, w, h, field, title, mode="Dropdown", sync=None):
    extra = {"syncGroup": {"groupName": sync, "fieldChanges": True, "filterChanges": True}} if sync else None
    return visual(name, "slicer", x, y, w, h, {"Values": [field]}, title, extra=extra, objects={
        "data": [{"properties": {"mode": lit(mode)}}],
        "header": [{"properties": {"show": raw("false")}}],
        "items": [{"properties": {"fontColor": color(INK), "background": color(PANEL)}}]})


def header(name, title, subtitle):
    """Page banner: a textbox with the title and one line saying what the page proves."""
    return {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.0.0/schema.json", "name": name,
            "position": {"x": 20, "y": 8, "z": 2000, "height": 62, "width": 1240, "tabOrder": 0},
            "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
                {"textRuns": [{"value": title, "textStyle": {"fontSize": "20pt", "color": INK, "fontWeight": "bold"}}]},
                {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "10pt", "color": MUTED}}]}]}}]},
                       "drillFilterOtherVisuals": True}}


def table(name, x, y, w, h, t, cols, title, sort=None):
    return visual(name, "tableEx", x, y, w, h, {"Values": [col(t, c) for c in cols]}, title, sort=sort)


def pages():
    rp, ct, sv, fi, ar, dt, cc = ("Race_Predictions", "Classifier_Comparison", "Season_Validation", "Feature_Importance",
                                  "Association_Rules", "Driver_Season_Tiers", "Clustering_Comparison")
    fr, dr, dd, dc, wt, so, se = ("Fact_Race_Results", "Dim_Race", "Dim_Driver", "Dim_Constructor", "Warehouse_Tables",
                                  "Snowflake_Objects", "Season_Entries")
    ms, cfm, clm, ksel, tp, cme, chc, ds = ("Mining_Sweep", "Confusion_Matrix", "Classification_Metrics", "K_Selection",
                                             "Tier_Profiles", "Clustering_Metrics", "Championship_Check", "Dim_Season")
    prob = agg(rp, "win_probability_pct", 1, "Avg")
    fc = "Forecast_2025"
    season = lambda n, x=1020, y=80, w=240: slicer(n, x, y, w, 100, col(ds, "season"), "Season", "Between", "g_season")
    era = lambda n, x=1020, y=80, w=240: slicer(n, x, y, w, 100, col(ds, "era"), "Era", "Dropdown", "g_era")
    return [
        ("overview", "Overview", [
            header("hdr", "ApexIQ | F1 Race Intelligence", "Data warehouse on Snowflake, race-winner classification and driver-tier clustering, 1994-2024"),
            card("k1", 20, 80, rp, "Winners Picked", "Race winners picked (68 unseen GPs)", 200, PURPLE),
            card("k2", 230, 80, ct, "Champion ROC-AUC", "XGBoost ROC-AUC", 200),
            card("k3", 440, 80, fr, "Race Results", "Warehouse fact rows", 200),
            card("k4", 650, 80, ar, "Rules", "Association rules", 200),
            card("k5", 860, 80, dt, "Driver Seasons", "Driver-seasons clustered", 200),
            card("k6", 1070, 80, dt, "Tiers", "Driver tiers (K-Means)", 190, GREEN),
            visual("gauge", "gauge", 20, 195, 400, 505, {"Y": [meas(rp, "Winner Hit Rate %")], "MaxValue": [meas(rp, "Gauge Max")],
                   "TargetValue": [meas(rp, "Pole Baseline %")]}, "Winner picked % vs. pole-sitter baseline (target line)",
                   objects={"calloutValue": [{"properties": {"color": color(PURPLE)}}], "target": [{"properties": {"color": color(INK)}}],
                            "labels": [{"properties": {"color": color(MUTED)}}]}),
            chart("models", "clusteredBarChart", 440, 195, 410, 505, {"Category": [col(ct, "model")], "Y": [agg(ct, "top1_winner_hit_pct")]},
                  "Race winner picked (%) by model", sort=agg(ct, "top1_winner_hit_pct")),
            chart("tiers", "clusteredColumnChart", 870, 195, 390, 505, {"Category": [col(dt, "cluster_name")], "Y": [meas(dt, "Driver Seasons")]},
                  "Driver-seasons per tier"),
        ]),
        ("warehouse", "1. Data warehouse", [
            header("hdr", "1. Data warehouse: star schema", "Fact_Race_Results (1 row = driver x Grand Prix) filtered through Dim_Race, Dim_Driver, Dim_Constructor and Dim_Season"),
            card("k1", 20, 80, fr, "Race Results", "Fact rows", 190),
            card("k2", 220, 80, fr, "Wins", "Wins", 150, PURPLE),
            card("k3", 380, 80, fr, "Podiums", "Podiums", 150),
            card("k4", 540, 80, fr, "Win Rate %", "Win rate %", 150, GREEN),
            card("k5", 700, 80, fr, "Drivers", "Drivers", 150),
            card("k6", 860, 80, fr, "Teams", "Teams", 150),
            season("s_season"),
            slicer("s_team", 1020, 195, 240, 80, col(dc, "constructor_name"), "Team"),
            slicer("s_driver", 1020, 285, 240, 80, col(dd, "driver_name"), "Driver"),
            era("s_era", 1020, 375, 240),
            visual("rollup", "pivotTable", 20, 195, 640, 300, {"Rows": [col(dc, "constructor_name")], "Columns": [col(ds, "era")],
                   "Values": [meas(fr, "Wins")]}, "Roll-up: wins by team and era (drill from era to season)"),
            chart("by_season", "clusteredColumnChart", 680, 195, 320, 300, {"Category": [col(ds, "season")], "Y": [meas(fr, "Wins")]},
                  "Wins per season"),
            chart("drivers", "clusteredBarChart", 20, 510, 640, 190, {"Category": [col(dd, "driver_name")], "Y": [meas(fr, "Wins")]},
                  "Most wins (Fact joined to Dim_Driver)", sort=meas(fr, "Wins")),
            table("tables", 680, 510, 580, 190, wt, ["table_name", "table_role", "row_count"], "Warehouse tables in f1_warehouse.db"),
        ]),
        ("snowflake", "1. Snowflake deployment", [
            header("hdr", "1. Snowflake deployment", "F1_PREDICTION_DB on account UKFIGDV-WD45232: RAW > CLEAN > DW > ML > ANALYTICS (snapshot of the live account)"),
            card("k1", 20, 80, so, "Snowflake Objects", "Tables and views", 240, PURPLE),
            slicer("s_layer", 280, 80, 300, 100, col(so, "schema_name"), "Layer (schema)"),
            slicer("s_type", 600, 80, 300, 100, col(so, "table_type"), "Object type"),
            chart("layers", "clusteredColumnChart", 20, 195, 560, 505, {"Category": [col(so, "schema_name")], "Y": [meas(so, "Snowflake Objects")]},
                  "Objects per layer"),
            table("objects", 600, 195, 660, 505, so, ["schema_name", "table_name", "table_type", "row_count"], "Objects and row counts"),
        ]),
        ("supervised_dataset", "2. Supervised dataset", [
            header("hdr", "2. Supervised dataset", "12,358 labelled driver-race entries, 16 pre-race features, target = race winner; chronological train / test split"),
            card("k1", 20, 80, se, "Labelled Entries", "Labelled entries", 240, PURPLE),
            card("k2", 270, 80, se, "Dataset Grands Prix", "Grands Prix", 240),
            season("s_season", 520, 80, 240), era("s_era", 770, 80, 240),
            chart("entries", "clusteredColumnChart", 20, 195, 1240, 300, {"Category": [col(se, "season")], "Series": [col(se, "split")],
                  "Y": [agg(se, "entries")]}, "Entries per season, coloured by train / test split (no shuffling)"),
            chart("winners", "clusteredColumnChart", 20, 510, 1240, 190, {"Category": [col(se, "season")], "Y": [agg(se, "winners")]},
                  "Winners per season: exactly one per Grand Prix"),
        ]),
        ("pattern_mining", "2. Pattern mining", [
            header("hdr", "2. Pattern mining: Apriori and FP-Growth", "Both find the same 414 frequent itemsets; FP-Growth needs 2 database scans and no candidate generation"),
            card("k1", 20, 80, ar, "Rules", "Rules shown", 230, PURPLE),
            card("k2", 260, 80, ar, "Max Lift", "Strongest lift", 230, GREEN),
            card("k3", 500, 80, ar, "Avg Confidence %", "Average confidence %", 230),
            slicer("s_outcome", 740, 80, 520, 100, col(ar, "consequents"), "Outcome (consequent)"),
            visual("scatter", "scatterChart", 20, 195, 620, 300, {"Category": [col(ar, "rule")], "X": [agg(ar, "support")],
                   "Y": [agg(ar, "confidence")], "Size": [agg(ar, "lift")]}, "Every rule: support vs. confidence (bubble size = lift)"),
            chart("sweep", "lineChart", 660, 195, 600, 300, {"Category": [col(ms, "min_support")], "Y": [agg(ms, "apriori_candidates"), agg(ms, "fp_tree_nodes")]},
                  "Search cost as support drops: Apriori candidates vs. FP-tree nodes"),
            table("rules", 20, 510, 1240, 190, ar, ["antecedents", "consequents", "support", "confidence", "lift"], "Rules, strongest lift first",
                  sort=col(ar, "lift")),
        ]),
        ("classifier_comparison", "2. Classifier comparison", [
            header("hdr", "2. Classifier comparison and validation", "Seven models, same 16 features, trained 1994-2021 and tested on 68 unseen Grands Prix (2022-2024)"),
            card("k1", 20, 80, ct, "Models", "Models compared", 230),
            card("k2", 260, 80, ct, "Best ROC-AUC", "Best ROC-AUC", 230, PURPLE),
            card("k3", 500, 80, ct, "Best Winner Pick %", "Best winner pick %", 230, GREEN),
            slicer("s_model", 740, 80, 520, 100, col(ct, "model"), "Model"),
            chart("auc", "clusteredBarChart", 20, 195, 620, 300, {"Category": [col(ct, "model")], "Y": [agg(ct, "roc_auc")]},
                  "ROC-AUC on the 2022-2024 holdout", sort=agg(ct, "roc_auc")),
            chart("top1", "clusteredBarChart", 660, 195, 600, 300, {"Category": [col(ct, "model")], "Y": [agg(ct, "top1_winner_hit_pct")]},
                  "Race winner picked (%)", sort=agg(ct, "top1_winner_hit_pct")),
            chart("folds", "lineChart", 20, 510, 620, 190, {"Category": [col(sv, "test_season")], "Y": [agg(sv, "roc_auc"), agg(sv, "baseline_roc_auc")]},
                  "Expanding-window validation: XGBoost vs. grid-only baseline"),
            table("models_t", 660, 510, 600, 190, ct, ["model", "roc_auc", "pr_auc", "recall", "top1_winner_hit_pct"], "All seven models",
                  sort=col(ct, "roc_auc")),
        ]),
        ("classification", "2. Classification (XGBoost)", [
            header("hdr", "2. Classification algorithm: cost-sensitive XGBoost", "Per-driver win probability, normalised so each race sums to 100%; pick a season or race to explore"),
            card("k1", 20, 80, rp, "Winner Hit Rate %", "Winner picked %", 220, PURPLE),
            card("k2", 250, 80, rp, "Winner In Top 3 %", "Winner in top 3 %", 220, GREEN),
            card("k3", 480, 80, rp, "Grands Prix", "Grands Prix", 200),
            season("s_season", 690, 80, 280),
            slicer("s_race", 980, 80, 280, 100, col(rp, "race"), "Grand Prix"),
            chart("prob", "clusteredBarChart", 20, 195, 500, 505, {"Category": [col(rp, "driver_name")], "Y": [prob]},
                  "Predicted win probability (%), average over the selection", sort=prob),
            visual("conf", "pivotTable", 540, 195, 400, 150, {"Rows": [col(cfm, "actual")], "Columns": [col(cfm, "predicted")],
                   "Values": [agg(cfm, "driver_races")]}, "Confusion matrix (threshold 0.5)"),
            table("metrics", 960, 195, 300, 260, clm, ["metric", "value"], "Holdout metrics"),
            chart("features", "clusteredBarChart", 540, 360, 400, 340, {"Category": [col(fi, "feature")], "Y": [agg(fi, "importance_pct")]},
                  "Feature importance (gain %)", sort=agg(fi, "importance_pct")),
            visual("gauge", "gauge", 960, 470, 300, 230, {"Y": [meas(rp, "Winner Hit Rate %")], "MaxValue": [meas(rp, "Gauge Max")],
                   "TargetValue": [meas(rp, "Pole Baseline %")]}, "Winner picked % vs. pole baseline",
                   objects={"calloutValue": [{"properties": {"color": color(PURPLE)}}], "target": [{"properties": {"color": color(INK)}}],
                            "labels": [{"properties": {"color": color(MUTED)}}]}),
        ]),
        ("race_predictor", "2. Race predictor", [
            header("hdr", "2. Race predictor", "Pick a Grand Prix the model never saw (2022-2024): its predicted winner, the probability, and what actually happened"),
            card("k1", 20, 80, rp, "Predicted Winner", "Predicted winner", 290, PURPLE),
            card("k2", 320, 80, rp, "Predicted Win %", "Predicted win probability %", 220),
            card("k3", 550, 80, rp, "Actual Winner", "Actual winner", 290, GREEN),
            card("k4", 850, 80, rp, "Prediction Result", "Model's pick was", 160),
            season("s_season", 1020, 80, 240),
            slicer("s_race", 1020, 195, 240, 505, col(rp, "race"), "Grand Prix (pick one)"),
            chart("prob", "clusteredBarChart", 20, 195, 560, 505, {"Category": [col(rp, "driver_name")], "Y": [prob]},
                  "Win probability (%) for the selected race", sort=prob),
            table("grid", 600, 195, 400, 300, rp, ["driver_name", "grid_position", "win_probability_pct", "predicted_rank",
                  "target_finish_position"], "Grid, prediction and result", sort=col(rp, "win_probability_pct")),
            chart("hits", "clusteredColumnChart", 600, 510, 400, 190, {"Category": [col(rp, "season")], "Y": [meas(rp, "Winners Picked")]},
                  "Winners picked per season"),
        ]),
        ("forecast_2025", "2. 2025 forecast", [
            header("hdr", "2. 2025 forecast: upcoming Grands Prix", "Champion retrained on 1994-2024; inputs rebuilt from each driver's history to the end of 2024; grid projected from recent starts"),
            card("k1", 20, 80, fc, "Forecast Winner", "Forecast winner", 300, PURPLE),
            card("k2", 330, 80, fc, "Forecast Win %", "Win probability %", 210),
            card("k3", 550, 80, fc, "Main Rival", "Main rival", 300, GREEN),
            card("k4", 860, 80, fc, "Races Forecast", "Races forecast", 150),
            slicer("s_race", 1020, 80, 240, 620, col(fc, "race"), "2025 Grand Prix (pick one)"),
            chart("prob", "clusteredBarChart", 20, 195, 490, 505, {"Category": [col(fc, "driver_name")], "Y": [agg(fc, "win_probability", 1, "Avg")]},
                  "Win probability (%), selected race", sort=agg(fc, "win_probability", 1, "Avg")),
            chart("expected", "clusteredBarChart", 530, 195, 470, 300, {"Category": [col(fc, "driver_name")], "Y": [meas(fc, "Expected Wins")]},
                  "Expected wins over the selection", sort=meas(fc, "Expected Wins")),
            table("grid", 530, 510, 470, 190, fc, ["race", "driver_name", "constructor_name", "projected_grid", "win_probability"],
                  "Projected grid and forecast", sort=col(fc, "win_probability")),
        ]),
        ("clustering_comparison", "3. Clustering comparison", [
            header("hdr", "3. Clustering comparison: six algorithms", "K-Means, K-Medoids, Ward, Gaussian Mixture, BIRCH and DBSCAN on the same 703 standardised driver-season profiles"),
            card("k1", 20, 80, cc, "Algorithms", "Algorithms compared", 240),
            card("k2", 270, 80, cc, "Best Silhouette", "Best silhouette", 240, PURPLE),
            slicer("s_algo", 520, 80, 740, 100, col(cc, "algorithm"), "Algorithm"),
            chart("sil", "clusteredBarChart", 20, 195, 620, 300, {"Category": [col(cc, "algorithm")], "Y": [agg(cc, "silhouette")]},
                  "Silhouette (higher is better)", sort=agg(cc, "silhouette")),
            chart("elbow", "lineChart", 660, 195, 600, 300, {"Category": [col(ksel, "k")], "Y": [agg(ksel, "inertia")]},
                  "Choosing k: elbow of K-Means inertia at k = 3"),
            table("algos", 20, 510, 1240, 190, cc, ["algorithm", "n_clusters", "noise_pct", "silhouette", "davies_bouldin",
                  "calinski_harabasz", "stability_ari"], "All six algorithms, every metric"),
        ]),
        ("driver_tiers", "3. K-Means driver tiers", [
            header("hdr", "3. K-Means: three driver tiers", "Title Contenders, Midfield Regulars and Backmarkers found without labels; filter by season, era or tier"),
            card("k1", 20, 80, dt, "Driver Seasons", "Driver-seasons", 220),
            card("k2", 250, 80, dt, "Title Contender Seasons", "Title contender seasons", 220, PURPLE),
            card("k3", 480, 80, dt, "Avg Win Rate %", "Average win rate %", 200, GREEN),
            season("s_season", 690, 80, 280),
            slicer("s_tier", 980, 80, 280, 100, col(dt, "cluster_name"), "Tier"),
            visual("pca", "scatterChart", 20, 195, 760, 330, {"Category": [col(dt, "driver_season")], "Series": [col(dt, "cluster_name")],
                   "X": [agg(dt, "pca_1")], "Y": [agg(dt, "pca_2")]}, "703 driver-seasons on two PCA axes, coloured by tier"),
            table("profiles", 800, 195, 460, 330, tp, ["cluster_name", "size", "avg_grid", "avg_finish", "win_rate", "podium_rate", "dnf_rate"],
                  "Tier profiles (centroids)"),
            chart("eras", "clusteredColumnChart", 20, 540, 1240, 160, {"Category": [col(dt, "season")], "Series": [col(dt, "cluster_name")],
                  "Y": [meas(dt, "Driver Seasons")]}, "Drivers per tier, each season"),
        ]),
        ("clustering_metrics", "3. Clustering metrics", [
            header("hdr", "3. Clustering performance metrics", "Internal quality, stability across reruns, and a check against the real championship (never used to fit the tiers)"),
            table("metrics", 20, 80, 600, 300, cme, ["metric", "value"], "K-Means quality metrics"),
            visual("champ", "pivotTable", 640, 80, 620, 300, {"Rows": [col(chc, "cluster_name")], "Columns": [col(chc, "championship_position")],
                   "Values": [agg(chc, "driver_seasons")]}, "Tier vs. championship position"),
            chart("champ_bar", "clusteredColumnChart", 20, 395, 1240, 305, {"Category": [col(chc, "cluster_name")],
                  "Series": [col(chc, "championship_position")], "Y": [agg(chc, "driver_seasons")]}, "Where each tier finished in the championship"),
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
    write(f"{NAME}.pbip", {"$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
                           "artifacts": [{"report": {"path": RP}}], "settings": {"enableAutoRecovery": True}})

    write(f"{SM}/.platform", platform("SemanticModel", NAME))
    write(f"{SM}/definition.pbism", {"$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json",
                                      "version": "4.2", "settings": {}})
    write(f"{SM}/definition/database.tmdl", "database\n\tcompatibilityLevel: 1606\n\n")
    write(f"{SM}/definition/model.tmdl", "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
          "\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
          "annotation __PBI_TimeIntelligenceEnabled = 0\n\n" + "".join(f"ref table {n}\n" for n in t))
    for n, df in t.items():
        write(f"{SM}/definition/tables/{n}.tmdl", table_tmdl(n, df))
    write(f"{SM}/definition/relationships.tmdl", "".join(
        f"relationship {uuid.uuid4()}\n\tfromColumn: {f}.{c}\n\ttoColumn: {d}.{c}\n\n" for f, c, d in RELATIONSHIPS))

    write(f"{RP}/.platform", platform("Report", NAME))
    write(f"{RP}/definition.pbir", {"$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
                                     "version": "4.0", "datasetReference": {"byPath": {"path": f"../{SM}"}}})
    write(f"{RP}/definition/version.json", {"$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    theme = json.load(open(os.path.join(ROOT, "powerbi", "assets", "ApexIQ_PitWall_Theme.json")))
    write(f"{RP}/StaticResources/RegisteredResources/ApexIQ_Theme.json", theme)
    at_import = {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"}  # as saved by Power BI Desktop
    write(f"{RP}/definition/report.json", {
        "$schema": f"{SCHEMA}/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {"customTheme": {"name": "ApexIQ_Theme.json", "reportVersionAtImport": at_import, "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "ApexIQ_Theme.json", "path": "ApexIQ_Theme.json", "type": "CustomTheme"}]}],
        "settings": {"useEnhancedTooltips": False}})
    pg = pages()
    write(f"{RP}/definition/pages/pages.json", {"$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
                                                 "pageOrder": [p[0] for p in pg], "activePageName": pg[0][0]})
    for pid, title, visuals in pg:
        write(f"{RP}/definition/pages/{pid}/page.json", {"$schema": f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json",
                                                          "name": pid, "displayName": title, "displayOption": "FitToPage", "height": 720, "width": 1280,
                                                          "objects": {"background": [{"properties": {"color": color("#0B0E14"), "transparency": raw("0D")}}]}})
        for v in visuals:
            write(f"{RP}/definition/pages/{pid}/visuals/{v['name']}/visual.json", v)
    return t, pg


if __name__ == "__main__":
    t, pg = build()
    # Self-check: every projected table/column/measure exists, and embedded data round-trips exactly
    known = {n: set(df.columns) | {m[0] for m in MEASURES.get(n, [])} for n, df in t.items()}
    for pid, _, visuals in pg:
        names = [v["name"] for v in visuals]
        assert len(names) == len(set(names)), f"{pid}: duplicate visual names"
        for v in visuals:
            for role in v["visual"].get("query", {"queryState": {}})["queryState"].values():
                for p in role["projections"]:
                    f = p["field"]
                    node = f.get("Column") or f.get("Measure") or f["Aggregation"]["Expression"]["Column"]
                    ent, prop = node["Expression"]["SourceRef"]["Entity"], node["Property"]
                    assert prop in known[ent], f"{v['name']}: {ent}.{prop} not in model"
    # Power BI rejects a measure name used twice in the model, or shared with a column of its table (case-insensitive)
    all_measures = [m[0].lower() for ms in MEASURES.values() for m in ms]
    assert len(all_measures) == len(set(all_measures)), "duplicate measure names"
    for n, ms in MEASURES.items():
        clash = {m[0].lower() for m in ms} & {c.lower() for c in t[n].columns}
        assert not clash, f"{n}: measure and column share a name {clash}"
    for f, c, d in RELATIONSHIPS:  # star schema: unique keys on the dimension side, every fact key found
        assert t[d][c].is_unique and t[f][c].isin(t[d][c]).all(), f"{f}.{c} -> {d}.{c}"
    for n, df in t.items():
        text = open(os.path.join(OUT, SM, "definition", "tables", f"{n}.tmdl"), encoding="utf-8").read()
        b64 = text.split('Binary.FromText("')[1].split('"')[0]
        rows = json.loads(zlib.decompress(base64.b64decode(b64), -15),
                          parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f"{n}: {c} is not valid JSON")))
        assert len(rows) == len(df) and len(rows[0]) == df.shape[1], n
    print(f"[+] {OUT}")
    print(f"    {len(t)} tables ({sum(len(d) for d in t.values()):,} rows), {len(RELATIONSHIPS)} relationships, "
          f"{sum(len(v) for _, _, v in pg)} visuals on {len(pg)} pages; self-check passed")
