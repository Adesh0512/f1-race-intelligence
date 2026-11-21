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

Step 6b builds the DW star and snowflake schemas and loads the clustering output. In total, 40 objects across 5 schemas.

**Q: Zero-copy clone vs. Time Travel?**
A clone creates a new table that shares the same micro-partitions, with no data copied (used for dev/test). Time Travel queries a table as it was in the past (`AT(OFFSET => -60)`), for recovery and auditing.

**Q: What does the stream + task do?**
The stream captures inserts into RAW race results (change data capture). The scheduled task scores new rows into `ML.AUTO_SCORED_WIN_PREDICTIONS` only when the stream has data.

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
Run `.venv/bin/python run_all_modules.py` (about 20 s), then refresh the dashboard. There are 61 automated tests: `.venv/bin/python -m unittest discover -s tests`.
