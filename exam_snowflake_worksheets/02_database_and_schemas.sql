-- 02 DATABASE AND SCHEMA CREATION
-- Read-only: GET_DDL prints how each object was created, without running it again.
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE F1_WH;
USE DATABASE F1_PREDICTION_DB;

-- The five schemas: RAW -> CLEAN -> DW -> ML -> ANALYTICS
SELECT schema_name, created, comment
FROM F1_PREDICTION_DB.INFORMATION_SCHEMA.SCHEMATA
WHERE schema_name IN ('RAW', 'CLEAN', 'DW', 'ML', 'ANALYTICS')
ORDER BY created;

-- How the warehouse, database and a schema were created
SELECT GET_DDL('WAREHOUSE', 'F1_WH') AS warehouse_ddl;
SELECT GET_DDL('SCHEMA', 'F1_PREDICTION_DB.DW') AS dw_schema_ddl;

-- Objects per schema
SELECT table_schema, COUNT_IF(table_type = 'BASE TABLE') AS tables, COUNT_IF(table_type = 'VIEW') AS views
FROM F1_PREDICTION_DB.INFORMATION_SCHEMA.TABLES
WHERE table_schema IN ('RAW', 'CLEAN', 'DW', 'ML', 'ANALYTICS')
GROUP BY table_schema ORDER BY table_schema;
