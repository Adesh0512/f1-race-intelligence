# Opening the ApexIQ Power BI dashboard (Windows)

1. Install **Power BI Desktop** (free, Microsoft Store) on a Windows PC.
2. Unzip this folder anywhere. Keep all files together.
3. Double-click **`ApexIQ_F1_Dashboard.pbip`**. Power BI Desktop opens the report with all data inside the project (no files to link, no internet needed).
   - If it says the project format isn't enabled: *File → Options and settings → Options → Preview features*, tick **Power BI Project (.pbip) save option** and **Store reports using enhanced metadata format (PBIR)**, restart Power BI Desktop, and open the `.pbip` again.
4. Click **Refresh** once (Home → Refresh) so every table loads.
5. **File → Save as → Power BI file (.pbix)**: this gives you the single `.pbix` file to show or share.

## Pages (same order as the Streamlit dashboard)
| Page | What it shows |
|---|---|
| Overview | Winners picked (40 of 68), XGBoost ROC-AUC 0.9629, 8,650 warehouse rows, 1,393 rules, 703 driver-seasons, 3 tiers |
| 1. Data warehouse (star schema) | A real star schema in the model: Fact_Race_Results joined to Dim_Race, Dim_Driver, Dim_Constructor. Roll-up matrix of wins by team × season; season and team slicers filter the fact through its dimensions |
| 1. Snowflake deployment | Tables and views in F1_PREDICTION_DB by layer (RAW → CLEAN → DW → ML → ANALYTICS), with row counts from the live account |
| 2. Supervised dataset | 12,358 entries and 577 Grands Prix per season, coloured by the chronological train / test split; one winner per race |
| 2. Pattern mining | Apriori candidates vs FP-tree nodes as support drops; all 1,393 rules, filterable by outcome |
| 2. Classifier comparison and validation | ROC-AUC and winners picked for 7 models; expanding-window validation vs the grid-only baseline |
| 2. Classification algorithm (XGBoost) | Accuracy, precision, recall, F1; confusion matrix; pick a race to see each driver's win probability; feature importance |
| 3. Clustering comparison | 6 algorithms: silhouette, Davies-Bouldin, Calinski-Harabasz, stability; elbow curve for k |
| 3. K-Means driver tiers | 703 driver-seasons on the PCA map by tier, tier profiles, tiers per season |
| 3. Clustering performance metrics | Quality metrics, and each tier against the real championship position |

## Using the filters (good to demo)
- **Season** (range slider) and **Era** are synced: change them on one page and the Warehouse, Supervised dataset, Classification and K-Means pages all follow, KPI cards included.
- **Warehouse:** pick a **Team** or **Driver**: the fact table is filtered through its dimension tables, so every KPI and chart recalculates. This is the star schema working live.
- **Classification:** pick a **Grand Prix** to see each driver's predicted win probability; the gauge compares the winner-pick rate with the pole-sitter baseline (target line).
- **Pattern mining:** pick an **Outcome** (e.g. Outcome_Winner) to see only the rules that predict it; the scatter shows support vs. confidence, bubble size = lift.
- Click any bar or row to cross-filter the other visuals on the page; click again to clear.

The numbers come from the same module outputs as the Streamlit dashboards.
To rebuild this folder after rerunning the modules: `.venv/bin/python powerbi/build_pbip.py`.
