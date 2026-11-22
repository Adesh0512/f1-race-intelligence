# Snowflake worksheets for the jury

Open them in this order. Every file is **read-only**: nothing here creates, changes or deletes data,
so any file can be run top to bottom in front of the jury.

| File | Shows (rubric B, Snowflake deployment) |
|---|---|
| `01_environment.sql` | 1. The Snowflake environment: account, region, warehouse, database |
| `02_database_and_schemas.sql` | 2. Database and schema creation (`GET_DDL` prints how they were created) |
| `03_tables_and_data_loading.sql` | 3. Table creation and data loading: stage files, `COPY INTO` history, row counts |
| `04_star_schema_olap.sql` | 4. SQL on the loaded data: star joins, roll-up, drill-down, slice/dice, `QUALIFY` |
| `05_snowflake_schema.sql` | 4. SQL on the normalised (snowflake) schema |
| `06_design_to_snowflake_check.sql` | 5. The designed warehouse vs. Snowflake: row counts match |
| `07_ml_results.sql` | Classifier comparison, association rules and K-Means tiers stored in Snowflake |
| `08_platform_features.sql` | Clone, Time Travel, secure view, stream + task, dynamic table, the Streamlit app |

**Before the jury:** run `01_environment.sql` once so the warehouse is awake.
**Shortcut:** put the cursor in one query and press Cmd+Enter (Ctrl+Enter on Windows) to run only that query.
