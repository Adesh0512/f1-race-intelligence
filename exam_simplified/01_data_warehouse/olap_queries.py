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
