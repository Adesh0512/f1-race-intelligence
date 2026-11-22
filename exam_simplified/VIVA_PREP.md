# ApexIQ — Viva and Jury Preparation

Everything here matches the real project's numbers. Read it aloud twice before the jury.

---

## 1. The 2–3 minute presentation (say this first)

> "Good morning. Our project is **ApexIQ: Formula 1 Race Intelligence using Data Warehousing and Data Mining**.
>
> Formula 1 has records of every race. We used 31 seasons, 1994 to 2024, to answer two questions. **One: before a race starts, who will win? Two: without being told, which drivers are title contenders, midfield or backmarkers?**
>
> **Dashboard 1 is the data warehouse.** We built a star schema where one row means one driver in one Grand Prix: 8,650 results with dimensions for driver, team, race and date. We also built a normalised snowflake schema and ran OLAP queries: roll-up, drill-down, slice, dice and pivot. Then we deployed it to Snowflake in five layers, RAW, CLEAN, DW, ML and ANALYTICS, using cloning, Time Travel, a stream and task, a dynamic table and a secure view.
>
> **Dashboard 2 is supervised learning.** We have 12,358 labelled entries with 16 features that are all known before the race. Winners are only 1 in 21 entries, so accuracy is misleading. With FP-Growth and Apriori we found 1,393 rules; for example, starting on pole and reaching the podium makes a win about 14 times more likely. We compared seven classifiers on the 2022 to 2024 seasons, which they never saw. Cost-sensitive XGBoost won: it picks the winner in **40 of 68 races**, against 35 for always backing the pole-sitter, with a ROC-AUC of 0.96.
>
> **Dashboard 3 is unsupervised learning.** We summarised 703 driver seasons and compared six clustering algorithms. K-Means found three tiers by itself, and 81% of its Title Contenders really finished in the top three of the championship.
>
> Finally, a prediction must be about the future. Our data runs to the Las Vegas Grand Prix, so we forecast the **next race, Qatar on 29 November 2026**: Antonelli is favourite at about 30%. In the dashboard you can change the pole-sitter or a driver's form and the forecast updates instantly. Thank you."

---

## 2. Who explains what (suggested split)

| Adesh Patankar | Dhruv Sakhare |
|---|---|
| Opening pitch (section 1) | Dataset, class labels and imbalance (folder 03) |
| Data warehouse: star and snowflake schema, OLAP (folder 01) | Pattern mining: Apriori vs FP-Growth (folder 04) |
| Snowflake deployment (folder 02) | Clustering: 6 algorithms and K-Means tiers (folder 07) |
| Classifier comparison and champion XGBoost (folders 05, 06) | Dashboard demo and Power BI (folder 09) |
| Next-race forecast (folder 08) | Limitations and future work |

Both should know the five numbers in section 6. If a question is about the other person's part, say "my teammate worked closely on that" and let them answer.

---

## 3. Important concepts in plain language

| Concept | Simple meaning |
|---|---|
| Data warehouse | A database built for analysis, not daily transactions. It keeps history and is read far more than written. |
| Fact table | The numbers we measure: grid slot, finish, points. |
| Dimension table | The descriptions: which driver, which team, which race, which date. |
| Grain | What one row of the fact table means. Ours: one driver in one Grand Prix. |
| Star schema | Fact table in the middle, every dimension joined to it directly. Fast. |
| Snowflake schema | Dimensions split further (race → circuit → country). Less repetition, more joins. |
| OLAP | Looking at the data from many angles: roll-up, drill-down, slice, dice, pivot. |
| ETL / ELT | Clean then load (ETL, local) or load then clean inside the warehouse (ELT, Snowflake). |
| Class label | The answer the model learns: did this driver win (1) or not (0)? |
| Feature | An input the model uses, like grid slot or recent form. |
| Data leakage | Accidentally giving the model information from the future. We prevent it. |
| Class imbalance | One answer is much rarer: 1 winner per 21 entries. |
| Support / confidence / lift | How often items appear together / how often the rule is right / how much more likely than normal. |
| Classification | Predicting a category (winner or not). Supervised: learns from labelled examples. |
| Clustering | Grouping similar items without labels. Unsupervised. |
| Decision tree | A flowchart of yes/no questions. |
| Boosting (XGBoost) | Many small trees; each new tree fixes the mistakes of the previous ones. |
| Cost-sensitive learning | Making some mistakes count more: a missed winner costs 15 times more. |
| Softmax | Turns scores into percentages that add up to 100% for each race. |
| ROC-AUC | The chance a real winner is ranked above a non-winner. 0.5 = guessing, 1 = perfect. |
| PR-AUC | Precision vs recall area; the honest metric for rare classes. Guessing = 0.05 here. |
| Precision / recall | Of the drivers we flagged, how many won / of the real winners, how many we flagged. |
| Confusion matrix | A 2×2 table of correct and wrong predictions. |
| K-Means | Choose k centres, assign each point to the nearest, move centres to the average, repeat. |
| Standardisation | Putting all features on the same scale, so no feature dominates the distance. |
| Silhouette | How well each point fits its own cluster compared with the next one (−1 to 1). |
| ARI | How similar two groupings are; 1 = the same, 0 = random. |

