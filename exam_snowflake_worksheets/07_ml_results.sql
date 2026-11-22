-- 07 MACHINE-LEARNING RESULTS STORED IN SNOWFLAKE (Dashboards 2 and 3)
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- Classifier comparison on the 2022-2024 holdout
SELECT model_name, test_roc_auc, test_pr_auc, top1_winner_hit_pct, top3_podium_hit_pct
FROM ML.MODEL_COMPARISON
ORDER BY test_roc_auc DESC;

-- Strongest association rules (FP-Growth)
SELECT antecedents, consequents, ROUND(support, 4) AS support, ROUND(confidence, 3) AS confidence, ROUND(lift, 2) AS lift
FROM ML.ASSOCIATION_RULES
ORDER BY lift DESC
LIMIT 10;

-- K-Means driver tiers
SELECT cluster_name, COUNT(*) AS driver_seasons, ROUND(AVG(avg_finish), 1) AS avg_finish,
       ROUND(AVG(win_rate), 3) AS avg_win_rate
FROM ML.DRIVER_SEASON_CLUSTERS
GROUP BY cluster_name
ORDER BY avg_finish;

SELECT season, driver_name, constructor_name, cluster_name
FROM ML.DRIVER_SEASON_CLUSTERS
WHERE season = 2024
ORDER BY win_rate DESC
LIMIT 10;
