-- DWDM JURY: F1 RACE INTELLIGENCE ON SNOWFLAKE
-- Open the worksheets in this order. Every one is read-only: nothing creates, changes or deletes data.
--
--   01_environment.sql                 1. Snowflake environment: account, region, warehouse, database
--   02_database_and_schemas.sql        2. Database and schema creation (GET_DDL shows how they were created)
--   03_tables_and_data_loading.sql     3. Table creation and data loading: stage files, COPY INTO history, row counts
--   04_star_schema_olap.sql            4. SQL on the loaded data: star joins, roll-up, drill-down, slice/dice, QUALIFY
--   05_snowflake_schema.sql            4. SQL on the normalised (snowflake) schema
--   06_design_to_snowflake_check.sql   5. The designed warehouse vs. Snowflake: row counts match
--   07_ml_results.sql                  Classifier comparison, association rules, K-Means tiers
--   08_platform_features.sql           Clone, Time Travel, secure view, stream + task, dynamic table, Streamlit app
--   09_race_predictor.sql              Race predictor: predicted winner per race, accuracy vs. the pole-sitter
--   10_forecast_2025.sql               2025 forecast: predicted winner of every upcoming Grand Prix
--
-- Run this file first: it wakes the warehouse so later results come back instantly.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;
SELECT 'Ready: ' || CURRENT_WAREHOUSE() || ' on ' || CURRENT_DATABASE() AS status;
