# F1 Race Performance Data Warehouse — STEP 1

This project implements both a multi-dimensional **Star Schema** and a **Snowflake Schema** data warehouse designed to analyze Formula 1 race performance, driver statistics, constructor histories, qualifying results, pit stop efficiency, and championship standings from 2004 to 2024.

---

## 1. Project Directory Structure

```text
f1_dw/
├── README.md                      # Project documentation and comparison guidelines (This file)
├── showcase.html                  # Interactive, styled HTML presentation dashboard with dynamic toggles
├── create_schema.sql              # PostgreSQL DDL script (Defaults to Star Schema format)
├── create_star_schema.sql         # PostgreSQL DDL script representing the pure Star Schema
├── create_snowflake_schema.sql    # PostgreSQL DDL script representing the Snowflake Schema
├── data_dictionary.md             # Data dictionary detailing columns across both schemas
├── er_diagram.mmd                 # Live Mermaid ER diagram (Defaults to Star Schema format)
├── er_diagram_star.mmd            # Mermaid ERD diagram representing the Star Schema
├── er_diagram_snowflake.mmd       # Mermaid ERD diagram representing the Snowflake Schema
└── source_to_target_mapping.csv   # Extraction and transformation blueprint mapping CSV to target tables
```

---

## 2. Interactive Presentation Dashboard

We created a custom-styled, interactive presentation dashboard at [showcase.html](showcase.html). 

To showcase this project, simply **double-click the file to open it in any web browser**. It includes:
* **Interactive Schema Switcher** to dynamically toggle the entire dashboard view between the **Star Schema** and **Snowflake Schema**.
* **Interactive ERD** rendering the live Mermaid graph for the selected model.
* **Searchable Data Dictionary** to filter and query column definitions based on the active schema configuration.
* **Interactive Source-to-Target mapping** showing mapping rules (updating targets depending on whether circuit fields are denormalized or isolated).
* **Copy-pasteable SQL DDL script view** highlighting the correct SQL code.

---

## 3. PostgreSQL Database Schema DDLs

We provide two distinct dimensional modeling implementations:
1. **Star Schema (Denormalized)**: Combines circuit attributes directly into `DIM_RACE` (no `DIM_CIRCUIT` table), optimizing query times by eliminating extra joins.
2. **Snowflake Schema (Normalized)**: Houses circuit details in a normalized sub-dimension table `DIM_CIRCUIT` linked via a foreign key in `DIM_RACE`.

The following default DDL script (also saved in [create_schema.sql](create_schema.sql)) implements the **Star Schema** configuration:

