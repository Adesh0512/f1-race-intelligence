-- ApexIQ F1 Race Intelligence: Snowflake queries to show during the jury
-- Paste into a Snowsight worksheet, put the cursor in one query and press Cmd+Enter (Ctrl+Enter on Windows).

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- 1. What is deployed: every table and its row count
SELECT table_schema, table_name, table_type, row_count
FROM information_schema.tables
WHERE table_schema IN ('RAW', 'CLEAN', 'DW', 'ML', 'ANALYTICS')
ORDER BY table_schema, table_name;

-- 2. Star schema: fact joined to its dimensions (most wins per driver)
SELECT d.driver_name, COUNT(*) AS races, SUM(f.is_win) AS wins, SUM(f.is_podium) AS podiums
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_DRIVER d ON d.driver_id = f.driver_id
GROUP BY d.driver_name
ORDER BY wins DESC
LIMIT 10;

-- 3. OLAP roll-up: wins by constructor and season, with subtotals per constructor
SELECT c.constructor_name, r.season, SUM(f.is_win) AS wins
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_CONSTRUCTOR c ON c.constructor_id = f.constructor_id
JOIN DW.DIM_RACE_STAR r ON r.race_id = f.race_id
WHERE r.season >= 2020
GROUP BY ROLLUP (c.constructor_name, r.season)
HAVING SUM(f.is_win) > 0
ORDER BY c.constructor_name NULLS LAST, r.season NULLS LAST;

-- 4. Snowflake schema: race -> circuit -> country (normalised dimension chain)
SELECT co.country_name, COUNT(DISTINCT r.race_id) AS races_hosted
FROM DW.DIM_RACE_SNOWFLAKE r
JOIN DW.DIM_CIRCUIT ci ON ci.circuit_id = r.circuit_id
JOIN DW.DIM_COUNTRY co ON co.country_id = ci.country_id
GROUP BY co.country_name
ORDER BY races_hosted DESC
LIMIT 10;

-- 5. Window function + QUALIFY: each season's champion by wins
SELECT r.season, d.driver_name, SUM(f.is_win) AS wins
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_DRIVER d ON d.driver_id = f.driver_id
JOIN DW.DIM_RACE_STAR r ON r.race_id = f.race_id
GROUP BY r.season, d.driver_name
QUALIFY ROW_NUMBER() OVER (PARTITION BY r.season ORDER BY wins DESC) = 1
ORDER BY r.season DESC;

-- 6. Pole position -> win conversion (drill-down by grid slot)
SELECT grid_position, COUNT(*) AS starts, ROUND(100 * AVG(is_win), 1) AS win_pct
FROM DW.FACT_RACE_RESULTS_STAR
WHERE grid_position BETWEEN 1 AND 10
GROUP BY grid_position
ORDER BY grid_position;

-- 7. Dashboard 2: classifier comparison and strongest association rules
SELECT model_name, test_roc_auc, top1_winner_hit_pct, top3_podium_hit_pct
FROM ML.MODEL_COMPARISON ORDER BY test_roc_auc DESC;

SELECT antecedents, consequents, ROUND(support, 3) AS support, ROUND(confidence, 3) AS confidence, ROUND(lift, 2) AS lift
FROM ML.ASSOCIATION_RULES ORDER BY lift DESC LIMIT 10;

-- 8. Dashboard 3: K-Means driver tiers
SELECT cluster_name, COUNT(*) AS driver_seasons, ROUND(AVG(win_rate), 3) AS avg_win_rate, ROUND(AVG(avg_finish), 1) AS avg_finish
FROM ML.DRIVER_SEASON_CLUSTERS GROUP BY cluster_name ORDER BY avg_win_rate DESC;

SELECT season, driver_name, constructor_name, cluster_name
FROM ML.DRIVER_SEASON_CLUSTERS WHERE season = 2024 ORDER BY win_rate DESC LIMIT 10;

-- 9. Snowflake features
-- Zero-copy clone: same rows, no extra storage
SELECT (SELECT COUNT(*) FROM CLEAN.F1_MODELING_MASTER) AS original, (SELECT COUNT(*) FROM CLEAN.F1_MODELING_MASTER_DEV_CLONE) AS clone;
-- Time Travel: the table as it was 5 minutes ago (works once the table is older than 5 minutes)
SELECT COUNT(*) FROM CLEAN.F1_MODELING_MASTER AT (OFFSET => -60 * 5);
-- Secure view, stream (CDC) and dynamic table
SELECT * FROM ANALYTICS.SECURE_F1_PUBLIC_LEADERBOARD WHERE season = 2024 AND is_win = 1 ORDER BY round;
SHOW STREAMS IN DATABASE F1_PREDICTION_DB;
SHOW DYNAMIC TABLES IN DATABASE F1_PREDICTION_DB;
-- The dashboard itself, running inside Snowflake
SHOW STREAMLITS IN ACCOUNT;
