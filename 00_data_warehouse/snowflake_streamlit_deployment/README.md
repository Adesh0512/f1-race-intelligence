# Streamlit-in-Snowflake (SiS) Deployment: Verification Scripts

The end-semester dashboard is deployed **inside Snowflake** as a native Streamlit app (November 2026):

| Object | Value |
|---|---|
| Streamlit app | `F1_RACE_INTELLIGENCE` |
| Stage holding the app files | `F1_PREDICTION_DB.ANALYTICS.F1_STREAMLIT_STAGE` |
| Database / warehouse | `F1_PREDICTION_DB` / `F1_WH` |

The scripts below are **read-only**: they inspect what is deployed and never create, change or upload anything. They read credentials from the project-root `.env`.

| Script | What it shows |
|---|---|
| `check_snowflake_app.py` | `SHOW STREAMLITS IN ACCOUNT` (app name, schema, main file, URL id) and the stages in `F1_PREDICTION_DB` |
| `verify_deployment.py` | `DESCRIBE STREAMLIT F1_RACE_INTELLIGENCE` plus the file count on the stage |
| `inspect_sis.py` | App description, stage listing and all stages in `ANALYTICS` |
| `get_stage_app.py` | Downloads the deployed `streamlit_app.py` into `./downloaded_stage/` as proof of what is live |

```bash
.venv/bin/python 00_data_warehouse/snowflake_streamlit_deployment/verify_deployment.py
```

## How it is deployed
```bash
.venv/bin/python deploy_to_snowflake.py     # warehouse, database, tables, DW schemas, ML results
.venv/bin/python deploy_streamlit_app.py    # PUT the app files to @F1_STREAMLIT_STAGE, then CREATE STREAMLIT
```
`deploy_streamlit_app.py` uploads every git-tracked file the app needs (pages, `db_utils.py`, module outputs, models,
`f1_warehouse.db`, `environment.yml`), then runs
`CREATE OR REPLACE STREAMLIT F1_RACE_INTELLIGENCE FROM '@F1_STREAMLIT_STAGE' MAIN_FILE = 'streamlit_app.py' QUERY_WAREHOUSE = F1_WH`.
Inside Snowflake the app uses its own Snowpark session, so no password is uploaded (`.env` is never staged).
