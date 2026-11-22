# ApexIQ · End-Semester Jury Q&A Prep

Every number below comes from the module output files. Rerun them with `.venv/bin/python run_all_modules.py`.

## Headline numbers (memorise these)
| What | Number |
|---|---|
| Warehouse fact grain / rows | 1 driver × 1 Grand Prix · 8,650 rows (2004–2024) · 33 tables |
| Supervised dataset | 12,358 entries · 577 GPs · 1994–2024 · 16 pre-race features · 20.4 : 1 imbalance |
| Pattern mining | 24 items · 414 itemsets · 1,393 rules · Apriori 770 candidates / 5 scans vs FP-tree 4,230 nodes / 2 scans |
| Champion classifier (2022–2024 holdout) | ROC-AUC **0.9629** · PR-AUC **0.6433** · recall **85.3%** · winner picked **58.8% (40/68)** vs 51.5% pole baseline |
| Significance | Race-level bootstrap ΔAUC **+0.042**, 95% CI [+0.018, +0.073], p < 0.001 |
| Unsupervised dataset | 703 driver-seasons · 153 drivers · 9 features · no label |
| Clustering | K-Means k = 3 · silhouette **0.264** · Davies-Bouldin **1.276** · Calinski-Harabasz **347.5** · seed ARI **0.92** |
| Tiers | Title Contenders 108 · Midfield Regulars 325 · Backmarkers 270 · 81% of Contenders finished the championship top-3 |

---

## Your 60-second opening (say this before anything else)
"ApexIQ answers two questions about Formula 1 from 31 seasons of results.
**One:** before a race starts, who will win? **Two:** without being told, can we discover which drivers are title contenders, midfield or backmarkers?
**Dashboard 1** is the data warehouse: a star schema with one row per driver per race, plus a snowflake schema, built in SQLite and deployed to Snowflake in five layers.
**Dashboard 2** is supervised learning: 12,358 labelled entries, FP-Growth rules, seven classifiers compared on races the model never saw, and cost-sensitive XGBoost, which picks the winner in 40 of 68 races, better than always backing the pole-sitter.
**Dashboard 3** is unsupervised learning: 703 driver-season profiles, six clustering algorithms compared, and K-Means finds three tiers that match the real championship standings 81% of the time."

## Demo order (what to click, what to say)
| # | Open | Say |
|---|---|---|
| 1 | Project overview | The 60-second opening; point at 40/68 and 0.9629 |
| 2 | Warehouse Design → Star Schema, then Live OLAP Queries | Grain = driver × race; run roll-up, then slice/dice |
| 3 | Snowflake Deployment → Live Verification | "Live, snowpark": the counts come from Snowflake right now |
| 4 | Snowsight worksheet `SNOWFLAKE_DEMO_QUERIES.sql` (only if asked) | Queries 2–5: star join, ROLLUP, snowflake chain, QUALIFY |
| 5 | Dataset (Supervised) | 20:1 imbalance, chronological split |
| 6 | Pattern Mining | Same 414 itemsets from both algorithms; FP-tree stays at 4,230 nodes |
| 7 | Classifier Comparison | Switch metric to *Accuracy %*: the baseline scores 95% yet finds no winners. That is why we rank on ROC-AUC / PR-AUC / top-1 |
| 8 | Classification Algorithm → Curves & Threshold | Move the threshold slider: precision ↔ recall |
| 9 | Dataset (Unsupervised) → Clustering Comparison | Different grain; 6 algorithms; ranking rule |
| 10 | K-Means → Cluster Map, Centroid Profiles | Three tiers; radar = tier fingerprints |
| 11 | Clustering Performance Metrics → vs. Championship | External check: 81% of Contenders finished top-3 |

## Snowflake: how it is deployed now
**Q: Is this your own Snowflake account?**
Yes: account UKFIGDV-WD45232 (AWS ap-southeast-7). `deploy_to_snowflake.py` builds everything from `.env` credentials; `deploy_streamlit_app.py` uploads this dashboard into Snowflake.

**Q: What exactly is in Snowflake?**
- Database `F1_PREDICTION_DB` with schemas RAW → CLEAN → DW → ML → ANALYTICS: 26 tables and views, 39 objects defined in the master SQL.
- Row counts match the local files exactly: 8,650 results, 412 races, 1,393 rules, 414 itemsets, 7 models, 703 clustered driver-seasons.
- Warehouse `F1_WH` is X-Small and suspends after 60 seconds idle.

