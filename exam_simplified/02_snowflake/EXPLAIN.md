# Folder 02 — Snowflake Cloud Deployment

**Responsibility of this folder:** put the warehouse into the Snowflake cloud in five layers and use Snowflake's cloud features.
**Real project:** `deploy_to_snowflake.py`, `MASTER_SNOWFLAKE_DEPLOYMENT.sql` (42 objects), `deploy_streamlit_app.py` and the read-only worksheets in `exam_snowflake_worksheets/`.

---

## File: `deploy_to_snowflake.py`

**1. Location:** `exam_simplified/02_snowflake/deploy_to_snowflake.py`

**2. What it does:** lists, in order, the SQL steps the real deployment runs. With `RUN = False` (the default) it only prints them; with `RUN = True` it connects using the login stored in `.env`. The password is never written in the code.

**3. Parameters and logic**
| Parameter | Value | Why |
|---|---|---|
| Account | UKFIGDV-WD45232 (AWS ap-southeast-7) | your own Snowflake account |
| Warehouse | `F1_WH`, X-Small, auto-suspend 60 s | smallest size; sleeps when idle to save credits |
| Database | `F1_PREDICTION_DB` | holds everything |
| Schemas | RAW → CLEAN → DW → ML → ANALYTICS | one layer per stage of the data |
| Objects | 42 in total, 29 tables and views | counted from the master SQL file |

Locally the pipeline is **ETL** (Python cleans, then loads). In Snowflake it is **ELT**: files are loaded raw first (`PUT` + `COPY INTO`), then transformed with SQL inside Snowflake.


**4. Simplified code**
```python
# ============================================================
# FILE: 02_snowflake/deploy_to_snowflake.py
# REAL MODULE: deploy_to_snowflake.py + MASTER_SNOWFLAKE_DEPLOYMENT.sql
# WHAT IT DOES: builds the warehouse in the Snowflake cloud, layer by layer:
#   RAW (files as they are) -> CLEAN (checked) -> DW (star schema) -> ML (model results) -> ANALYTICS (what users see)
# By default it only PRINTS the steps. It connects only if RUN = True and the .env file has your login.
# The password is never written in this file.
# ============================================================

import os

RUN = False   # keep False in the exam: it just shows the steps

# Each step is one SQL command, in the same order as the real deployment
STEPS = [
    ("Create a small compute warehouse that sleeps after 60 seconds",
     "CREATE WAREHOUSE IF NOT EXISTS F1_WH WITH WAREHOUSE_SIZE = 'X-SMALL' AUTO_SUSPEND = 60"),
    ("Create the database", "CREATE DATABASE IF NOT EXISTS F1_PREDICTION_DB"),
    ("Create the five layers (schemas)",
     "CREATE SCHEMA IF NOT EXISTS RAW; CREATE SCHEMA IF NOT EXISTS CLEAN; CREATE SCHEMA IF NOT EXISTS DW; "
     "CREATE SCHEMA IF NOT EXISTS ML; CREATE SCHEMA IF NOT EXISTS ANALYTICS"),
    ("Create a stage: a folder inside Snowflake for uploaded files", "CREATE OR REPLACE STAGE RAW.F1_RAW_STAGE"),
    ("Upload a CSV file to the stage", "PUT 'file://data/raw_race_results.csv' @RAW.F1_RAW_STAGE"),
    ("Bulk-load the file into a RAW table", "COPY INTO RAW.RAW_RACE_RESULTS FROM @RAW.F1_RAW_STAGE/raw_race_results.csv"),
    ("ELT: clean the data with SQL inside Snowflake", "CREATE TABLE CLEAN.F1_MODELING_MASTER AS SELECT ... FROM RAW.RAW_MODELING_MASTER"),
    ("Zero-copy clone: an instant copy that uses no extra storage",
     "CREATE OR REPLACE TABLE CLEAN.F1_MODELING_MASTER_DEV_CLONE CLONE CLEAN.F1_MODELING_MASTER"),
    ("Time Travel: read the table as it was 60 seconds ago",
     "SELECT COUNT(*) FROM CLEAN.F1_MODELING_MASTER AT (OFFSET => -60)"),
    ("Stream: records every new race result (change data capture)",
     "CREATE OR REPLACE STREAM RAW.STREAM_RACE_RESULTS_CDC ON TABLE RAW.RAW_RACE_RESULTS"),
    ("Task: a scheduled job that runs when the stream has new rows (kept suspended)",
     "CREATE OR REPLACE TASK ML.TASK_AUTO_SCORE_F1_PREDICTIONS ... WHEN SYSTEM$STREAM_HAS_DATA('RAW.STREAM_RACE_RESULTS_CDC')"),
    ("Dynamic table: refreshes itself within 1 hour (rolling driver form)",
     "CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.DT_DRIVER_SEASON_FORM TARGET_LAG = '1 hour' ..."),
    ("Secure view: a read-only window with only public columns",
     "CREATE OR REPLACE SECURE VIEW ANALYTICS.SECURE_F1_PUBLIC_LEADERBOARD AS SELECT ..."),
]

for number, (meaning, sql) in enumerate(STEPS, start=1):
    print(f"Step {number:>2}: {meaning}\n         {sql}\n")

if RUN:
    # Read the login from the .env file (never typed into code)
    import snowflake.connector
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    connection = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"], role="ACCOUNTADMIN")
    cursor = connection.cursor()
    cursor.execute("SELECT CURRENT_ACCOUNT(), CURRENT_VERSION()")
    print("Connected to Snowflake:", cursor.fetchone())
    connection.close()

print("In total the real deployment creates 42 objects; 29 of them are tables and views.")
```