```sql
-- PostgreSQL DDL script for F1 Race Performance Data Warehouse (Pure Star Schema)
-- Creates dimension tables first (with circuit attributes denormalized into DIM_RACE),
-- then the central FACT_RACE_RESULTS table.

BEGIN;

--------------------------------------------------------------------------------
-- 1. DROP EXISTING TABLES (FOR IDEMPOTENT EXECUTION)
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS FACT_RACE_RESULTS CASCADE;
DROP TABLE IF EXISTS DIM_DATE CASCADE;
DROP TABLE IF EXISTS DIM_STATUS CASCADE;
DROP TABLE IF EXISTS DIM_RACE CASCADE;
DROP TABLE IF EXISTS DIM_CONSTRUCTOR CASCADE;
DROP TABLE IF EXISTS DIM_DRIVER CASCADE;

--------------------------------------------------------------------------------
-- 2. CREATE DIMENSION TABLES
--------------------------------------------------------------------------------

-- DIM_DRIVER: Details of drivers participating in F1
CREATE TABLE DIM_DRIVER (
    driver_id INT PRIMARY KEY,
    driver_ref VARCHAR(50) NOT NULL UNIQUE,
    driver_code VARCHAR(3),
    driver_name VARCHAR(100) NOT NULL,
    driver_dob DATE,
    driver_nationality VARCHAR(50)
);

-- DIM_CONSTRUCTOR: Details of constructors/teams participating in F1
CREATE TABLE DIM_CONSTRUCTOR (
    constructor_id INT PRIMARY KEY,
    constructor_ref VARCHAR(50) NOT NULL UNIQUE,
    constructor_name VARCHAR(100) NOT NULL,
    constructor_nationality VARCHAR(50)
);

-- DIM_RACE: Details of races scheduled across seasons (includes denormalized Circuit details)
CREATE TABLE DIM_RACE (
    race_id INT PRIMARY KEY,
    season_year INT NOT NULL,
    round INT NOT NULL,
    race_name VARCHAR(100) NOT NULL,
    race_date DATE NOT NULL,
    race_start_time TIME,
    
    -- Denormalized Circuit Attributes (Merged from DIM_CIRCUIT to form a flat Star Schema)
    circuit_id INT NOT NULL,
    circuit_name VARCHAR(150) NOT NULL,
    circuit_location VARCHAR(100),
    circuit_country VARCHAR(100),
    circuit_latitude DECIMAL(9,6),
    circuit_longitude DECIMAL(9,6),
    circuit_altitude_m INT,
    
    CONSTRAINT uq_race_season_round UNIQUE (season_year, round)
);

-- DIM_STATUS: Map of status descriptions (Finished, DNF reasons, etc.)
CREATE TABLE DIM_STATUS (
    status_id SERIAL PRIMARY KEY,
    status_description VARCHAR(100) NOT NULL UNIQUE
);

-- DIM_DATE: Calendar date dimension for time-slice analysis
CREATE TABLE DIM_DATE (
    date_id INT PRIMARY KEY, -- Format: YYYYMMDD
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name VARCHAR(20) NOT NULL,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    day_name VARCHAR(20) NOT NULL
);

--------------------------------------------------------------------------------
-- 3. CREATE FACT TABLE
--------------------------------------------------------------------------------

-- FACT_RACE_RESULTS: Central fact table storing results, qualifying, pit summaries,
-- standings and indicators. Links directly to all 5 flat dimensions.
CREATE TABLE FACT_RACE_RESULTS (
    result_id SERIAL PRIMARY KEY,
    race_id INT NOT NULL REFERENCES DIM_RACE(race_id),
    driver_id INT NOT NULL REFERENCES DIM_DRIVER(driver_id),
    constructor_id INT NOT NULL REFERENCES DIM_CONSTRUCTOR(constructor_id),
    date_id INT NOT NULL REFERENCES DIM_DATE(date_id),
    status_id INT NOT NULL REFERENCES DIM_STATUS(status_id),
    
    -- Race Performance Metrics
    car_number INT,
    grid_position INT NOT NULL,
    qualifying_position INT,
    qualifying_best_time_sec DECIMAL(6,3),
    finish_position INT, -- NULL if DNF
    finish_position_text VARCHAR(10),
    race_points DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    race_laps INT NOT NULL,
    race_time VARCHAR(20),
    race_milliseconds BIGINT,
    
    -- Fastest Lap & Pit Stop Summary Metrics
    fastest_lap_number INT,
    fastest_lap_rank INT,
    fastest_lap_time VARCHAR(20),
    fastest_lap_speed DECIMAL(6,3),
    pit_stop_count INT NOT NULL DEFAULT 0,
    total_pit_duration_sec DECIMAL(7,3) NOT NULL DEFAULT 0.000,
    avg_pit_duration_sec DECIMAL(6,3) NOT NULL DEFAULT 0.000,
    fastest_pit_duration_sec DECIMAL(6,3) NOT NULL DEFAULT 0.000,
    last_pit_lap INT NOT NULL DEFAULT 0,
    
    -- Lap timing aggregates
    laps_recorded INT NOT NULL DEFAULT 0,
    fastest_recorded_lap_ms INT,
    average_lap_ms INT,
    
    -- Standings & Championship Metrics (Cumulative up to this race)
    driver_standing_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    driver_championship_position INT,
    driver_championship_wins INT NOT NULL DEFAULT 0,
    constructor_standing_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    constructor_championship_position INT,
    constructor_championship_wins INT NOT NULL DEFAULT 0,
    constructor_race_points DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    driver_standing_gap_to_leader DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    constructor_standing_gap_to_leader DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    
    -- Sprint & Positioning Deltas
    sprint_position INT,
    sprint_points DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    position_gain INT,
    qualifying_to_finish_delta INT,
    
    -- Indicators & Derived metrics
    is_pole INT NOT NULL CHECK (is_pole IN (0, 1)),
    is_podium INT NOT NULL CHECK (is_podium IN (0, 1)),
    is_win INT NOT NULL CHECK (is_win IN (0, 1)),
    is_top_10 INT NOT NULL CHECK (is_top_10 IN (0, 1)),
    is_dnf INT NOT NULL CHECK (is_dnf IN (0, 1)),
    points_per_lap DECIMAL(6,4),
    race_completion_pct DECIMAL(5,4),
    driver_age_years DECIMAL(5,2),
    
    CONSTRAINT uq_race_driver UNIQUE (race_id, driver_id)
);

--------------------------------------------------------------------------------
-- 4. CREATE INDEXES ON FOREIGN KEYS & COMMON QUERY COLUMNS
--------------------------------------------------------------------------------

-- Dimension Indexes
CREATE INDEX idx_dim_race_season ON DIM_RACE(season_year);

-- FACT_RACE_RESULTS Indexes
CREATE INDEX idx_fact_results_race ON FACT_RACE_RESULTS(race_id);
CREATE INDEX idx_fact_results_driver ON FACT_RACE_RESULTS(driver_id);
CREATE INDEX idx_fact_results_constructor ON FACT_RACE_RESULTS(constructor_id);
CREATE INDEX idx_fact_results_date ON FACT_RACE_RESULTS(date_id);
CREATE INDEX idx_fact_results_status ON FACT_RACE_RESULTS(status_id);

-- Performance Composite Indexes
CREATE INDEX idx_fact_results_season_driver ON FACT_RACE_RESULTS(race_id, driver_id);

COMMIT;
```

