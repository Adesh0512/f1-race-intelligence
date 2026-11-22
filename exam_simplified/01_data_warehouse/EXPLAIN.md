# Folder 01 — Data Warehouse

**Responsibility of this folder:** store 21 seasons of race results (2004–2024) in a star schema, then ask analytical questions of it (OLAP).
**Real project:** `00_data_warehouse/` (ETL script, star and snowflake schema SQL, 12 OLAP queries) and the dashboard page *Warehouse Design*.

---

## File 1: `build_star_schema.py`

**1. Location:** `exam_simplified/01_data_warehouse/build_star_schema.py` (real: `00_data_warehouse/etl_master_ingestion.py`)

**2. What it does:** ETL. It **E**xtracts the master results file, **T**ransforms it into dimension tables and one fact table, and **L**oads them into a SQLite database.

**3. Parameters and logic**
| Parameter | Value | Meaning |
|---|---|---|
| Source | `F1_Warehouse_Master_65_Columns_2004_2024.csv` | 8,650 rows, one per driver per race |
| Grain | 1 driver × 1 Grand Prix | what one fact row means |
| Dimensions | driver (108), constructor (35), race (412), date (412) | who / where / when |
| Measures | grid, finish, points, is_win, is_podium, is_pole | the numbers we analyse |

The real warehouse has 7 dimensions (also status, session, tyre compound), a lap-times fact table with 296,727 rows and a snowflake schema; 33 tables in total. This simplified file builds the core star.


**4. Simplified code**
```python
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
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `results = pd.read_csv(SOURCE_FILE)` | Extract: read all 8,650 results into a table in memory |
| `dim_driver = results[[...]].drop_duplicates("driver_id")` | Keep one row per driver: this is the driver dimension |
| `dim_constructor = ...`, `dim_race = ...` | Same for teams and races |
| `dim_date["month"] = ...dt.month`, `["quarter"] = ...dt.quarter` | Build the date hierarchy day → month → quarter → season |
| `fact = results[["race_id", "driver_id", ...]]` | The fact table keeps only keys and measures |
| `fact["is_win"] = (fact["finish_position"] == 1).astype(int)` | 1 if the driver won, 0 if not |
| `table.to_sql(name, connection, ...)` | Load: write each table into the SQLite file |
| `assert fact["race_id"].isin(dim_race["race_id"]).all()` | Check: every fact row points to a real race (referential integrity) |

**6. Say this in the jury:** "Our fact table has one row per driver per Grand Prix. The dimensions describe who drove, for which team, at which race and on which date. We built it with ETL: read the file, split it into dimensions and facts, and load it into the warehouse."

**7. Viva question:** *Why is the grain one driver per race?*
**Answer:** Every measure we care about (grid slot, finish, points) belongs to one driver in one race. A finer grain (one lap) is in the separate lap-times fact table; a coarser grain (one season) would lose the race detail.

---

## File 2: `olap_queries.py`

**1. Location:** `exam_simplified/01_data_warehouse/olap_queries.py` (real: `00_data_warehouse/olap_queries.sql`, 12 queries)

**2. What it does:** runs the five OLAP operations on the star schema and prints the answers.

**3. Parameters and logic**
| Operation | Example in the file | What it means |
|---|---|---|
| Roll-up | wins per team per season | climb the hierarchy: race → season |
| Drill-down | Red Bull points per quarter of 2023 | go down: season → quarter |
| Slice | winners of races in Italy | fix **one** dimension |
| Dice | wins from grid 1–3 in 2021–2024 | fix **several** dimensions |
| Pivot | points of each team, one column per season | turn rows into columns |


**4. Simplified code**
```python
# ============================================================
# FILE: 01_data_warehouse/olap_queries.py
# REAL MODULE: 00_data_warehouse/olap_queries.sql (12 queries) and run_olap_suite.py
# WHAT IT DOES: runs the 5 classic OLAP operations on the star schema
#   ROLL-UP, DRILL-DOWN, SLICE, DICE and PIVOT.
# Run build_star_schema.py first.
# ============================================================

import os
import sqlite3
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "output", "exam_warehouse.db")
connection = sqlite3.connect(DB)


def run(title, sql):
    """Runs one SQL query and prints the first rows of the answer."""
    print("\n=====", title, "=====")
    print(pd.read_sql(sql, connection).head(8).to_string(index=False))