**Q: Why does the dashboard also run inside Snowflake?**
It is a native Streamlit-in-Snowflake app (`F1_RACE_INTELLIGENCE`). Inside Snowflake it uses the app's own Snowpark session, so no password is stored anywhere. It runs on the *warehouse runtime*, which installs packages from Snowflake's own Anaconda channel. The newer container runtime needs internet access to PyPI, which a trial account blocks.

**Q: ELT or ETL?**
Locally, ETL: Python cleans the data, then loads SQLite. In Snowflake, ELT: raw CSVs are loaded first (`PUT` + `COPY INTO` RAW), then transformed with SQL inside Snowflake (RAW → CLEAN → DW).

**Q: Why five schemas?**
Layered (medallion-style) design. RAW is untouched source data you can always rebuild from. CLEAN is typed and validated. DW holds the dimensional model. ML holds model outputs. ANALYTICS holds what users see (secure view, dynamic table). Each layer gets its own permissions.

**Q: What is a dynamic table?**
A table defined by a query that Snowflake keeps fresh automatically within a `TARGET_LAG` (ours: 1 hour, a rolling 5-race form per driver). It is suspended to save trial credits.

**Q: What is a secure view?**
A view whose definition is hidden from users, given to the read-only role `F1_ANALYST_READONLY`. Only public columns are exposed (no internal features).

## Power BI
**Q: What is the Power BI dashboard?**
`powerbi/ApexIQ_F1_Dashboard.pbip` holds 4 pages: Race predictor, Classifier comparison, Pattern mining and Driver tiers. Its data comes from the same module outputs as Streamlit (`F1_Race_Intelligence_PowerBI_Dataset.xlsx`, 18 sheets), so the numbers match: 40/68, 0.9629, 1,393 rules, silhouette 0.264.

**Q: Why both Streamlit and Power BI?**
Streamlit holds the full analysis and the live Snowflake queries. Power BI is the business-user view: drag-and-drop filters, no code, the tool most companies use.

## Basics they may test (one line each)
- **Data warehouse:** a subject-oriented, integrated, time-variant, non-volatile store for analysis (Inmon).
- **Fact vs. dimension:** facts are measurements (finish position, points); dimensions describe them (who, where, when).
- **OLAP operations:**
  - Roll-up: aggregate up a hierarchy (month → season).
  - Drill-down: the reverse.
  - Slice: fix one dimension (season = 2024).
  - Dice: fix several.
  - Pivot: rotate the axes.
- **Supervised vs. unsupervised:** with a label (who won) vs. without one (find the tiers).
- **XGBoost:** builds trees one after another, each one correcting the previous trees' errors, with regularisation.
- **K-Means:**
  1. Pick k centres.
  2. Assign each point to the nearest centre.
  3. Move each centre to the mean of its points.
  4. Repeat until nothing changes.
- **PCA:** projects the 9 features onto the 2 directions of largest variance, for plotting only. Clustering itself uses all 9.
- **ROC-AUC:** the probability that a random winner is ranked above a random non-winner.
- **PR-AUC:** the precision-recall area; its baseline equals the positive rate (0.05 here), so 0.64 is about 13× better than chance.
- **Recall:** of the real winners, how many we flagged.
- **Precision:** of the drivers we flagged, how many actually won.

---

## Dashboard 1: Data Warehouse

**Q: What is the grain of your fact table?**
One row per driver per Grand Prix. Every measure (grid, finish, points, pit stops, lap times) is additive or averageable at that level.

**Q: Star vs. snowflake schema: which do you use and why?**
Both. In the star schema the dimensions are denormalised, so every query needs only 1 join; we use it for dashboards and OLAP because latency is lowest. In the snowflake schema `DIM_RACE → DIM_CIRCUIT → DIM_COUNTRY` is normalised, which removes redundancy and update anomalies, at the cost of 2–3 joins per query.

**Q: Name your dimensions and one hierarchy.**
Driver, Constructor, Race (+ Circuit), Status, Date. The date hierarchy day → month → quarter → season is what we roll up along (OLAP query 1).

**Q: Show roll-up / drill-down / slice / dice.**
Warehouse Design page → Live OLAP Queries tab. Queries 1–5 run live against `f1_warehouse.db`.

