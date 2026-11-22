-- 04 STAR SCHEMA + OLAP: FACT_RACE_RESULTS_STAR joined to its dimensions
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- Star join: most wins per driver
SELECT d.driver_name, COUNT(*) AS races, SUM(f.is_win) AS wins, SUM(f.is_podium) AS podiums
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_DRIVER d ON d.driver_id = f.driver_id
GROUP BY d.driver_name
ORDER BY wins DESC
LIMIT 10;

-- ROLL-UP: wins by team and season, with a subtotal per team
SELECT c.constructor_name, r.season, SUM(f.is_win) AS wins
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_CONSTRUCTOR c ON c.constructor_id = f.constructor_id
JOIN DW.DIM_RACE_STAR r ON r.race_id = f.race_id
WHERE r.season >= 2020
GROUP BY ROLLUP (c.constructor_name, r.season)
HAVING SUM(f.is_win) > 0
ORDER BY c.constructor_name NULLS LAST, r.season NULLS LAST;

-- DRILL-DOWN: from season to quarter to month (date dimension hierarchy)
SELECT dt.year, dt.quarter, dt.month_name, COUNT(*) AS results, SUM(f.is_win) AS wins
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_DATE dt ON dt.date_id = f.date_id
WHERE dt.year = 2024
GROUP BY dt.year, dt.quarter, dt.month, dt.month_name
ORDER BY dt.quarter, dt.month;

-- SLICE (one season) and DICE (season AND team)
SELECT r.race_name, d.driver_name, f.grid_position, f.finish_position
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_RACE_STAR r ON r.race_id = f.race_id
JOIN DW.DIM_DRIVER d ON d.driver_id = f.driver_id
JOIN DW.DIM_CONSTRUCTOR c ON c.constructor_id = f.constructor_id
WHERE r.season = 2024 AND c.constructor_name = 'McLaren' AND f.is_podium = 1
ORDER BY r.round;

-- Window function + QUALIFY: each season's top winner
SELECT r.season, d.driver_name, SUM(f.is_win) AS wins
FROM DW.FACT_RACE_RESULTS_STAR f
JOIN DW.DIM_DRIVER d ON d.driver_id = f.driver_id
JOIN DW.DIM_RACE_STAR r ON r.race_id = f.race_id
GROUP BY r.season, d.driver_name
QUALIFY ROW_NUMBER() OVER (PARTITION BY r.season ORDER BY wins DESC) = 1
ORDER BY r.season DESC;

-- Insight: how often each grid slot wins
SELECT grid_position, COUNT(*) AS starts, ROUND(100 * AVG(is_win), 1) AS win_pct
FROM DW.FACT_RACE_RESULTS_STAR
WHERE grid_position BETWEEN 1 AND 10
GROUP BY grid_position
ORDER BY grid_position;
