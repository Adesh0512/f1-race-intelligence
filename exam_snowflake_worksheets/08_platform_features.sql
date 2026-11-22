-- 08 SNOWFLAKE PLATFORM FEATURES
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- Zero-copy clone: same rows, no extra storage
SELECT (SELECT COUNT(*) FROM CLEAN.F1_MODELING_MASTER) AS original_rows,
       (SELECT COUNT(*) FROM CLEAN.F1_MODELING_MASTER_DEV_CLONE) AS clone_rows;

-- Time Travel: the table as it was 5 minutes ago
SELECT COUNT(*) AS rows_5_minutes_ago FROM CLEAN.F1_MODELING_MASTER AT (OFFSET => -60 * 5);

-- Secure view (definition hidden from other roles)
SELECT * FROM ANALYTICS.SECURE_F1_PUBLIC_LEADERBOARD
WHERE season = 2024 AND is_win = 1
ORDER BY round;

-- Change data capture: stream + scheduled task (task kept suspended to save credits)
SHOW STREAMS IN DATABASE F1_PREDICTION_DB;
SHOW TASKS IN DATABASE F1_PREDICTION_DB;

-- Dynamic table (auto-refreshing query result; suspended to save credits)
SHOW DYNAMIC TABLES IN DATABASE F1_PREDICTION_DB;

-- The dashboard itself, running inside Snowflake
SHOW STREAMLITS IN ACCOUNT;
