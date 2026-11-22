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