**Q: What did you deploy on Snowflake?**
`deploy_to_snowflake.py` runs 7 steps from `MASTER_SNOWFLAKE_DEPLOYMENT.sql`:
1. Warehouse, database and stages.
2. Table DDLs.
3. `PUT` the files to the stage.
4. `COPY INTO` the RAW tables.
5. ELT into CLEAN.
6. Clone, Time Travel, dynamic table, stream + task, secure view and a Cortex procedure.

Step 6b builds the DW star and snowflake schemas and loads the clustering output. In total, 39 objects across 5 schemas.

**Q: Zero-copy clone vs. Time Travel?**
A clone creates a new table that shares the same micro-partitions, with no data copied (used for dev/test). Time Travel queries a table as it was in the past (`AT(OFFSET => -60)`), for recovery and auditing.

**Q: What does the stream + task do?**
The stream `RAW.STREAM_RACE_RESULTS_CDC` captures inserts into RAW race results (change data capture). The task `ML.TASK_AUTO_SCORE_F1_PREDICTIONS` is scheduled every 10 minutes and runs only `WHEN SYSTEM$STREAM_HAS_DATA(...)`, writing scores into `ML.AUTO_SCORED_WIN_PREDICTIONS`.
- **Be honest if asked:** the task scores with a simple pole-position rule, not the XGBoost model. It demonstrates the CDC pipeline. Putting XGBoost inside Snowflake would need a Snowpark Python UDF.
- **It is kept suspended** so it spends no trial credits. `SHOW TASKS` shows it; `ALTER TASK ... RESUME` would start it.

---

## Dashboard 2: Supervised Learning

**Q: What are your class labels?**
`target_is_win` (primary), podium, points and DNF. There is exactly one winner per GP and no missing labels.

**Q: How do you handle the 20 : 1 imbalance?**
Cost-sensitive XGBoost with `scale_pos_weight = 15`: a missed winner costs 15× more than a false alarm. We evaluate with PR-AUC, recall and race-level top-1, not accuracy.

**Q: Why is the baseline's accuracy 95% but it's still the worst model?**
It predicts "no win" for everyone, which gives 95% accuracy and 0% recall. Accuracy is meaningless at this level of imbalance.

**Q: How do you prevent data leakage?**
1. Every feature uses only past races (`shift(1)` before rolling windows).
2. The test set is strictly later in time (train ≤ 2021, test ≥ 2022), with an assertion in code.
3. No in-race data is used (pit strategy, safety cars, fastest laps).

**Q: Why not random k-fold cross-validation?**
Random folds would train on 2024 races to predict 2019 races, which leaks the future. We use a 6-fold expanding window instead: train 1994 → season−1, then test on that season.

**Q: Apriori vs. FP-Growth: how do they differ, and which is faster?**
- **Apriori** generates candidates level by level and needs k database scans (here 770 candidates over 5 scans).
- **FP-Growth** compresses the data into a prefix tree in 2 scans and mines it recursively, with no candidates.
- **Both find exactly the same 414 itemsets.** On our 24-item basket Apriori is faster at high support. As support drops, its candidates grow 11× while the tree stays at 4,230 nodes, and **at min_support = 0.005 FP-Growth overtakes it**.

**Q: Support, confidence, lift?**
- Support = P(X ∪ Y).
- Confidence = P(Y | X).
- Lift = confidence ÷ P(Y). Lift > 1 means positive association.

Example: {pole, podium} ⇒ winner has confidence 0.64 and lift 13.8.

**Q: Why XGBoost over Random Forest or LightGBM?**
It has the best ROC-AUC (0.9629), PR-AUC (0.6433) and top-1 hit rate (40/68). It is regularised second-order boosting with built-in class weighting. Random Forest has slightly higher recall but picks the winner in 5 fewer races.

**Q: What is the race softmax?**
Per-driver probabilities don't sum to 1, so we apply a softmax over log-probabilities within each race (T = 0.8). The probabilities then sum to exactly 1 and the argmax is the predicted winner.

**Q: Is the improvement statistically significant?**
Yes. A paired bootstrap that resamples the 68 races 1,000 times gives ΔAUC +0.042 with a 95% CI of [+0.018, +0.073], which excludes 0 (p < 0.001). The Wilcoxon test over 6 folds gives p = 0.078. That test has low power: its minimum possible p is 0.016, and the baseline legitimately wins 2019–20, when pole-sitters dominated.

**Q: Precision is only 32%. Is that bad?**
At a 0.5 threshold, about 2.6 genuine contenders per race get flagged, and only one can win. The softmax then picks one, which is why the top-1 hit rate (58.8%) is the business metric. The threshold slider on the Classification page shows the trade-off live.

