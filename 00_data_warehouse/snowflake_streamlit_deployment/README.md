# Streamlit-in-Snowflake (SiS) Deployment: Verification Scripts

The Jury 2 version of this app was deployed **inside Snowflake** as a native Streamlit app (October 2026):

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

## How it was deployed (October 2026)
1. `assemble_stage.py` copied the app (`streamlit_app.py`, `db_utils.py`, `pages/`, data, models) into a `staging_upload/` folder.
2. `upload_to_sis_stage.py` ran `PUT file://… @F1_STREAMLIT_STAGE AUTO_COMPRESS=FALSE` for every file.
3. The app was registered with `CREATE STREAMLIT F1_RACE_INTELLIGENCE ROOT_LOCATION='@…F1_STREAMLIT_STAGE' MAIN_FILE='streamlit_app.py'`.

Those upload scripts were **not** brought into this project. They are hard-wired to the old Jury 2 folder layout (`logic/`, `jury/`) and would re-deploy the outdated Jury 2 pages. The deployed app therefore still shows the Jury 2 version; redeploying the end-semester dashboard would mean re-staging the current `pages/` and module outputs.
