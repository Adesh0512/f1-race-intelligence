-- 10 NEXT-RACE FORECAST: who the model expects to win the upcoming Grands Prix
-- History = f1.zip (1994-2024) + Jolpica-F1 results since; the champion is retrained on all of it.
-- Qualifying has not happened, so the grid is projected from each driver's average start over his last 5 races.
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- Favourite, runner-up and third for each upcoming race
SELECT season, race_name, race_date,
       MAX(IFF(predicted_rank = 1, driver_name, NULL)) AS favourite,
       MAX(IFF(predicted_rank = 1, ROUND(win_probability, 1), NULL)) AS favourite_pct,
       MAX(IFF(predicted_rank = 2, driver_name, NULL)) AS second,
       MAX(IFF(predicted_rank = 3, driver_name, NULL)) AS third
FROM ML.RACE_FORECAST_UPCOMING
GROUP BY season, race_name, race_date
ORDER BY race_date;

-- Full forecast for the very next race
SELECT driver_name, constructor_name, projected_grid, ROUND(win_probability, 1) AS win_pct
FROM ML.RACE_FORECAST_UPCOMING
WHERE race_date = (SELECT MIN(race_date) FROM ML.RACE_FORECAST_UPCOMING)
ORDER BY win_probability DESC;

-- Real-world test: trained on 1994-2024, then asked to call every race since
SELECT COUNT(*) AS races, SUM(model_correct) AS model_correct, SUM(pole_correct) AS pole_sitter_correct,
       ROUND(AVG(model_correct) * 100, 1) AS model_hit_pct
FROM ML.REAL_WORLD_TEST;

SELECT season, round, race_name, predicted_winner, actual_winner, pole_sitter, model_correct
FROM ML.REAL_WORLD_TEST
ORDER BY season DESC, round DESC;
