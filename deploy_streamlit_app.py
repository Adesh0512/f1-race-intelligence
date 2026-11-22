"""
Uploads the current dashboard to Streamlit in Snowflake (SiS) in the account from .env.
Usage: .venv/bin/python deploy_streamlit_app.py   (run deploy_to_snowflake.py first)
"""

import os
import subprocess

import snowflake.connector
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
STAGE = "F1_PREDICTION_DB.ANALYTICS.F1_STREAMLIT_STAGE"
APP = "F1_PREDICTION_DB.ANALYTICS.F1_RACE_INTELLIGENCE"
# Not needed by the app: build tooling, tests, documents and the old pre-module pipeline outputs
SKIP_DIRS = ("powerbi/", "tests/", "reports/", "docs/", "results/", "app/")
SKIP_EXT = (".pdf", ".png", ".xlsx", ".svg", ".html", ".md")


def app_files():
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    files = [f for f in tracked if f and not f.startswith(SKIP_DIRS) and not f.endswith(SKIP_EXT)]
    files.append(".streamlit/config.toml")
    assert ".env" not in files and "streamlit_app.py" in files and "environment.yml" in files
    return sorted(set(f for f in files if os.path.exists(os.path.join(ROOT, f))))


def deploy():
    load_dotenv(os.path.join(ROOT, ".env"))
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"], role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse="F1_WH", database="F1_PREDICTION_DB", schema="ANALYTICS")
    cs = conn.cursor()
    cs.execute(f"CREATE STAGE IF NOT EXISTS {STAGE} DIRECTORY = (ENABLE = TRUE)")
    cs.execute(f"REMOVE @{STAGE}")  # drop files from an earlier upload so the stage mirrors the repo
    files = app_files()
    for i, f in enumerate(files, 1):
        sub = os.path.dirname(f)
        target = f"@{STAGE}" + (f"/{sub}" if sub else "")
        print(f"[{i}/{len(files)}] {f}", flush=True)
        cs.execute(f"PUT 'file://{os.path.join(ROOT, f)}' '{target}' AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
    cs.execute(f"""CREATE OR REPLACE STREAMLIT {APP}
        FROM '@{STAGE}'
        MAIN_FILE = 'streamlit_app.py'
        QUERY_WAREHOUSE = F1_WH
        RUNTIME_NAME = 'SYSTEM$WAREHOUSE_RUNTIME'
        TITLE = 'ApexIQ F1 Race Intelligence'""")
    cs.execute(f"ALTER STREAMLIT {APP} ADD LIVE VERSION FROM LAST")
    row = cs.execute(f"DESCRIBE STREAMLIT {APP}").fetchone()
    print("\nDeployed", APP, "| files:", len(files))
    print("Open it in Snowsight: Projects -> Streamlit -> ApexIQ F1 Race Intelligence")
    conn.close()
    return row


if __name__ == "__main__":
    deploy()
