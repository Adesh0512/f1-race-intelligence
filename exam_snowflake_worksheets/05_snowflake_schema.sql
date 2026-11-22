-- 05 SNOWFLAKE SCHEMA: normalised dimension chain race -> circuit -> country
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

SELECT co.country_name, COUNT(DISTINCT r.race_id) AS races_hosted
FROM DW.DIM_RACE_SNOWFLAKE r
JOIN DW.DIM_CIRCUIT ci ON ci.circuit_id = r.circuit_id
JOIN DW.DIM_COUNTRY co ON co.country_id = ci.country_id
GROUP BY co.country_name
ORDER BY races_hosted DESC
LIMIT 10;

-- The same fact, reached through the normalised dimensions (3 hops)
SELECT co.country_name, ci.circuit_name, SUM(f.is_win) AS wins_recorded
FROM DW.FACT_RACE_RESULTS_SNOWFLAKE f
JOIN DW.DIM_RACE_SNOWFLAKE r ON r.race_id = f.race_id
JOIN DW.DIM_CIRCUIT ci ON ci.circuit_id = r.circuit_id
JOIN DW.DIM_COUNTRY co ON co.country_id = ci.country_id
GROUP BY co.country_name, ci.circuit_name
ORDER BY wins_recorded DESC
LIMIT 10;
