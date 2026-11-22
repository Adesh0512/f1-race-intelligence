# ============================================================
# FILE: 01_data_warehouse/build_star_schema.py
# REAL MODULE: 00_data_warehouse/etl_master_ingestion.py
# WHAT IT DOES: ETL = Extract, Transform, Load.
#   1. EXTRACT   : read the master results file (8,650 rows, 2004-2024)
#   2. TRANSFORM : split it into dimension tables and one fact table
#   3. LOAD      : save them into a SQLite database (a star schema)
# ============================================================

import os
import sqlite3
import pandas as pd

# Where the files are
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.join(HERE, "..", "..")
SOURCE_FILE = os.path.join(PROJECT, "00_data_warehouse", "F1_Warehouse_Master_65_Columns_2004_2024.csv")
OUTPUT_DB = os.path.join(HERE, "..", "output", "exam_warehouse.db")

# ---------- 1. EXTRACT ----------
results = pd.read_csv(SOURCE_FILE)
print("Rows read from the source file:", len(results))          # 8,650 = one row per driver per race

# ---------- 2. TRANSFORM ----------
# A dimension table describes "who / where / when". We keep one row per driver, team and race.
dim_driver = results[["driver_id", "driver_name", "driver_nationality"]].drop_duplicates("driver_id")
dim_constructor = results[["constructor_id", "constructor_name", "constructor_nationality"]].drop_duplicates("constructor_id")
dim_race = results[["race_id", "season", "round", "race_name", "race_date", "circuit_name", "circuit_country"]].drop_duplicates("race_id")

# The date dimension holds the hierarchy  day -> month -> quarter -> season  (used for roll-up)
dim_date = dim_race[["race_id", "race_date", "season"]].copy()
dim_date["month"] = pd.to_datetime(dim_date["race_date"]).dt.month
dim_date["quarter"] = pd.to_datetime(dim_date["race_date"]).dt.quarter

# The fact table holds the measurements. GRAIN = one driver in one Grand Prix.
fact = results[["race_id", "driver_id", "constructor_id", "grid_position", "finish_position", "race_points"]].copy()
fact["is_win"] = (fact["finish_position"] == 1).astype(int)      # 1 if the driver won, else 0
fact["is_podium"] = (fact["finish_position"] <= 3).astype(int)   # 1 if the driver finished in the top 3
fact["is_pole"] = (fact["grid_position"] == 1).astype(int)       # 1 if the driver started first

# ---------- 3. LOAD ----------
os.makedirs(os.path.dirname(OUTPUT_DB), exist_ok=True)
connection = sqlite3.connect(OUTPUT_DB)
tables = {"DIM_DRIVER": dim_driver, "DIM_CONSTRUCTOR": dim_constructor, "DIM_RACE": dim_race,
          "DIM_DATE": dim_date, "FACT_RACE_RESULTS": fact}
for name, table in tables.items():
    table.to_sql(name, connection, if_exists="replace", index=False)
    print(f"Loaded {name:<18} {len(table):>6} rows")
connection.close()

# Check: every fact row must point to a race that exists in the race dimension
assert fact["race_id"].isin(dim_race["race_id"]).all()
print("Star schema saved to", os.path.abspath(OUTPUT_DB))