---

## 4. Thirty likely viva questions with answers

**Data warehouse**

1. **What is a data warehouse?**
   A subject-oriented, integrated, time-variant, non-volatile store of data for analysis (Inmon's definition). Ours is about Formula 1 results.
2. **What is the grain of your fact table?**
   One driver in one Grand Prix: 8,650 rows for 2004–2024.
3. **Name your dimensions.**
   Driver, constructor (team), race (with circuit), date, status, session and tyre compound: seven in the real warehouse.
4. **Why both star and snowflake schemas?**
   The star schema is fast (one join per dimension), so the dashboards use it. The snowflake schema normalises race → circuit → country to remove repetition. We show both and compare them.
5. **Explain roll-up and drill-down with your data.**
   Roll-up adds race results up to seasons (wins per team per season). Drill-down goes the other way, from a season to its quarters or races.
6. **Slice vs dice?**
   Slice fixes one dimension (only races in Italy). Dice fixes several (seasons 2021–2024 and grid slots 1–3).

**Snowflake**

7. **Why five schemas?**
   Each layer has one job: RAW keeps the original files so we can always rebuild, CLEAN is checked, DW is the dimensional model, ML holds model outputs and ANALYTICS is what users see. Each layer can have its own permissions.
8. **ETL or ELT?**
   Locally ETL (Python cleans, then loads SQLite). In Snowflake ELT: PUT and COPY INTO load the raw files, then SQL transforms them inside Snowflake.
9. **What are a zero-copy clone and Time Travel?**
   A clone is an instant copy sharing the same storage, for testing. Time Travel reads a table as it was earlier, for recovery and auditing.
10. **What do the stream and task do?**
    The stream records new race results; the task runs only when the stream has data and scores them. It is kept suspended to save trial credits, and it uses a simple pole rule rather than XGBoost.
11. **How is the password protected?**
    It is read from a local .env file that is never uploaded to GitHub. Inside Snowflake the dashboard uses Snowflake's own session, so no password is stored at all.

**Dataset and pattern mining**

12. **What are your class labels?**
    target_is_win (main), plus podium, points finish and DNF. Every race has exactly one winner and no label is missing.
13. **How do you prevent data leakage?**
    Every feature uses only earlier races (shifted by one race); we train on 1994–2021 and test on later seasons; no in-race data such as pit stops or safety cars is used.
14. **Why not use a random train/test split?**
    It would train on later races and test on earlier ones, learning from the future. A time split matches real use.
15. **Explain support, confidence and lift with an example.**
    For {pole, podium} ⇒ winner: support 0.022 (2.2% of all entries have all three), confidence 0.64 (64% of pole-sitters on the podium won) and lift 13.8 (13.8 times more likely than the usual 4.7% win rate).
16. **Apriori vs FP-Growth: which is better?**
    They find the same 414 itemsets. Apriori makes candidates and scans the data 5 times (770 candidates); FP-Growth builds a tree in 2 scans (4,230 nodes). On our small data Apriori is faster at high support, but FP-Growth wins at low support (0.005), where Apriori's candidates explode.
17. **Why min_support 0.02 and min_confidence 0.25?**
    0.02 keeps patterns that occur at least about 250 times, enough to trust; lower values flood us with rare patterns. 0.25 keeps rules that are right at least a quarter of the time, which is useful for a rare outcome like winning.

**Classification**

18. **Why is accuracy not your main metric?**
    A model that says "nobody wins" is 95% accurate and useless. We use ROC-AUC, PR-AUC, recall and winners picked.
19. **Why did you choose XGBoost?**
    It had the best ROC-AUC (0.9629), PR-AUC (0.6433) and winners picked (40 of 68) of the seven models, and it supports class weighting.
20. **What does scale_pos_weight = 15 mean?**
    Each winner counts 15 times more in training, so the model does not ignore the rare winners. The data has about 20 non-winners per winner.
21. **What is the race softmax and why T = 0.8?**
    It converts every driver's score into a percentage so that one race adds up to 100%; the highest is the predicted winner. A temperature below 1 makes the favourite stand out a little more.
22. **Is the improvement over the baseline significant?**
    Yes. Resampling the 68 races 1,000 times gives a ROC-AUC gain of +0.042 with a 95% interval of [+0.018, +0.073], which does not include zero.
23. **Is the model overfitting?**
    No. ROC-AUC is 0.973 on training, 0.961 on validation and 0.964 on test: very close.
24. **Precision is only 0.32. Is that bad?**
    At a 0.5 threshold about 2.6 contenders per race are flagged and only one can win. The softmax picks one per race, which is right 58.8% of the time.
25. **Which feature matters most?**
    Grid position (47.5% of the importance), then the driver's average finish in his last 5 races (10%).
26. **Give an example of a wrong prediction.**
    2024 British GP: the model picked pole-sitter Russell, who retired with a water-system failure; Hamilton, ranked second, won. Pre-race data cannot predict failures.

**Clustering**

27. **Why a separate dataset for clustering?**
    Clustering groups objects without labels. We changed the grain to one driver per season: 703 profiles with 9 features and no target column.
28. **Why standardise the features?**
    K-Means uses distance. Without scaling, starts (about 17) would outweigh win rate (about 0.04).
29. **How did you choose k = 3?**
    The elbow of the inertia curve is at k = 3, and the largest gap in the Ward dendrogram also gives 3. k = 2 only separates front-runners from everyone else.
30. **How do you know the clusters are meaningful?**
    The championship was never used to make them, yet 81% of Title Contender seasons finished in the top 3 and no Backmarker season did. They are also stable: ARI about 0.92 across reruns.

**Forecast and dashboards**

31. **How do you predict a race that has not happened?**
    We add the 2025–2026 results up to Las Vegas, rebuild the 16 features for every driver from races before the race date, and score them with the champion model. Qatar 2026: Antonelli 29.9%, Norris 24.6%, Verstappen 23.8%.
32. **How good is it on real new races?**
    On the 45 races of 2025–2026 it called 29 winners; backing the pole-sitter called 31. The 2026 rule change made older form less useful. We report this honestly.
33. **Why does Power BI use precomputed scenarios?**
    Power BI cannot run a Python model, so we computed every race × pole-sitter combination (44 scenarios). Streamlit runs the model live.

---

## 5. Demonstration sequence (what to open, in order)

| # | Open | Say / show |
|---|---|---|
| 1 | Streamlit → **Project overview** | The opening pitch; point at 40/68 and 0.9629 |
| 2 | **Warehouse Design** → Star Schema, then Live OLAP Queries | Grain; run a roll-up, then slice/dice |
| 3 | **Snowflake Deployment** (or Snowsight) | Live account, 5 schemas, 42 objects |
| 4 | **Dataset (Supervised)** → Class Labels | 20.42 : 1 imbalance, time split |
| 5 | **Pattern Mining** → Algorithm Comparison, Outcome Rules | Same 414 itemsets; pole + podium ⇒ win |
| 6 | **Classifier Comparison** | Switch to accuracy to show why it misleads; XGBoost wins |
| 7 | **Classification Algorithm** → Curves & Threshold | Move the threshold: precision vs recall |
| 8 | **Race Predictor** | Qatar 2026 forecast; set Verstappen on pole and watch it update |
| 9 | **Clustering Comparison**, then **K-Means** | 6 algorithms; 3 tiers |
| 10 | **Clustering Performance Metrics** → vs. Championship | 81% of Contenders finished top 3 |
| 11 | Power BI → **2. Race predictor** | Slicers for race and pole-sitter |
| 12 | Only if asked for code: `exam_simplified/06_champion_model/xgboost_champion.py` | Run it; it prints 40 of 68 and 0.9629 |

To run the simplified code during the viva:

```bash
.venv/bin/python exam_simplified/06_champion_model/xgboost_champion.py
```

---

## 6. Five numbers to remember

1. **40 / 68** winners picked on unseen races (pole-sitter: 35)
2. **0.9629** ROC-AUC, **0.6433** PR-AUC
3. **414** itemsets, **1,393** rules, same from both algorithms
4. **3 tiers**, silhouette **0.264**, **81%** of Contenders in the top 3
5. Next race: **Qatar 2026, Antonelli 29.9%**