**Q: Is the model overfitting?**
Not much. ROC-AUC is 0.973 on train, 0.961 on validation and 0.964 on test.

**Q: Where does it fail?**
- **2024 British GP:** it ranked pole-sitter Russell first. He retired with a water-system failure; Hamilton, ranked 2nd, won. Pre-race data cannot predict that.
- **Where it beats the pole heuristic:** 8 races, for example 2024 Canada, where Verstappen won from P2.
- **Where it loses to the pole heuristic:** 3 races.

---

## Dashboard 3: Unsupervised Learning

**Q: Why a separate dataset for clustering?**
Clustering needs unlabelled objects to group. We changed the grain to one row per driver-season: 703 profiles with 9 features and no target column.

**Q: Isn't using wins and podiums as features leakage?**
No. Clustering is descriptive, not predictive, so there is no future to leak. Leakage only matters when predicting; the link experiment below uses the *previous* season's tier for exactly that reason.

**Q: Why standardise?**
K-Means uses Euclidean distance. Without scaling, `starts` (≈17) would dominate `win_rate` (≈0.04).

**Q: How did you choose k = 3?**
- The elbow in inertia is at k = 3.
- k = 2 has a higher silhouette but only separates front-runners from everyone else.
- The Ward dendrogram's largest vertical gap also gives 3 clusters.

**Q: Compare your 6 algorithms.**
| Algorithm | How it works | How it did here |
|---|---|---|
| **K-Means** (centroid) | Minimises within-cluster squared distance | Best silhouette and Calinski-Harabasz, stable |
| **K-Medoids** (PAM) | Like K-Means, but every centre must be a real driver-season | Close second (silhouette 0.234), robust to outliers |
| **Ward** (hierarchical) | Merges the groups that add the least variance | Unstable, ARI 0.52 |
| **GMM** (probabilistic) | EM fits Gaussians with soft membership | Most stable, but its clusters overlap heavily |
| **BIRCH** (CF-tree) | Single-pass summarisation | Unstable, like Ward |
| **DBSCAN** (density) | Finds dense regions, no k needed | Labels 7.7% as noise and fails on varying density |

**Q: How did you choose eps for DBSCAN and k for GMM?**
DBSCAN: grid search, then checked on the k-distance curve (sorted distance to each point's 5th nearest neighbour); eps = 1.3 sits near the knee. GMM: BIC and AIC keep falling until k = 7 because full-covariance Gaussians always fit density better with more parts. That's a density answer, not a tier count, so we compare all algorithms at the elbow's k = 3.

**Q: Silhouette 0.26 seems low.**
Driver performance is a continuum, not separate islands, so touching clusters are expected. Only 2% of points have a negative silhouette, stability is high (ARI 0.92), and the external check is strong: 81% of Contenders finished the championship top-3, and no Backmarker ever did.

**Q: Silhouette vs. Davies-Bouldin vs. Calinski-Harabasz?**
- **Silhouette:** (b − a) / max(a, b) per point, range −1 to 1, higher is better.
- **Davies-Bouldin:** the mean worst ratio of scatter to centroid distance, lower is better.
- **Calinski-Harabasz:** between-cluster dispersion over within-cluster dispersion, higher is better.

**Q: What is ARI?**
The Adjusted Rand Index: pair-counting agreement between two labelings, corrected for chance. 1 means identical, 0 means random. We use it for stability (rerunning with new seeds or subsamples) and for the external check against championship standings.

**Q: Give a real insight from the clusters.**
Hamilton: Contender 2007–08, Midfield in 2009 (a bad McLaren), Contender 2010–22, then Midfield in 2023–24 (the Mercedes slump). The clusters detect car-competitiveness shifts without labels. The "Tiers by Era" chart shows how competitive each season was.

**Q: How are Dashboards 2 and 3 connected?**
We added each driver's previous-season tier (K-Means fitted on 1994–2021 only) as a classifier feature.
- **On top of grid position:** PR-AUC rises from 0.40 to 0.49, so the clusters carry real signal.
- **On top of all 16 features:** it is redundant, because rolling form already encodes it, so the champion leaves it out.

---

## Report & reproducibility
**Q: Can you reproduce a number live?**
Run `.venv/bin/python run_all_modules.py` (about 20 s), then refresh the dashboard. There are 64 automated tests: `.venv/bin/python -m unittest discover -s tests`.