---

## 5. PaddockIQ Dashboard (`dashboard.html`)

An advanced, interactive browser dashboard implemented in [dashboard.html](dashboard.html) providing dual visual workspaces:

1. **Live Performance Dashboard**: 
   - Interactive left-rail driver standings with team color chips (Red Bull, McLaren, Ferrari, Mercedes, Aston Martin).
   - Dynamic lap-time trend chart in the center powered by ECharts.
   - Simplified vector racing line track mapping for Monza GP with live vehicle coordinates.
   - Selected driver telemetry details showing real-time tyre compound ages, color-shifting tyre wear progress bars (6px), and track temperature indicators.
2. **Schema Explorer**:
   - Dotted layout grid canvas with neutral slate-blue styling.
   - Collapsible dimension card tables (`DIM_DRIVER`, `DIM_CONSTRUCTOR`, etc.) with gold key 🔑 (PK) and blue link 🔗 (FK) tags.
   - Radially aligned snowflake sub-dimensions (`DIM_CIRCUIT`) connected with dashed normalized edge lines.
   - Search bar filtering, zoom controls (reset/fit/percentage), mini-map tracking, and active element focus modes.
3. **Lineage Mapper**:
   - Interactive mapping interface containing all 68 source CSV columns on the left.
   - Renders target table paths, data types, and specific transformation rules (e.g. data cleaning, key mappings, calendar derivations) in a visual flow panel.
   - Supports bidirectional element clicking: clicking a CSV source highlights its database column target, and clicking a database column displays its CSV source attribute.

To run: double-click the `dashboard.html` file to open it in Chrome, Edge, or Firefox.