# 1. ROLL-UP: add up wins from single races to whole seasons (climbing the date hierarchy)
run("ROLL-UP: wins per team per season (2024)", """
    SELECT d.season, c.constructor_name, SUM(f.is_win) AS wins
    FROM FACT_RACE_RESULTS f
    JOIN DIM_DATE d        ON d.race_id = f.race_id
    JOIN DIM_CONSTRUCTOR c ON c.constructor_id = f.constructor_id
    WHERE d.season = 2024
    GROUP BY d.season, c.constructor_name
    ORDER BY wins DESC""")

# 2. DRILL-DOWN: the opposite - go from a season down to each quarter of that season
run("DRILL-DOWN: Red Bull points per quarter of 2023", """
    SELECT d.quarter, SUM(f.race_points) AS points
    FROM FACT_RACE_RESULTS f
    JOIN DIM_DATE d        ON d.race_id = f.race_id
    JOIN DIM_CONSTRUCTOR c ON c.constructor_id = f.constructor_id
    WHERE d.season = 2023 AND c.constructor_name = 'Red Bull'
    GROUP BY d.quarter""")

# 3. SLICE: fix ONE dimension to one value (only races in Italy)
run("SLICE: winners of races held in Italy", """
    SELECT r.season, r.race_name, dr.driver_name
    FROM FACT_RACE_RESULTS f
    JOIN DIM_RACE r    ON r.race_id = f.race_id
    JOIN DIM_DRIVER dr ON dr.driver_id = f.driver_id
    WHERE r.circuit_country = 'Italy' AND f.is_win = 1
    ORDER BY r.season DESC""")

# 4. DICE: fix SEVERAL dimensions at once (seasons 2021-2024 AND starting in the top 3)
run("DICE: wins from the top-3 grid slots, 2021-2024", """
    SELECT d.season, f.grid_position, SUM(f.is_win) AS wins
    FROM FACT_RACE_RESULTS f
    JOIN DIM_DATE d ON d.race_id = f.race_id
    WHERE d.season BETWEEN 2021 AND 2024 AND f.grid_position BETWEEN 1 AND 3
    GROUP BY d.season, f.grid_position""")

# 5. PIVOT: turn rows into columns (one column per season)
run("PIVOT: points of the top teams, seasons as columns", """
    SELECT c.constructor_name,
           SUM(CASE WHEN d.season = 2022 THEN f.race_points ELSE 0 END) AS "2022",
           SUM(CASE WHEN d.season = 2023 THEN f.race_points ELSE 0 END) AS "2023",
           SUM(CASE WHEN d.season = 2024 THEN f.race_points ELSE 0 END) AS "2024"
    FROM FACT_RACE_RESULTS f
    JOIN DIM_DATE d        ON d.race_id = f.race_id
    JOIN DIM_CONSTRUCTOR c ON c.constructor_id = f.constructor_id
    GROUP BY c.constructor_name
    ORDER BY "2024" DESC""")

connection.close()
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `def run(title, sql)` | A helper that runs one SQL query and prints the first 8 rows |
| `FROM FACT_RACE_RESULTS f JOIN DIM_DATE d ON d.race_id = f.race_id` | A star join: the fact table joined to one dimension |
| `SUM(f.is_win) ... GROUP BY d.season, c.constructor_name` | Roll-up: add the wins up per season and team |
| `WHERE r.circuit_country = 'Italy'` | Slice: keep one value of one dimension |
| `WHERE d.season BETWEEN 2021 AND 2024 AND f.grid_position BETWEEN 1 AND 3` | Dice: limits on two dimensions at once |
| `SUM(CASE WHEN d.season = 2022 THEN f.race_points ELSE 0 END) AS "2022"` | Pivot: one column per season |

**6. Say this in the jury:** "OLAP lets us look at the same facts from different angles. Roll-up adds detail together, drill-down splits it apart, slice and dice filter, and pivot rotates the table."

**7. Viva question:** *What is the difference between slice and dice?*
**Answer:** Slice fixes one dimension to one value (only Italy). Dice applies conditions on two or more dimensions at once (seasons 2021–2024 and grid 1–3), which gives a smaller sub-cube.
