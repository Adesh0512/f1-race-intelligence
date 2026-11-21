# Opening the ApexIQ Power BI dashboard (Windows)

1. Install **Power BI Desktop** (free, Microsoft Store) on a Windows PC.
2. Unzip this folder anywhere. Keep all files together.
3. Double-click **`ApexIQ_F1_Dashboard.pbip`**. Power BI Desktop opens the report with all data loaded (no files to link, no internet needed).
   - If it says the project format isn't enabled: *File → Options and settings → Options → Preview features*, tick **Power BI Project (.pbip) save option** and **Store reports using enhanced metadata format (PBIR)**, restart Power BI Desktop, and open the `.pbip` again.
4. Click **Refresh** once (Home → Refresh) so every table loads.
5. **File → Save as → Power BI file (.pbix)**: this gives you the single `.pbix` file to show or share.

## Pages
| Page | What it shows |
|---|---|
| Race predictor (Dashboard 2) | Winner-picked %, winner-in-top-3 %, Grands Prix count; pick a race to see each driver's predicted win probability next to their grid slot and actual result |
| Classifier comparison (Dashboard 2) | ROC-AUC and winner-picked % for the 7 models, ROC-AUC per unseen season vs the grid-only baseline, feature importance |
| Pattern mining (Dashboard 2) | All 1,393 association rules sorted by lift, filterable by outcome |
| Driver tiers (Dashboard 3) | 703 driver-seasons on the PCA map coloured by K-Means tier, tiers per season, the 6-algorithm clustering comparison |

The numbers come from the same module outputs as the Streamlit dashboards (40 of 68 winners picked, ROC-AUC 0.9629, silhouette 0.264).
To rebuild this folder after rerunning the modules: `.venv/bin/python powerbi/build_pbip.py`.
