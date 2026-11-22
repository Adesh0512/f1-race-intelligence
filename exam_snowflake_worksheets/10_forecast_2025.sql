-- 10 FORECAST 2025: who the model expects to win each upcoming Grand Prix
-- The model is retrained on every season 1994-2024; each driver's inputs are rebuilt from history up to the end of 2024.
-- Qualifying is unknown, so the grid is projected from each driver's average start over his last 5 races.
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- Predicted winner and runner-up of every 2025 Grand Prix
SELECT round, race_name,
       MAX(IFF(predicted_rank = 1, driver_name, NULL)) AS forecast_winner,
       MAX(IFF(predicted_rank = 1, ROUND(win_probability, 1), NULL)) AS winner_pct,
       MAX(IFF(predicted_rank = 2, driver_name, NULL)) AS main_rival
FROM ML.RACE_FORECAST_2025
GROUP BY round, race_name
ORDER BY round;

-- Full forecast for one race
SELECT driver_name, constructor_name, projected_grid, ROUND(win_probability, 1) AS win_pct
FROM ML.RACE_FORECAST_2025
WHERE race_name = 'Monaco Grand Prix'
ORDER BY win_probability DESC;

-- Expected wins over the season (sum of win probabilities across all races)
SELECT driver_name, constructor_name, ROUND(SUM(win_probability) / 100, 1) AS expected_wins
FROM ML.RACE_FORECAST_2025
GROUP BY driver_name, constructor_name
ORDER BY expected_wins DESC
LIMIT 10;
