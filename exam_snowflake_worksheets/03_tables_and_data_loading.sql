-- 03 TABLE CREATION AND DATA LOADING (PUT to stage, then COPY INTO)
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- Table definition
SELECT GET_DDL('TABLE', 'RAW.RAW_RACE_RESULTS') AS table_ddl;

-- Files uploaded to the internal stage with PUT
LIST @RAW.F1_RAW_STAGE;

-- Snowflake's own record of every COPY INTO (kept 14 days)
SELECT schema_name || '.' || table_name AS target_table,
       SPLIT_PART(file_name, '/', -1) AS staged_file,
       row_count AS rows_loaded, error_count AS errors, status,
       TO_VARCHAR(CONVERT_TIMEZONE('Asia/Kolkata', last_load_time), 'YYYY-MM-DD HH24:MI') AS loaded_at_ist
FROM F1_PREDICTION_DB.INFORMATION_SCHEMA.LOAD_HISTORY
ORDER BY last_load_time;

-- Row counts in every table
SELECT table_schema, table_name, table_type, row_count
FROM F1_PREDICTION_DB.INFORMATION_SCHEMA.TABLES
WHERE table_schema IN ('RAW', 'CLEAN', 'DW', 'ML', 'ANALYTICS')
ORDER BY table_schema, table_name;
