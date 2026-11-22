-- 01 ENVIRONMENT: which account, warehouse and database this project runs on
-- Read-only. Run top to bottom.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() AS account,
       CURRENT_REGION() AS region, CURRENT_ROLE() AS role,
       CURRENT_WAREHOUSE() AS warehouse, CURRENT_DATABASE() AS database, CURRENT_VERSION() AS snowflake_version;

-- Compute: the virtual warehouse (X-Small, suspends after 60 s idle)
SHOW WAREHOUSES LIKE 'F1_WH';

-- Storage: the project database
SHOW DATABASES LIKE 'F1_PREDICTION_DB';
