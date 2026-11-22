-- 09 RACE PREDICTOR: champion XGBoost predictions stored in Snowflake (68 unseen races, 2022-2024)
-- Read-only.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- Every driver's predicted win probability for one race (probabilities in a race add up to 100%)
SELECT driver_name, constructor_name, grid_position, ROUND(win_probability * 100, 1) AS win_pct, finish_position
FROM ML.RACE_PREDICTIONS
WHERE season = 2024 AND race_name = 'British Grand Prix'
ORDER BY win_probability DESC;

-- The model's pick for each race, and whether it was right
SELECT season, race_name, driver_name AS predicted_winner, ROUND(win_probability * 100, 1) AS win_pct,
       IFF(is_win = 1, 'correct', 'missed') AS result
FROM ML.RACE_PREDICTIONS
QUALIFY ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY win_probability DESC) = 1
ORDER BY season DESC, round DESC;

-- Accuracy: winners picked out of 68 races, against always backing the pole-sitter
SELECT COUNT(*) AS races,
       COUNT_IF(model_pick_won) AS model_correct,
       COUNT_IF(pole_won) AS pole_sitter_correct
FROM (
    SELECT race_id,
           MAX(IFF(rank_by_model = 1 AND is_win = 1, TRUE, FALSE)) AS model_pick_won,
           MAX(IFF(grid_position = 1 AND is_win = 1, TRUE, FALSE)) AS pole_won
    FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY win_probability DESC) AS rank_by_model
          FROM ML.RACE_PREDICTIONS)
    GROUP BY race_id
);