**5. Line by line**
| Code | Meaning |
|---|---|
| `RUN = False` | Safety switch: only print, do not connect |
| `CREATE WAREHOUSE ... X-SMALL AUTO_SUSPEND = 60` | The compute engine; it stops after 60 idle seconds |
| `CREATE SCHEMA RAW / CLEAN / DW / ML / ANALYTICS` | The five layers |
| `CREATE STAGE RAW.F1_RAW_STAGE` | A landing folder inside Snowflake for files |
| `PUT 'file://...' @RAW.F1_RAW_STAGE` | Upload a CSV file to the stage |
| `COPY INTO RAW.RAW_RACE_RESULTS FROM @...` | Bulk-load the file into a table |
| `... CLONE CLEAN.F1_MODELING_MASTER` | Zero-copy clone: an instant copy sharing the same storage |
| `AT (OFFSET => -60)` | Time Travel: the table as it was 60 seconds ago |
| `CREATE STREAM ...` | Records every new row (change data capture) |
| `CREATE TASK ... WHEN SYSTEM$STREAM_HAS_DATA(...)` | A scheduled job that runs only if the stream has new rows |
| `CREATE DYNAMIC TABLE ... TARGET_LAG = '1 hour'` | A table that refreshes itself |
| `CREATE SECURE VIEW ...` | A read-only window with only public columns |
| `load_dotenv(...)`, `os.environ["SNOWFLAKE_PASSWORD"]` | Read the login from `.env`, never from the code |

**6. Say this in the jury:** "We deployed the warehouse to Snowflake in five layers: RAW keeps the files untouched, CLEAN is checked, DW is the star and snowflake schema, ML holds the model results and ANALYTICS is what users see. We also used cloning, Time Travel, a stream and task, a dynamic table and a secure view. The dashboard itself runs inside Snowflake too."

**7. Viva question:** *What is the difference between a zero-copy clone and Time Travel?*
**Answer:** A clone makes a new table instantly that shares the original's storage, for safe testing. Time Travel reads an existing table as it was at an earlier moment, for recovery and auditing.

**Be honest if asked:** the task scores new results with a simple pole-position rule, not XGBoost, and it is kept suspended to save trial credits. Running XGBoost inside Snowflake would need a Snowpark Python function (future work).
