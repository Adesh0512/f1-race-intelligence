"""Text of the ApexIQ project report. Every number comes from the module output files (see the README of each module).

Blocks: ("h2"|"h3", title), ("p", text), ("def", term, text), ("bullets", [texts]), ("eq", key, formula),
("table", key, caption, headers, rows, widths), ("fig", key, image, caption, width_in).
Text may use **bold**, [@ref] citations and {tab:key} / {fig:key} / {eq:key} cross-references.
"""

TITLE = "ApexIQ: Formula 1 Race Intelligence Using Data Warehousing and Data Mining"
GUIDE = "Dr. Reena Pagare"

FRONT = {
    "title": TITLE,
    "guide": GUIDE,
    "examiner": (f"The project report entitled “{TITLE}” submitted by Adesh Patankar (ADT24SOCB0049) and Dhruv Sakhare "
                 "(ADT24SOCB0369) in partial fulfillment for the award of the degree of Bachelor of Technology (Computer Science & "
                 "Engineering (Big Data and Cloud Engineering)) during the academic year 2026-27, of MIT-ADT University, MIT School of "
                 "Computing, Pune, is hereby approved."),
    "acknowledgement": (f"We express our sincere gratitude to our project guide, **{GUIDE}**, for constant guidance, encouragement and "
                        "valuable suggestions throughout this project. The guidance to test every model on seasons it had never seen, and "
                        "to compare it honestly with the simplest possible rule, shaped both ApexIQ and this report. The reviews at every "
                        "stage helped us turn a dataset into a working data warehouse, a set of data-mining models and dashboards that "
                        "anyone can use."),
    "abstract": [
        "Formula 1 keeps consistent records of every race, yet two questions are still answered mostly by intuition before each "
        "Grand Prix: who is likely to win, and which drivers are genuinely competitive once the quality of their car is taken into "
        "account. This project presents **ApexIQ**, an end-to-end data warehousing and data mining system built on 31 seasons "
        "(1994–2024) of Grand Prix results from the f1.zip dataset, extended with 2025–2026 results from the public Jolpica-F1 API "
        "so that it can forecast races that have not yet been run.",
        "ApexIQ has three parts. A data warehouse models each driver's result in each Grand Prix as a star schema (a fact table of "
        "8,650 results for 2004–2024 and seven dimensions) and as a normalised snowflake schema, answers 12 OLAP queries, and is "
        "deployed to Snowflake in five layers (RAW, CLEAN, DW, ML and ANALYTICS; 42 objects) with cloning, Time Travel, a stream "
        "and task, a secure view and a dynamic table. A supervised pipeline builds 12,358 labelled driver-race entries with 16 "
        "strictly pre-race features, mines 1,393 association rules with FP-Growth and Apriori, which find the same 414 frequent "
        "itemsets, and compares seven classifiers on the 2022–2024 seasons that no model saw in training. A cost-sensitive XGBoost "
        "classifier with a race-level softmax reaches a ROC-AUC of 0.9629 and a PR-AUC of 0.6433, and names the winner in 40 of 68 "
        "races (58.8%) against 35 (51.5%) for always backing the pole-sitter; a race-level bootstrap confirms the gain (ΔAUC +0.042, "
        "95% CI [+0.018, +0.073]). An unsupervised pipeline groups 703 driver-season profiles with six clustering algorithms; "
        "K-Means with k = 3 (silhouette 0.264, seed-stability ARI 0.92) finds Title Contenders, Midfield Regulars and Backmarkers, "
        "and 81% of Title Contender seasons ended in the championship top three.",
        "The champion model is retrained on every race up to the 2026 Las Vegas Grand Prix and forecasts the next one, the 2026 "
        "Qatar Grand Prix, with Andrea Kimi Antonelli as favourite at 29.9%. In a real-world test on the 45 races of 2025–2026, "
        "which the model never saw, it called 29 winners against 31 for the pole-sitter, a result we report and discuss. All "
        "results are presented in a Streamlit dashboard that also runs natively inside Snowflake, where a user can change the race "
        "parameters and see the forecast update instantly, and in a 13-page Power BI report. The system is verified by 70 "
        "automated tests.",
    ],
}

BIB = {
    "inmon": "W. H. Inmon, Building the Data Warehouse, 4th ed. Indianapolis, IN, USA: Wiley, 2005.",
    "kimball": "R. Kimball and M. Ross, The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling, 3rd ed. Indianapolis, IN, USA: Wiley, 2013.",
    "han": "J. Han, M. Kamber, and J. Pei, Data Mining: Concepts and Techniques, 3rd ed. Waltham, MA, USA: Morgan Kaufmann, 2011.",
    "snowflake": "B. Dageville et al., “The Snowflake elastic data warehouse,” in Proc. ACM SIGMOD Int. Conf. Management of Data, San Francisco, CA, USA, 2016, pp. 215–226.",
    "ergast": "Jolpica-F1, “Jolpica F1 API: an open continuation of the Ergast Developer API.” [Online]. Available: https://github.com/jolpica/jolpica-f1 (accessed Nov. 2026).",
    "bunker": "R. P. Bunker and F. Thabtah, “A machine learning framework for sport result prediction,” Applied Computing and Informatics, vol. 15, no. 1, pp. 27–33, 2019.",
    "chaudhuri": "S. Chaudhuri and U. Dayal, “An overview of data warehousing and OLAP technology,” ACM SIGMOD Record, vol. 26, no. 1, pp. 65–74, 1997.",
    "agrawal": "R. Agrawal and R. Srikant, “Fast algorithms for mining association rules,” in Proc. 20th Int. Conf. Very Large Data Bases (VLDB), Santiago, Chile, 1994, pp. 487–499.",
    "he": "H. He and E. A. Garcia, “Learning from imbalanced data,” IEEE Trans. Knowledge and Data Engineering, vol. 21, no. 9, pp. 1263–1284, 2009.",
    "friedman": "J. H. Friedman, “Greedy function approximation: A gradient boosting machine,” Annals of Statistics, vol. 29, no. 5, pp. 1189–1232, 2001.",
    "xgboost": "T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, San Francisco, CA, USA, 2016, pp. 785–794.",
    "saito": "T. Saito and M. Rehmsmeier, “The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets,” PLoS ONE, vol. 10, no. 3, e0118432, 2015.",
    "rousseeuw": "P. J. Rousseeuw, “Silhouettes: A graphical aid to the interpretation and validation of cluster analysis,” J. Computational and Applied Mathematics, vol. 20, pp. 53–65, 1987.",
    "db": "D. L. Davies and D. W. Bouldin, “A cluster separation measure,” IEEE Trans. Pattern Analysis and Machine Intelligence, vol. PAMI-1, no. 2, pp. 224–227, 1979.",
    "ch": "T. Caliński and J. Harabasz, “A dendrite method for cluster analysis,” Communications in Statistics, vol. 3, no. 1, pp. 1–27, 1974.",
    "ari": "L. Hubert and P. Arabie, “Comparing partitions,” J. Classification, vol. 2, no. 1, pp. 193–218, 1985.",
    "sklearn": "F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” J. Machine Learning Research, vol. 12, pp. 2825–2830, 2011.",
    "lightgbm": "G. Ke et al., “LightGBM: A highly efficient gradient boosting decision tree,” in Advances in Neural Information Processing Systems 30, Long Beach, CA, USA, 2017, pp. 3146–3154.",
    "fpgrowth": "J. Han, J. Pei, and Y. Yin, “Mining frequent patterns without candidate generation,” in Proc. ACM SIGMOD Int. Conf. Management of Data, Dallas, TX, USA, 2000, pp. 1–12.",
    "elkan": "C. Elkan, “The foundations of cost-sensitive learning,” in Proc. 17th Int. Joint Conf. Artificial Intelligence (IJCAI), Seattle, WA, USA, 2001, pp. 973–978.",
    "guo": "C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On calibration of modern neural networks,” in Proc. 34th Int. Conf. Machine Learning (ICML), Sydney, Australia, 2017, pp. 1321–1330.",
    "bergmeir": "C. Bergmeir and J. M. Benítez, “On the use of cross-validation for time series predictor evaluation,” Information Sciences, vol. 191, pp. 192–213, 2012.",
    "efron": "B. Efron and R. J. Tibshirani, An Introduction to the Bootstrap. New York, NY, USA: Chapman & Hall, 1993.",
    "wilcoxon": "F. Wilcoxon, “Individual comparisons by ranking methods,” Biometrics Bulletin, vol. 1, no. 6, pp. 80–83, 1945.",
    "macqueen": "J. MacQueen, “Some methods for classification and analysis of multivariate observations,” in Proc. 5th Berkeley Symp. Mathematical Statistics and Probability, vol. 1, 1967, pp. 281–297.",
    "kaufman": "L. Kaufman and P. J. Rousseeuw, Finding Groups in Data: An Introduction to Cluster Analysis. New York, NY, USA: Wiley, 1990.",
    "ward": "J. H. Ward, “Hierarchical grouping to optimize an objective function,” J. American Statistical Association, vol. 58, no. 301, pp. 236–244, 1963.",
    "dempster": "A. P. Dempster, N. M. Laird, and D. B. Rubin, “Maximum likelihood from incomplete data via the EM algorithm,” J. Royal Statistical Society: Series B, vol. 39, no. 1, pp. 1–38, 1977.",
    "birch": "T. Zhang, R. Ramakrishnan, and M. Livny, “BIRCH: An efficient data clustering method for very large databases,” in Proc. ACM SIGMOD Int. Conf. Management of Data, Montreal, Canada, 1996, pp. 103–114.",
    "dbscan": "M. Ester, H.-P. Kriegel, J. Sander, and X. Xu, “A density-based algorithm for discovering clusters in large spatial databases with noise,” in Proc. 2nd Int. Conf. Knowledge Discovery and Data Mining (KDD), Portland, OR, USA, 1996, pp. 226–231.",
    "gray": "J. Gray et al., “Data cube: A relational aggregation operator generalizing group-by, cross-tab, and sub-totals,” Data Mining and Knowledge Discovery, vol. 1, no. 1, pp. 29–53, 1997.",
    "tan": "P.-N. Tan, V. Kumar, and J. Srivastava, “Selecting the right objective measure for association analysis,” Information Systems, vol. 29, no. 4, pp. 293–313, 2004.",
    "breiman": "L. Breiman, “Random forests,” Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
    "sis": "Snowflake Inc., “About Streamlit in Snowflake,” Snowflake Documentation. [Online]. Available: https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit (accessed Nov. 2026).",
}

CH1 = ("1.  INTRODUCTION", [
    ("h2", "1.1  INTRODUCTION"),
    ("p", "Formula 1 is one of the most data-intensive sports in the world. Every Grand Prix produces a starting grid decided in "
          "qualifying, a finishing order, points, retirements, pit stops and lap times, and the sport's results have been recorded "
          "consistently since 1950 [@ergast]. For teams, broadcasters, fantasy-league players and fans the same two questions come up "
          "before every race: who is most likely to win, and which drivers are genuinely competitive once the quality of their car "
          "is taken into account."),
    ("p", "Answering these questions well needs two things that are usually built separately. The first is a well-designed store "
          "of historical data that can be queried quickly from many angles: by driver, team, circuit, season or era. This is the "
          "classic job of a data warehouse [@inmon, @kimball]. The second is a set of data-mining models that turn the stored history "
          "into patterns, predictions and groupings [@han]."),
    ("p", "This project builds **ApexIQ**, a system that joins both. It loads 31 seasons of results into a dimensional data "
          "warehouse, deploys it to the Snowflake cloud data platform [@snowflake], mines association rules between pre-race "
          "conditions and race outcomes, trains and compares classifiers that predict the winner before the start, groups driver "
          "seasons into performance tiers without labels, and forecasts the next Grand Prix. All results are presented in "
          "interactive dashboards built with Streamlit and Power BI."),
    ("h3", "1.1.1  Formula 1 as a Data Problem"),
    ("p", "Race data has a natural dimensional structure. A result is a measurable fact (grid slot, finishing position, points) "
          "recorded for a driver, driving for a constructor, at a race held at a circuit in a country on a date. This makes it a good "
          "fit for a star schema whose grain is one driver in one Grand Prix. The data also changes over time in ways that matter: "
          "regulations, car designs and points systems change between eras, so any model must be tested on seasons that come after "
          "the ones it learned from."),
    ("h3", "1.1.2  Why Predicting the Winner Is Difficult"),
    ("p", "Only one of about twenty drivers wins each race, so winners make up under 5% of all entries, an imbalance of 20.4 to 1. "
          "A model that always predicts “no win” is 95% accurate and of no use. Much of what decides a race also happens after the "
          "start: retirements, safety cars, strategy and weather. A pre-race model can only use what is known before the lights go "
          "out, so its job is to rank the drivers well, not to be certain. Qualifying position alone is a strong signal, so every "
          "model must be compared honestly with the simple rule of backing the pole-sitter."),
    ("h2", "1.2  EXISTING WORK"),
    ("p", "Several tools and studies address parts of this problem. Table {tab:existing} summarises the most relevant ones and the "
          "gaps that motivated ApexIQ."),
    ("table", "existing", "Comparison of existing tools and studies", ["System", "What it does", "Limitations"], [
        ["Official timing apps and broadcast graphics", "Live timing, lap charts and simple statistics", "No historical warehouse for analysis; no predictive model"],
        ["Ergast / Jolpica-F1 API [@ergast]", "Open historical results since 1950", "Raw tables only; no dimensional model, mining or prediction"],
        ["Betting-market odds", "Implied win probability per race", "Commercial and opaque; includes the bookmaker's margin; not explainable"],
        ["Fan analytics sites and notebooks", "Charts of driver and team statistics", "Mostly descriptive; models rarely validated on later seasons"],
        ["Academic sports-prediction studies [@bunker]", "Machine-learning models of match and race outcomes", "Often evaluated on random splits; rarely delivered as usable tools"],
    ], [3, 3, 4]),
    ("h2", "1.3  MOTIVATION"),
    ("p", "As students of Data Warehousing and Data Mining, we wanted a project in which every topic of the course does real work "
          "on one dataset: dimensional modelling and OLAP, a cloud data warehouse, frequent-pattern mining, classification and "
          "clustering. Formula 1 offered a public, well-documented dataset with a clear grain, a hard prediction problem and an "
          "audience that cares about the answer."),
    ("p", "A second motivation was honest evaluation. Many published predictions are tested on randomly chosen races, which lets a "
          "model learn from the future. We set three rules from the start: every feature must be known before the race, every model "
          "is judged on later seasons it never saw, and every model is compared with the pole-sitter. These rules shaped many of the "
          "design decisions described in this report."),
    ("h2", "1.4  OBJECTIVES"),
    ("bullets", [
        "To design a dimensional data warehouse (star and snowflake schemas) for Formula 1 results and support OLAP operations on it.",
        "To deploy the warehouse to Snowflake in layered schemas and use its cloud features: stages, bulk loading, zero-copy cloning, Time Travel, streams and tasks, secure views and dynamic tables.",
        "To build a leakage-free supervised dataset with clearly defined class labels and pre-race features.",
        "To mine association rules between pre-race conditions and race outcomes, and compare Apriori with FP-Growth.",
        "To compare several classification algorithms on unseen seasons, then select and tune a champion model that predicts the race winner.",
        "To discover driver performance tiers without labels by comparing clustering algorithms and validating the chosen one.",
        "To forecast the next Grand Prix from all results up to the latest race, and test the model on races run after it was trained.",
        "To present the results in interactive dashboards (Streamlit, Streamlit in Snowflake and Power BI) and verify the system with automated tests.",
    ]),
    ("h2", "1.5  SCOPE"),
    ("p", "**In scope.** Formula 1 results from 1994 to 2024 from the f1.zip dataset, extended with 2025–2026 results for "
          "forecasting; a local SQLite data warehouse and its Snowflake deployment; association-rule mining; seven classifiers and "
          "six clustering algorithms; a next-race forecaster with adjustable race parameters; and dashboards for analysts and "
          "examiners."),
    ("p", "**Out of scope.** Live in-race prediction (lap-by-lap telemetry, pit strategy, weather and safety cars), betting or any "
          "financial use, and certainty about results. The model ranks drivers by their chance of winning; it cannot know the result "
          "in advance."),
])

CH2 = ("2.  CONCEPTS AND METHODS", [
    ("h2", "2.1  DEFINITIONS"),
    ("def", "Data warehouse", "a subject-oriented, integrated, time-variant and non-volatile collection of data that supports analysis and decision making [@inmon]."),
    ("def", "Fact and dimension", "a fact table stores measurements at a declared grain; dimension tables describe the who, what, where and when of each fact [@kimball]."),
    ("def", "Star and snowflake schema", "in a star schema each dimension is one denormalised table joined directly to the fact table; in a snowflake schema dimensions are normalised into chains such as race → circuit → country."),
    ("def", "OLAP", "online analytical processing: queries that roll up, drill down, slice, dice and pivot multidimensional data [@chaudhuri, @gray]."),
    ("def", "ETL and ELT", "extract-transform-load cleans the data before loading it; extract-load-transform loads raw data first and transforms it inside the warehouse."),
    ("def", "Frequent itemset and association rule", "a set of items that occurs together in at least a minimum share of transactions, and an implication X ⇒ Y between such sets [@agrawal]."),
    ("def", "Support, confidence and lift", "the share of transactions that contain both X and Y; the share of transactions containing X that also contain Y; and confidence divided by the support of Y, where a lift above 1 means a positive association [@tan]."),
    ("def", "Class imbalance", "a dataset in which one class is much rarer than the other; here about 1 entry in 21 is a winner [@he]."),
    ("def", "Gradient boosting and XGBoost", "an ensemble that adds decision trees one at a time, each correcting the errors of the trees before it; XGBoost adds second-order optimisation and regularisation [@friedman, @xgboost]."),
    ("def", "ROC-AUC and PR-AUC", "the probability that a random winner is ranked above a random non-winner, and the area under the precision-recall curve, which is more informative when the positive class is rare [@saito]."),
    ("def", "Clustering", "grouping objects so that members of a group are more similar to each other than to members of other groups, without using labels [@han]."),
    ("def", "Silhouette, Davies-Bouldin and Calinski-Harabasz", "internal measures of cluster quality based on how compact the clusters are and how well they are separated [@rousseeuw, @db, @ch]."),
    ("def", "Adjusted Rand Index (ARI)", "the agreement between two groupings corrected for chance: 1 means identical and 0 means no better than random [@ari]."),
    ("h2", "2.2  TECHNOLOGY STACK"),
    ("p", "ApexIQ is built in Python. Table {tab:stack} lists the main technologies and why each was chosen."),
    ("table", "stack", "Technology stack", ["Layer", "Technology", "Purpose"], [
        ["Local data warehouse", "SQLite, pandas, NumPy", "Star and snowflake schemas, ETL and OLAP queries"],
        ["Cloud data warehouse", "Snowflake (X-Small warehouse), Snowflake Connector for Python", "Layered deployment from RAW to ANALYTICS and the platform's cloud features"],
        ["Pattern mining", "mlxtend (Apriori, FP-Growth)", "Frequent itemsets and association rules"],
        ["Machine learning", "scikit-learn [@sklearn], XGBoost [@xgboost], LightGBM [@lightgbm]", "Classifiers, clustering algorithms and metrics"],
        ["Dashboards", "Streamlit, Plotly, Streamlit in Snowflake [@sis]", "Interactive pages, run locally and inside Snowflake"],
        ["Business intelligence", "Power BI Desktop (PBIP project, TMDL model)", "Report with KPI cards, slicers and synced filters"],
        ["External data", "Jolpica-F1 REST API [@ergast]", "Race results after 2024 for the forecaster"],
        ["Testing", "Python unittest, Streamlit AppTest", "70 automated tests"],
    ], [2.2, 3.6, 4.2]),
    ("h2", "2.3  DATA WAREHOUSE DESIGN"),
    ("h3", "2.3.1  Grain and Fact Tables"),
    ("p", "The grain of the main fact table is **one driver in one Grand Prix**. FACT_RACE_RESULTS holds 8,650 results for the "
          "2004–2024 seasons with additive or averageable measures: grid position, finishing position, points, laps completed, "
          "pit stops and fastest-lap time. A second fact table, FACT_LAP_TIMES, stores 296,727 individual laps at the grain of one "
          "driver on one lap of one race. Together with the dimensions and supporting tables, the local warehouse has 33 tables."),
    ("h3", "2.3.2  Dimensions and Hierarchies"),
    ("p", "Seven dimensions describe each result: DIM_DRIVER (108 drivers), DIM_CONSTRUCTOR (35 teams), DIM_RACE (412 races), "
          "DIM_DATE, DIM_STATUS (91 finishing states such as Finished, +1 Lap or Engine), DIM_SESSION and DIM_TYRE_COMPOUND. The date "
          "dimension carries the hierarchy day → month → quarter → season, which is the path the roll-up and drill-down queries "
          "follow."),
    ("h3", "2.3.3  Star and Snowflake Schemas"),
    ("p", "The star schema in Figure {fig:star} joins every dimension directly to the fact table, so each analytical query needs "
          "only one join per dimension; it serves the dashboards and OLAP queries. The snowflake schema in Figure {fig:snow} "
          "normalises the race dimension into the chain race → circuit → country (30 countries) and splits out nationality, engine "
          "supplier and other attributes. This removes redundancy and update anomalies at the cost of two or three extra joins."),
    ("fig", "star", "shots/s02_star.png", "Star schema: fact tables with their dimensions", 4.6, (590, 2260)),
    ("fig", "snow", "shots/s03_snowflake_schema.png", "Snowflake schema: normalised dimension chains", 6.0, (590, 780)),
    ("h3", "2.3.4  OLAP Operations"),
    ("p", "Twelve OLAP queries run live against the warehouse. The first five cover the classic operations: **roll-up** of "
          "points, podiums and wins along race → month → quarter → season; **drill-down** from a constructor's season to circuits "
          "and then to each driver's share; **slice** to the European historic circuits; **dice** on the 2021–2024 seasons, the top "
          "four constructors and top-three starts; and **pivot** of constructors against championship eras. The others use window "
          "ranking for the standings, pit-stop strategy, pole-to-win conversion, retirement reliability and altitude. Equivalent "
          "queries are available as read-only worksheets in Snowflake."),
    ("h2", "2.4  SNOWFLAKE CLOUD DEPLOYMENT"),
    ("p", "The warehouse is deployed to Snowflake [@snowflake] in the database F1_PREDICTION_DB, organised as the five layers in "
          "Figure {fig:pipeline}. RAW holds the source files exactly as delivered, CLEAN holds typed and validated tables, DW holds "
          "the star and snowflake schemas, ML holds features, model outputs and forecasts, and ANALYTICS holds what users see. "
          "Locally the pipeline is ETL (Python cleans, then loads SQLite); in Snowflake it is ELT (PUT and COPY INTO load RAW, then "
          "SQL transforms the data inside the warehouse)."),
    ("fig", "pipeline", "figures/f_pipeline.png", "Layered data pipeline from f1.zip to the dashboards", 6.2),
    ("p", "A single script, deploy_to_snowflake.py, runs the master SQL file in order: it creates the X-Small warehouse F1_WH "
          "(suspended after 60 seconds idle), the database, schemas and stages; uploads the files; bulk-loads RAW; transforms into "
          "CLEAN and DW; and loads the model outputs into ML. It then creates the platform features listed below, giving 42 objects "
          "in total, 29 of them tables and views."),
    ("bullets", [
        "**Zero-copy clone:** CLEAN.F1_MODELING_MASTER_DEV_CLONE shares storage with the original table, for safe development and testing.",
        "**Time Travel:** queries such as AT(OFFSET => -300) read a table as it was five minutes earlier, for recovery and auditing.",
        "**Stream and task:** RAW.STREAM_RACE_RESULTS_CDC captures new race results (change data capture); the task ML.TASK_AUTO_SCORE_F1_PREDICTIONS scores them when the stream has data. It is kept suspended to save trial credits.",
        "**Secure view:** ANALYTICS.SECURE_F1_PUBLIC_LEADERBOARD exposes only public columns to the read-only role F1_ANALYST_READONLY.",
        "**Dynamic table:** a rolling five-race form per driver that Snowflake keeps fresh within a one-hour target lag.",
        "**Streamlit in Snowflake:** the full dashboard runs inside the account as the app F1_RACE_INTELLIGENCE, using the account's own session, so no password is stored in the app [@sis].",
    ]),
    ("h2", "2.5  SUPERVISED DATASET AND CLASS LABELS"),
    ("p", "The supervised dataset has one row per driver per Grand Prix: 12,358 entries from 577 Grands Prix between 1994 and 2024. "
          "The primary class label is target_is_win (1 for the winner, 0 otherwise); podium, points finish and retirement are "
          "secondary labels. Every race has exactly one winner and no label is missing."),
    ("p", "Sixteen features describe each driver before the race, in five groups: qualifying (grid position, out-qualified the "
          "teammate, gap between grid slot and recent form), driver form (average finish and points over the last five races, "
          "season points so far), team form (average finish and points over the team's last ten races), circuit history (average "
          "finish, win rate, podium rate and number of starts at the track) and career (starts, win rate, retirement rate and age)."),
    ("p", "Leakage is prevented in three ways. Every rolling feature is shifted by one race, so it only uses earlier races. The "
          "split is chronological: models train on 1994–2021 (509 Grands Prix), are validated on 2022 (22) and tested on 2023–2024 "
          "(46), and code asserts that no test race is older than any training race. No in-race information such as pit strategy, "
          "safety cars or fastest laps is used."),
    ("h2", "2.6  FREQUENT PATTERN MINING"),
    ("p", "For pattern mining each driver-race becomes a transaction of 24 possible items describing the grid band, recent form, "
          "team strength, the teammate battle and the outcome, for example Grid_Pole_P1 or Outcome_Podium. Frequent itemsets are "
          "mined at a minimum support of 0.02 and rules are kept above a confidence of 0.25, using the measures in Equations "
          "{eq:sup} to {eq:lift}."),
    ("eq", "sup", "support(X ⇒ Y) = P(X ∪ Y)"),
    ("eq", "conf", "confidence(X ⇒ Y) = support(X ∪ Y) / support(X)"),
    ("eq", "lift", "lift(X ⇒ Y) = confidence(X ⇒ Y) / support(Y)"),
    ("p", "Two algorithms are compared. **Apriori** [@agrawal] generates candidate itemsets level by level and scans the data once "
          "per level. **FP-Growth** [@fpgrowth] compresses the data into a prefix tree in two scans and mines it recursively without "
          "generating candidates. Both must return exactly the same itemsets, which the code checks."),
    ("h2", "2.7  CLASSIFICATION MODEL"),
    ("p", "Seven classifiers are compared on the same features and split: a dummy classifier, a logistic regression on grid "
          "position only (the pole-sitter baseline), a decision tree, a random forest [@breiman], gradient boosting [@friedman], "
          "LightGBM [@lightgbm] and XGBoost [@xgboost]. The champion is XGBoost, which minimises a regularised loss over K trees:"),
    ("eq", "xgb", "L = Σ_i w_i · l(y_i, ŷ_i) + Σ_k (γ · T_k + ½ · λ · ‖w_k‖²)"),
    ("p", "where l is the log loss, T_k the number of leaves of tree k and w_k its leaf weights. The model is made cost-sensitive "
          "[@elkan] by giving every winner a sample weight w_i = 15 (scale_pos_weight), so a missed winner costs fifteen times more "
          "than a false alarm. It uses 100 trees of depth 4, a learning rate of 0.05 and 85% row and column sampling. Per-driver "
          "probabilities do not add up to one across a race, so a race-level softmax with temperature T = 0.8 [@guo] turns them into "
          "a distribution over the drivers in that race:"),
    ("eq", "softmax", "P(i wins) = exp(log p_i / T) / Σ_j exp(log p_j / T)"),
    ("p", "The driver with the highest probability is the predicted winner. Models are judged on ROC-AUC, PR-AUC, recall and the "
          "share of races in which the predicted winner actually won, not on accuracy. Stability is checked with a six-fold "
          "expanding window (train on 1994 up to the previous season, test on the next) [@bergmeir], and the gain over the baseline "
          "with a paired bootstrap that resamples whole races 1,000 times [@efron] and a Wilcoxon signed-rank test [@wilcoxon]."),
    ("h2", "2.8  CLUSTERING OF DRIVER SEASONS"),
    ("p", "Clustering uses a different grain: one row per driver per season. The unsupervised dataset has 703 driver-season "
          "profiles of 153 drivers from 1994 to 2024, each described by nine standardised features: average grid, average finish, "
          "spread of finishes, win rate, podium rate, points rate, retirement rate, teammate qualifying rate and number of starts. "
          "There is no label."),
    ("p", "Six algorithms are compared: K-Means [@macqueen], K-Medoids (PAM) [@kaufman], Ward agglomerative clustering [@ward], "
          "a Gaussian mixture fitted by EM [@dempster], BIRCH [@birch] and DBSCAN [@dbscan] with eps = 1.3 and five minimum samples, "
          "chosen from the k-distance curve. K-Means minimises the within-cluster sum of squares in Equation {eq:kmeans}, and each "
          "point's silhouette in Equation {eq:sil} compares its mean distance a(i) to its own cluster with the mean distance b(i) to "
          "the nearest other cluster [@rousseeuw]."),
    ("eq", "kmeans", "J = Σ_k Σ_(x in C_k) ‖x − μ_k‖²"),
    ("eq", "sil", "s(i) = (b(i) − a(i)) / max(a(i), b(i))"),
    ("p", "The number of clusters is chosen from the elbow of the inertia curve and checked with the Ward dendrogram. Clusters are "
          "then validated internally (silhouette, Davies-Bouldin, Calinski-Harabasz), for stability (ARI across random seeds and "
          "bootstrap samples [@ari]) and externally against the real championship standings, which are never used to fit them."),
    ("h2", "2.9  NEXT-RACE FORECASTING"),
    ("p", "To predict races that have not happened yet, the history is extended with the 45 Grands Prix of 2025 and 2026 (941 "
          "results) from the Jolpica-F1 API [@ergast], converted to the project's conventions: a pit-lane start or a grid slot above "
          "20 counts as 20, any status other than Finished or Lapped counts as a retirement, and new drivers, teams and circuits get "
          "new identifiers. For each driver in the latest line-up the 16 features are rebuilt from the history before the race date. "
          "The rebuild was checked against the original feature store: for the 2024 Abu Dhabi Grand Prix all 16 features match "
          "exactly."),
    ("p", "Qualifying has not happened when a forecast is made, so the default grid ranks drivers by their average starting "
          "position over their last five races. The champion model is retrained on every race up to the latest one and scores the "
          "line-up. In the dashboard a user can change the race, the pole-sitter and one driver's team, starting position, recent "
          "form and teammate battle, and the forecast is recalculated at once."),
])

CH3 = ("3.  LITERATURE SURVEY", [
    ("h2", "3.1  DATA WAREHOUSING AND OLAP"),
    ("p", "Inmon defined the data warehouse as a subject-oriented, integrated, time-variant and non-volatile store that supports "
          "decision making, separate from operational systems [@inmon]. Kimball and Ross made dimensional modelling practical: "
          "declare the grain, then design facts and conformed dimensions around it, and prefer star schemas for query simplicity "
          "[@kimball]. Chaudhuri and Dayal surveyed the architecture of warehouses and the OLAP operations built on them "
          "[@chaudhuri], and Gray et al. introduced the data cube operator that generalises GROUP BY to roll-ups and cross-tabs "
          "[@gray]. Dageville et al. described Snowflake's design, which separates storage from compute and makes features such as "
          "zero-copy cloning and Time Travel cheap [@snowflake]. ApexIQ follows Kimball's grain-first design and uses these "
          "Snowflake features directly."),
    ("h2", "3.2  FREQUENT PATTERN MINING"),
    ("p", "Agrawal and Srikant introduced Apriori, which prunes candidate itemsets using the property that every subset of a "
          "frequent itemset must itself be frequent [@agrawal]. Han, Pei and Yin showed that FP-Growth avoids candidate generation "
          "altogether by compressing transactions into an FP-tree, and is faster on dense data and low support thresholds "
          "[@fpgrowth]. Tan, Kumar and Srivastava compared interestingness measures and showed that confidence alone favours "
          "common consequents, which is why lift is reported with every rule [@tan]. ApexIQ runs both algorithms on the same "
          "transactions, confirms that they find identical itemsets, and measures where each one is faster."),
    ("h2", "3.3  SPORTS OUTCOME PREDICTION"),
    ("p", "Bunker and Thabtah proposed a framework for predicting sports results with machine learning and stressed that features "
          "must reflect only information available before the event [@bunker]. Bergmeir and Benítez showed that ordinary k-fold "
          "cross-validation can give optimistic results on time-ordered data and that validation must respect time order "
          "[@bergmeir]. ApexIQ applies both points: every feature is lagged, the holdout seasons come after the training seasons, "
          "and cross-validation uses an expanding window."),
    ("h2", "3.4  IMBALANCED CLASSIFICATION AND ENSEMBLES"),
    ("p", "He and Garcia reviewed learning from imbalanced data and warned that accuracy is misleading when one class is rare "
          "[@he]; Saito and Rehmsmeier showed that precision-recall curves are more informative than ROC curves in that setting "
          "[@saito]. Elkan gave the theory of cost-sensitive learning, in which errors on the rare class are weighted more heavily "
          "[@elkan]. Breiman's random forests [@breiman], Friedman's gradient boosting [@friedman], XGBoost [@xgboost] and LightGBM "
          "[@lightgbm] are the strongest general-purpose models for tabular data. Guo et al. showed that a single temperature "
          "parameter can rescale a model's scores into better-behaved probabilities [@guo], which ApexIQ uses inside each race."),
    ("h2", "3.5  CLUSTERING AND CLUSTER VALIDATION"),
    ("p", "K-Means [@macqueen] minimises within-cluster variance, K-Medoids (PAM) restricts every centre to a real data point and "
          "is less sensitive to outliers [@kaufman], Ward's method merges the clusters that increase variance least [@ward], "
          "Gaussian mixtures fitted with EM give soft memberships [@dempster], BIRCH summarises the data in a single pass "
          "[@birch], and DBSCAN finds dense regions of any shape and marks the rest as noise [@dbscan]. Clusters are judged with "
          "internal indices such as the silhouette [@rousseeuw], Davies-Bouldin [@db] and Calinski-Harabasz [@ch], and compared "
          "with each other or with external labels using the Adjusted Rand Index [@ari]."),
    ("h2", "3.6  SUMMARY OF THE SURVEY"),
    ("p", "Table {tab:survey} summarises the main sources and how each one is used in ApexIQ."),
    ("table", "survey", "Literature survey summary", ["Area", "Key work", "How ApexIQ uses it"], [
        ["Data warehousing", "Inmon [@inmon]; Kimball and Ross [@kimball]", "Grain-first star schema plus a normalised snowflake schema"],
        ["OLAP and cloud warehouse", "Chaudhuri and Dayal [@chaudhuri]; Gray et al. [@gray]; Dageville et al. [@snowflake]", "Twelve OLAP queries; layered Snowflake deployment with cloning, Time Travel, streams and tasks"],
        ["Pattern mining", "Agrawal and Srikant [@agrawal]; Han, Pei and Yin [@fpgrowth]; Tan et al. [@tan]", "Apriori and FP-Growth on the same transactions; rules ranked by lift"],
        ["Sports prediction", "Bunker and Thabtah [@bunker]; Bergmeir and Benítez [@bergmeir]", "Pre-race features only; chronological holdout and expanding-window validation"],
        ["Imbalanced learning", "He and Garcia [@he]; Elkan [@elkan]; Saito and Rehmsmeier [@saito]", "Cost-sensitive weights; PR-AUC and top-1 hit rate instead of accuracy"],
        ["Ensembles", "Breiman [@breiman]; Friedman [@friedman]; Chen and Guestrin [@xgboost]; Ke et al. [@lightgbm]", "Seven classifiers compared; XGBoost selected as champion"],
        ["Clustering", "MacQueen [@macqueen]; Kaufman and Rousseeuw [@kaufman]; Ester et al. [@dbscan]", "Six algorithms compared; K-Means selected"],
        ["Cluster validation", "Rousseeuw [@rousseeuw]; Davies and Bouldin [@db]; Hubert and Arabie [@ari]", "Internal, stability and external validation of the tiers"],
    ], [2.2, 4, 4]),
])

CH4 = ("4.  PROJECT PLAN", [
    ("h2", "4.1  DEVELOPMENT MODEL"),
    ("p", "The project followed an iterative model, shown in Figure {fig:dev}. Each of the three dashboards (data warehouse, "
          "supervised learning, unsupervised learning) went through the same cycle: requirements from the course rubric and the "
          "previous review, design of the schema or features, implementation of the module code, validation with tests and holdout "
          "data, and a review with the guide. Feedback from each review fed into the next iteration; the next-race forecaster was "
          "added in the last iteration after the end-semester review asked for predictions of future races."),
    ("fig", "dev", "figures/f_dev_model.png", "Iterative development model followed in the project", 5.6),
    ("h2", "4.2  TEAM ORGANISATION"),
    ("p", "The project was carried out by a team of two. Table {tab:team} lists the members and their responsibilities."),
    ("table", "team", "Team members and responsibilities", ["Member", "Enrollment No", "Responsibilities"], [
        ["Adesh Patankar", "ADT24SOCB0049", "Shared across all modules: data warehouse and Snowflake, data mining models, dashboards and testing"],
        ["Dhruv Sakhare", "ADT24SOCB0369", "Shared across all modules: data warehouse and Snowflake, data mining models, dashboards and testing"],
    ], [2.5, 2.5, 5]),
    ("h2", "4.3  TIMELINE"),
    ("p", "Figure {fig:gantt} shows the schedule of the main activities over the semester, and Table {tab:milestones} lists the "
          "milestones."),
    ("fig", "gantt", "figures/f_gantt.png", "Project schedule (Gantt chart)", 6.2),
    ("table", "milestones", "Project milestones", ["Milestone", "Deliverable"], [
        ["Dataset and labels", "Supervised feature store with class labels and imbalance report"],
        ["Data warehouse", "Star and snowflake schemas, ETL pipeline and OLAP queries"],
        ["Snowflake deployment", "Five-layer deployment with cloud features and live verification"],
        ["Supervised learning", "Pattern mining, classifier comparison and champion model"],
        ["Unsupervised learning", "Driver-season dataset, six clustering algorithms and validated K-Means tiers"],
        ["Dashboards", "Streamlit app (local and in Snowflake) and Power BI report"],
        ["Forecasting and final review", "Next-race forecaster, real-world test, report and end-semester jury"],
    ], [3, 7]),
    ("h2", "4.4  RISK MANAGEMENT"),
    ("p", "Table {tab:risks} lists the main risks identified during the project and how each was handled."),
    ("table", "risks", "Project risks and mitigations", ["Risk", "Impact", "Mitigation"], [
        ["Data leakage from future races", "Inflated, untrustworthy accuracy", "Lagged features, chronological split with an assertion, no in-race data"],
        ["Severe class imbalance (20.4 : 1)", "A model that never predicts a winner", "Cost-sensitive weights; PR-AUC, recall and top-1 hit rate as metrics"],
        ["Limited Snowflake trial credits", "Deployment stops when credits run out", "X-Small warehouse with 60-second auto-suspend; task and dynamic table kept suspended"],
        ["Trial account cannot reach PyPI", "Dashboard fails to start in Snowflake", "App runs on the warehouse runtime with packages from Snowflake's own channel"],
        ["2026 regulation change", "Older form becomes a weaker guide", "Real-world test on 2025–2026 races reported honestly against the pole-sitter"],
        ["Power BI Desktop unavailable on macOS", "Report cannot be opened while building it", "Report generated as a PBIP project with automated self-checks before every build"],
        ["External API rate limits", "Incomplete 2025–2026 results", "Paging with retries and back-off; check that every race has exactly one winner"],
    ], [3, 3, 4]),
])

CH5 = ("5.  SOFTWARE REQUIREMENT SPECIFICATION", [
    ("h2", "5.1  PROJECT SCOPE"),
    ("p", "ApexIQ is an analytical system, not a transactional one. It ingests historical Formula 1 results, stores them in a "
          "dimensional warehouse locally and in Snowflake, runs the data-mining modules, and serves the results through dashboards. "
          "Users read and explore the data and change forecast parameters; they do not edit the stored history."),
    ("h2", "5.2  USER CLASSES AND CHARACTERISTICS"),
    ("table", "users", "User classes", ["User class", "Characteristics", "Main needs"], [
        ["Examiner / faculty", "Evaluates the project against the course outcomes", "See every deliverable, run live queries, verify numbers"],
        ["Analyst / fan", "Interested in race outcomes; no programming needed", "Forecast the next race, explore tiers and patterns"],
        ["Data engineer (project team)", "Maintains the pipeline and models", "Rerun the ETL and modules, redeploy to Snowflake, run tests"],
    ], [2.5, 3.5, 4]),
    ("h2", "5.3  FUNCTIONAL REQUIREMENTS"),
    ("table", "fr", "Functional requirements", ["ID", "Requirement"], [
        ["FR1", "Load the f1.zip source files into a star and a snowflake schema with a documented grain."],
        ["FR2", "Run OLAP queries covering roll-up, drill-down, slice, dice and pivot."],
        ["FR3", "Deploy the warehouse to Snowflake in RAW, CLEAN, DW, ML and ANALYTICS schemas and show live row counts."],
        ["FR4", "Build the supervised dataset with class labels and 16 pre-race features without leakage."],
        ["FR5", "Mine frequent itemsets and association rules with Apriori and FP-Growth and compare them."],
        ["FR6", "Train and compare seven classifiers on unseen seasons and report all metrics."],
        ["FR7", "Predict the winning probability of every driver in a race, adding up to 100% per race."],
        ["FR8", "Cluster driver seasons with six algorithms, choose one and validate it."],
        ["FR9", "Forecast the next Grand Prix and recalculate it when the user changes the race parameters."],
        ["FR10", "Present every result in Streamlit (locally and in Snowflake) and in Power BI."],
    ], [1, 9]),
    ("h2", "5.4  NON-FUNCTIONAL REQUIREMENTS"),
    ("bullets", [
        "**Performance:** a forecast must update within one second of a parameter change; measured at about 0.15 seconds.",
        "**Reproducibility:** every module is deterministic (fixed random seeds) and the whole pipeline reruns with one command in about 20 seconds.",
        "**Security:** credentials are read only from a local .env file that is never committed; the dashboard in Snowflake uses the account's own session; examiners get a read-only role and a secure view.",
        "**Usability:** plain-language labels, consistent colours and an explanation next to every chart.",
        "**Portability:** the same dashboard runs locally (Streamlit 1.67) and inside Snowflake (Streamlit 1.52).",
        "**Maintainability:** each module has one responsibility and its own verification tests.",
    ]),
    ("h2", "5.5  HARDWARE AND SOFTWARE REQUIREMENTS"),
    ("table", "hwsw", "Hardware and software requirements", ["Item", "Requirement"], [
        ["Processor and memory", "Any 64-bit dual-core processor; 8 GB RAM recommended"],
        ["Storage", "About 1 GB for the data, warehouse and models"],
        ["Operating system", "macOS, Windows or Linux"],
        ["Runtime", "Python 3.11 or later with the packages in requirements.txt"],
        ["Cloud", "Snowflake account (trial is sufficient), X-Small warehouse"],
        ["Business intelligence", "Power BI Desktop (Windows) to open the PBIP project"],
        ["Browser", "Any modern browser for the Streamlit dashboard and Snowsight"],
    ], [3, 7]),
    ("h2", "5.6  SYSTEM DESIGN"),
    ("h3", "5.6.1  System Architecture"),
    ("p", "Figure {fig:arch} shows the architecture. Source data flows into the local warehouse and on to Snowflake. The "
          "supervised, unsupervised and forecasting modules read from the warehouse and write their outputs, which the Streamlit "
          "dashboard, the Power BI report and the Snowflake worksheets present."),
    ("fig", "arch", "figures/f_architecture.png", "System architecture of ApexIQ", 6.3),
    ("h3", "5.6.2  Use Cases"),
    ("p", "Figure {fig:uc} shows the main use cases. Examiners and analysts explore the warehouse, review the mining rules, compare "
          "classifiers, forecast the next race and explore driver tiers; the data engineer runs the pipeline, deploys to Snowflake, "
          "retrains the modules and runs the tests."),
    ("fig", "uc", "figures/f_use_cases.png", "Use case diagram", 6.0),
    ("h3", "5.6.3  Forecast Sequence"),
    ("p", "Figure {fig:seq} shows what happens when a user changes a parameter on the race predictor: the dashboard asks the "
          "forecast engine for a new forecast, the engine rebuilds every driver's features from the history before the race date, "
          "the model scores them, and the race softmax turns the scores into probabilities that add up to 100%."),
    ("fig", "seq", "figures/f_sequence.png", "Sequence of a next-race forecast", 6.3),
    ("h3", "5.6.4  Database Design in Snowflake"),
    ("table", "schemas", "Snowflake schemas of F1_PREDICTION_DB", ["Schema", "Contents", "Examples"], [
        ["RAW", "Source files loaded unchanged with COPY INTO", "race results, drivers, constructors, circuits; CDC stream"],
        ["CLEAN", "Typed, deduplicated and validated tables", "F1_MODELING_MASTER and its zero-copy clone"],
        ["DW", "Dimensional model", "FACT_RACE_RESULTS_STAR, DIM_DRIVER, DIM_RACE_SNOWFLAKE, DIM_CIRCUIT, DIM_COUNTRY"],
        ["ML", "Model inputs and outputs", "MODEL_COMPARISON, ASSOCIATION_RULES, DRIVER_SEASON_CLUSTERS, RACE_PREDICTIONS, RACE_FORECAST_UPCOMING, REAL_WORLD_TEST"],
        ["ANALYTICS", "What users see", "secure leaderboard view, dynamic table, Streamlit app"],
    ], [1.6, 3.4, 5]),
    ("h2", "5.7  EXTERNAL INTERFACES"),
    ("table", "interfaces", "External interfaces", ["Interface", "Used for"], [
        ["Snowflake Connector for Python", "Deployment scripts and live queries from the local dashboard"],
        ["Snowsight worksheets", "Read-only SQL for examiners inside the Snowflake account"],
        ["Streamlit in Snowflake", "The dashboard running natively inside the Snowflake account"],
        ["Jolpica-F1 REST API", "Results and calendar after 2024 for the forecaster"],
        ["Power BI Desktop", "Opening the generated PBIP report and its semantic model"],
    ], [3.5, 6.5]),
    ("h2", "5.8  DATA DICTIONARY"),
    ("table", "dict", "Data dictionary of key fields", ["Field", "Type", "Meaning"], [
        ["driver_id, constructor_id, race_id", "INT", "Surrogate keys of the driver, team and race dimensions"],
        ["grid_position", "INT (1–20)", "Starting slot; pit-lane starts count as 20"],
        ["target_finish_position", "INT (1–20)", "Classified finishing position, capped at 20"],
        ["target_is_win", "0 / 1", "Primary class label: 1 for the race winner"],
        ["driver_rolling_finish_5", "FLOAT", "Average finish over the driver's previous five races"],
        ["constructor_rolling_points_10", "FLOAT", "Average points per race over the team's previous ten races"],
        ["circuit_experience", "INT", "Number of earlier starts at this circuit"],
        ["career_win_rate", "FLOAT", "Share of the driver's earlier starts that were wins"],
        ["win_probability", "FLOAT (%)", "Forecast chance to win; adds up to 100 per race"],
        ["cluster_name", "TEXT", "K-Means tier of a driver season"],
    ], [3.4, 1.8, 4.8]),
])

CH6 = ("6.  RESULTS", [
    ("h2", "6.1  DATA WAREHOUSE AND SNOWFLAKE DEPLOYMENT"),
    ("p", "The local warehouse and the Snowflake deployment contain the same data: row counts match exactly for every table "
          "compared, as the dashboard's live verification shows. Table {tab:rows} lists the main objects."),
    ("table", "rows", "Main warehouse objects and row counts", ["Object", "Grain or content", "Rows"], [
        ["FACT_RACE_RESULTS", "One driver in one Grand Prix (2004–2024)", "8,650"],
        ["FACT_LAP_TIMES", "One driver on one lap", "296,727"],
        ["DIM_RACE", "One Grand Prix", "412"],
        ["DIM_DRIVER / DIM_CONSTRUCTOR", "One driver / one team", "108 / 35"],
        ["DIM_STATUS / DIM_COUNTRY", "Finishing state / host country", "91 / 30"],
        ["ML.ASSOCIATION_RULES / frequent itemsets", "Mined rules / itemsets", "1,393 / 414"],
        ["ML.DRIVER_SEASON_CLUSTERS", "One driver in one season", "703"],
        ["Snowflake objects (manifest)", "Tables, views, stages, stream, task, procedure and app", "42"],
    ], [3.8, 4.4, 1.8]),
    ("h2", "6.2  PATTERN MINING RESULTS"),
    ("p", "On 12,358 transactions over 24 items, Apriori and FP-Growth found exactly the same 414 frequent itemsets, from which "
          "1,393 rules were generated. Apriori produced 770 candidates over 5 database scans; FP-Growth built a tree of 4,230 nodes "
          "in 2 scans. Figure {fig:sweep} shows how the two behave as the minimum support falls: Apriori's candidates grow eleven-fold "
          "while the tree stays at 4,230 nodes, and at a support of 0.005 FP-Growth becomes faster (42.4 ms against 46.2 ms)."),
    ("fig", "sweep", "figures/f_mining_sweep.png", "Apriori and FP-Growth as the minimum support falls", 6.2),
    ("p", "The strongest rules connect qualifying with winning. For example, {pole position, podium} ⇒ {out-qualified teammate, "
          "winner} has a support of 0.022, a confidence of 0.64 and a lift of 17.2: drivers who start on pole and reach the podium "
          "win far more often than the base rate of 4.7% would suggest."),
    ("h2", "6.3  CLASSIFIER COMPARISON"),
    ("p", "Table {tab:models} and Figure {fig:modelsfig} compare the seven classifiers on the 68 Grands Prix of 2022–2024, which no "
          "model saw in training. The grid-only baseline is 95% accurate yet finds no winner at a 0.5 threshold, which shows why "
          "accuracy is not used to rank the models. Cost-sensitive XGBoost has the best ROC-AUC, PR-AUC and winner hit rate."),
    ("table", "models", "Holdout results of the seven classifiers (2022–2024, 68 races)", ["Model", "ROC-AUC", "PR-AUC", "Recall", "Winner picked"], [
        ["Dummy classifier", "0.5000", "0.050", "0.485", "23 / 68 (33.8%)"],
        ["Logistic regression, grid only (baseline)", "0.9198", "0.399", "0.000", "35 / 68 (51.5%)"],
        ["Decision tree", "0.9177", "0.472", "0.838", "36 / 68 (52.9%)"],
        ["Random forest", "0.9561", "0.587", "0.897", "35 / 68 (51.5%)"],
        ["Gradient boosting", "0.9622", "0.599", "0.412", "36 / 68 (52.9%)"],
        ["LightGBM", "0.9586", "0.615", "0.838", "35 / 68 (51.5%)"],
        ["**XGBoost, cost-sensitive (champion)**", "**0.9629**", "**0.643**", "**0.853**", "**40 / 68 (58.8%)**"],
    ], [4, 1.4, 1.4, 1.4, 2.4]),
    ("fig", "modelsfig", "figures/f_classifiers.png", "PR-AUC and winner hit rate of the seven classifiers", 6.2),
    ("p", "Figure {fig:cv} shows the expanding-window validation. XGBoost beats the baseline in four of the six seasons; the "
          "baseline wins 2019 and 2020, seasons dominated by pole-sitters. The paired race-level bootstrap gives a mean ROC-AUC gain "
          "of +0.042 with a 95% confidence interval of [+0.018, +0.073], which excludes zero (p < 0.001). The Wilcoxon test over six "
          "folds gives p = 0.078; with only six folds its smallest possible p-value is 0.016, so it has little power here."),
    ("fig", "cv", "figures/f_temporal_cv.png", "Expanding-window validation: ROC-AUC per test season", 5.6),
    ("h2", "6.4  CHAMPION MODEL PERFORMANCE"),
    ("p", "Table {tab:parts} shows the champion's metrics on each partition. Training and test results are close (ROC-AUC 0.973 "
          "and 0.964), so the model is not overfitting."),
    ("table", "parts", "Champion XGBoost metrics by partition", ["Partition", "ROC-AUC", "PR-AUC", "Recall", "Winner picked"], [
        ["Training (1994–2021)", "0.9730", "0.599", "0.935", "301 / 509 (59.1%)"],
        ["Validation (2022)", "0.9606", "0.600", "0.909", "11 / 22 (50.0%)"],
        ["Test (2023–2024)", "0.9636", "0.666", "0.826", "29 / 46 (63.0%)"],
        ["Combined holdout (2022–2024)", "0.9629", "0.643", "0.853", "40 / 68 (58.8%)"],
    ], [3.6, 1.5, 1.5, 1.5, 2.4]),
    ("p", "The confusion matrix in Figure {fig:cm} is at a 0.5 threshold over the 1,359 holdout entries. The model flags 58 of "
          "the 68 winners (recall 0.853) and raises 122 false alarms (precision 0.322): about 2.6 genuine contenders per race are "
          "flagged, of whom only one can win. The race softmax then picks one of them, which is why the winner hit rate is the "
          "measure that matters."),
    ("fig", "cm", "figures/f_confusion.png", "Confusion matrix on the 2022–2024 holdout", 3.2),
    ("p", "Figure {fig:imp} shows the feature importance. Grid position carries 47.5% of the gain, followed by the driver's recent "
          "average finish (10.0%); career win rate, team form and the gap between grid slot and form make up most of the rest."),
    ("fig", "imp", "figures/f_importance.png", "Feature importance of the champion model", 5.4),
    ("p", "The errors are instructive. At the 2024 British Grand Prix the model ranked pole-sitter George Russell first; he "
          "retired with a water-system failure and Lewis Hamilton, ranked second, won. Pre-race data cannot foresee such failures. "
          "The model beats the pole-sitter rule in 8 holdout races, for example 2024 Canada, which Max Verstappen won from second, "
          "and loses to it in 3."),
    ("h2", "6.5  CLUSTERING RESULTS"),
    ("p", "Table {tab:clust} compares the six algorithms on the 703 driver-season profiles. K-Means has the best silhouette and "
          "Calinski-Harabasz index and is stable across random seeds. DBSCAN has the lowest Davies-Bouldin value but labels 7.7% of "
          "seasons as noise and fails on clusters of different density; Ward and BIRCH are unstable (ARI about 0.5)."),
    ("table", "clust", "Comparison of the six clustering algorithms", ["Algorithm", "Clusters", "Silhouette", "Davies-Bouldin", "Calinski-Harabasz", "Stability ARI"], [
        ["**K-Means (champion)**", "3", "**0.264**", "1.276", "**347.5**", "0.945"],
        ["K-Medoids (PAM)", "3", "0.234", "1.393", "329.1", "0.888"],
        ["Agglomerative (Ward)", "3", "0.181", "1.515", "280.8", "0.520"],
        ["Gaussian mixture", "3", "0.141", "1.685", "252.7", "0.995"],
        ["BIRCH", "3", "0.195", "1.523", "298.3", "0.502"],
        ["DBSCAN (7.7% noise)", "4", "0.112", "0.855", "24.0", "0.897"],
    ], [3, 1.3, 1.5, 1.7, 1.9, 1.6]),
    ("p", "The number of clusters was chosen at the elbow of the inertia curve in Figure {fig:k}. A k of 2 has a higher silhouette "
          "but only separates front-runners from everyone else; k = 3 gives three interpretable tiers, which the largest gap in the "
          "Ward dendrogram confirms."),
    ("fig", "k", "figures/f_k_selection.png", "Choosing k: inertia and silhouette for k = 2 to 8", 5.6),
    ("table", "tiers", "Profiles of the three K-Means tiers (cluster centres)", ["Tier", "Seasons", "Avg grid", "Avg finish", "Win rate", "Podium rate", "Retirement rate"], [
        ["Title Contenders", "108", "4.0", "5.0", "25.2%", "59.3%", "13.6%"],
        ["Midfield Regulars", "325", "9.6", "10.4", "1.2%", "9.1%", "27.6%"],
        ["Backmarkers", "270", "16.5", "14.9", "0.0%", "0.3%", "38.6%"],
    ], [2.8, 1.3, 1.3, 1.3, 1.3, 1.5, 1.7]),
    ("p", "The tiers were never shown the championship standings, yet they match them closely (Figure {fig:champ}): 87 of the 108 "
          "Title Contender seasons (81%) ended in the top three of the championship, and no Backmarker season ever did. The "
          "silhouette of 0.264 is moderate because driver performance is a continuum rather than separate islands; only 2% of "
          "points have a negative silhouette, and seed stability is high (mean ARI 0.92)."),
    ("fig", "champ", "figures/f_championship.png", "K-Means tiers against the final championship position", 5.6),
    ("h2", "6.6  NEXT-RACE FORECAST AND REAL-WORLD TEST"),
    ("p", "With history up to the 2026 Las Vegas Grand Prix (22 November 2026), the model forecasts the next race, the Qatar Grand "
          "Prix on 29 November 2026 (Figure {fig:fcfig}). Andrea Kimi Antonelli is favourite at 29.9%, ahead of Lando Norris (24.6%) "
          "and Max Verstappen (23.8%). Table {tab:fc} shows the parameters behind the top five."),
    ("fig", "fcfig", "figures/f_forecast.png", "Forecast for the 2026 Qatar Grand Prix, top ten drivers", 5.6),
    ("table", "fc", "Forecast for the 2026 Qatar Grand Prix with its main parameters", ["Driver", "Team", "Projected start", "Avg finish, last 5", "Team points per race, last 10", "Win chance"], [
        ["Andrea Kimi Antonelli", "Mercedes", "P1", "3.2", "10.5", "29.9%"],
        ["Lando Norris", "McLaren", "P2", "3.4", "11.4", "24.6%"],
        ["Max Verstappen", "Red Bull", "P3", "1.6", "13.4", "23.8%"],
        ["Charles Leclerc", "Ferrari", "P4", "5.2", "9.9", "10.3%"],
        ["George Russell", "Mercedes", "P5", "7.2", "10.5", "3.8%"],
    ], [2.8, 1.7, 1.5, 1.6, 2.2, 1.4]),
    ("p", "To test the model on genuinely unseen races, a copy trained only on 1994–2024 called every Grand Prix of 2025 and 2026 "
          "before it was run, from the information available at the time (Figure {fig:rw}). It named the winner in 29 of 45 races "
          "(16 of 24 in 2025 and 13 of 21 in 2026); simply backing the pole-sitter named 31 (16 and 15). In 2025 the two are level. "
          "In 2026 new technical regulations reshuffled the order, so form built on older seasons became a weaker guide while "
          "qualifying still reflected the new pace. We report this result as it is: on recent races the model is about as good as "
          "the pole-sitter rule, not better."),
    ("fig", "rw", "figures/f_real_world.png", "Real-world test on 2025–2026: winners called by the model and by the pole-sitter", 4.8),
    ("h2", "6.7  PERFORMANCE"),
    ("table", "perf", "Measured run times", ["Operation", "Time"], [
        ["Full module pipeline (run_all_modules.py)", "about 20 s"],
        ["Rebuild of 2025–2026 history, real-world test and forecasts", "about 4 s"],
        ["Forecast update after a parameter change in the dashboard", "about 0.15 s"],
        ["Apriori / FP-Growth at min_support = 0.02", "11.2 ms / 28.1 ms"],
        ["K-Means fit on 703 profiles", "13 ms"],
    ], [7, 3]),
    ("h2", "6.8  DISCUSSION"),
    ("p", "The project shows that a well-designed warehouse makes the mining steps simple: the same star schema feeds the OLAP "
          "queries, the supervised dataset and the clustering profiles, and the Snowflake deployment reproduces it exactly. On the "
          "held-out 2022–2024 seasons the cost-sensitive XGBoost model is clearly better than the pole-sitter rule, and the gain is "
          "statistically significant at the race level. Unsupervised clustering recovers tiers that agree with the real "
          "championship without ever seeing it."),
    ("p", "The real-world test is a useful warning. On 2025–2026 the model was level with the pole-sitter rule in 2025 and behind "
          "it in 2026, when regulation changes made older form less informative. A forecaster for a sport that changes its rules "
          "must weight recent races more, or be retrained as soon as qualifying results are known. The dashboard supports the second "
          "option already: setting the real pole-sitter after qualifying recalculates the forecast at once."),
    ("h2", "6.9  APPLICATION SCREENS"),
    ("h3", "6.9.1  Project Overview and Data Warehouse"),
    ("fig", "s1", "shots/s01_home.png", "Project overview: every page with its key result", 5.6, (0, 1080)),
    ("fig", "s4", "shots/s04_olap.png", "Live OLAP queries against the warehouse", 5.6, (690, 1080)),
    ("h3", "6.9.2  Snowflake Deployment"),
    ("fig", "s5", "shots/s05_sf_deploy.png", "Snowflake deployment: live account, database and schemas", 5.6, (0, 1080)),
    ("fig", "s6", "shots/s06_sf_features.png", "Snowflake advanced features: cloning and Time Travel", 5.6, (0, 1080)),
    ("h3", "6.9.3  Pipeline and Supervised Dataset"),
    ("fig", "s7", "shots/s07_architecture.png", "Pipeline architecture page", 5.6, (0, 1080)),
    ("fig", "s8", "shots/s08_labels.png", "Supervised dataset: class labels and imbalance", 5.6, (690, 1080)),
    ("h3", "6.9.4  Pattern Mining"),
    ("fig", "s9", "shots/s09_mining_algos.png", "Apriori and FP-Growth compared", 5.6, (690, 1080)),
    ("fig", "s10", "shots/s10_rules.png", "Association rules that predict the winner", 5.6, (690, 1080)),
    ("h3", "6.9.5  Classifier Comparison"),
    ("fig", "s11", "shots/s11_holdout.png", "Holdout benchmark of the seven classifiers", 5.6, (690, 1080)),
    ("fig", "s12", "shots/s12_cv.png", "Expanding-window validation by season", 5.6, (690, 1080)),
    ("h3", "6.9.6  Classification Algorithm"),
    ("fig", "s13", "shots/s13_curves.png", "ROC and precision-recall curves with the threshold slider", 5.6, (690, 1080)),
    ("fig", "s14", "shots/s14_explorer.png", "Race explorer: predicted probabilities for one race", 5.6, (690, 1080)),
    ("h3", "6.9.7  Race Predictor"),
    ("fig", "s15", "shots/s15_predictor.png", "Race predictor: next race, filters and predicted podium", 5.6, (330, 1100)),
    ("fig", "s16", "shots/s16_predictor_why.png", "Full predicted order with the parameters behind it", 5.6, (0, 1080)),
    ("fig", "s17", "shots/s17_track.png", "Track record: real-world test against the pole-sitter", 5.6, (690, 1080)),
    ("h3", "6.9.8  Unsupervised Learning"),
    ("fig", "s18", "shots/s18_unsup.png", "Driver-season dataset for clustering", 5.6, (0, 1080)),
    ("fig", "s19", "shots/s19_clust_cmp.png", "Comparison of the six clustering algorithms", 5.6, (0, 1080)),
    ("fig", "s20", "shots/s20_kmeans.png", "K-Means: the three driver tiers", 5.6, (0, 1080)),
    ("fig", "s21", "shots/s21_champ.png", "Clusters against the championship standings", 5.6, (690, 1080)),
])

CH7 = ("7.  SOFTWARE TESTING", [
    ("h2", "7.1  TESTING STRATEGY"),
    ("p", "Testing worked at four levels. Each module has a verification suite that checks its outputs and rules (labels, "
          "features, rules, metrics). A dashboard smoke test renders every page and drives every widget, both with the local "
          "Streamlit version and with the version Snowflake runs. Data and model checks are built into the code as assertions, so "
          "a broken assumption stops the pipeline. Finally, end-to-end cases were run by hand in the browser, in Snowsight and on "
          "the Power BI build."),
    ("h2", "7.2  AUTOMATED TESTS"),
    ("table", "tests", "Automated tests by area", ["Test file", "Area", "Tests"], [
        ["test_dashboard_pages.py", "Every page and widget renders without error", "2"],
        ["test_evaluation_parameters.py", "Rubric capabilities end to end", "9"],
        ["test_f1_architecture_qa.py", "Pipeline architecture and warehouse", "8"],
        ["test_f1_class_labels_qa.py", "Class labels and imbalance", "7"],
        ["test_f1_classification_comparison_qa.py", "Classifier comparison", "6"],
        ["test_f1_clustering_qa.py", "Clustering dataset, algorithms and metrics", "5"],
        ["test_f1_dataset_qa.py", "Feature store and leakage", "7"],
        ["test_f1_input_output_qa.py", "Input and output specification", "5"],
        ["test_f1_pattern_matching_qa.py", "Apriori and FP-Growth", "6"],
        ["test_race_lab_engine_qa.py", "Race prediction engine end to end", "9"],
        ["test_race_predictor.py", "Next-race forecaster and its filters", "6"],
        ["**Total**", "", "**70**"],
    ], [4.2, 4.6, 1.2]),
    ("p", "All 70 tests pass. The forecaster tests check that the 16 features rebuild exactly, that the probabilities add up to "
          "100% and are deterministic, that moving a driver keeps the grid a valid permutation, that pole position raises a "
          "driver's chance, that changing team uses the new team's form and that a form change updates the derived gap feature."),
    ("h2", "7.3  TEST CASES"),
    ("table", "cases", "Manual end-to-end test cases", ["ID", "Test", "Expected result", "Status"], [
        ["TC1", "Open every dashboard page", "Each page renders with data and no error", "Pass"],
        ["TC2", "Set Max Verstappen on pole for Qatar 2026", "He becomes the predicted winner (30.2%) and all chances update", "Pass"],
        ["TC3", "Press Reset all parameters", "Forecast returns to the projected grid", "Pass"],
        ["TC4", "Open Snowflake Deployment", "Live counts from the account match the local files", "Pass"],
        ["TC5", "Run an OLAP roll-up query", "Subtotals per constructor and a grand total", "Pass"],
        ["TC6", "Open the app inside Snowsight", "Dashboard loads on the warehouse runtime", "Pass"],
        ["TC7", "Build the Power BI project", "Self-checks pass: unique measures, valid relationships, strict JSON", "Pass"],
    ], [0.9, 3.3, 4.8, 1]),
    ("h2", "7.4  DATA AND MODEL VALIDATION"),
    ("bullets", [
        "Every race has exactly one winner, and no class label is missing.",
        "No test race is older than any training race (assertion in the training code).",
        "Rolling features are shifted by one race, so they never include the race being predicted.",
        "Apriori and FP-Growth must return identical itemsets before the rules are written.",
        "The rebuilt forecast features must match the feature store exactly for the 2024 Abu Dhabi Grand Prix.",
        "Every forecast scenario must add up to 100% (between 99.5 and 100.5 after rounding).",
    ]),
    ("h2", "7.5  DEFECTS FOUND AND FIXED DURING TESTING"),
    ("table", "defects", "Defects found and fixed", ["Defect", "Cause", "Fix"], [
        ["Snowflake file upload failed", "Project path contains spaces", "Quoted file URIs in every PUT command"],
        ["Dashboard would not start in Snowflake", "Container runtime needs PyPI, blocked on a trial account", "Recreated the app on the warehouse runtime"],
        ["Load times shown in the wrong time zone", "Snowflake returns Pacific time", "Converted to IST with CONVERT_TIMEZONE"],
        ["Power BI refused to load", "Duplicate measure name; missing values written as NaN", "Unique names and strict JSON, both asserted by the builder"],
        ["Every circuit got a new ID in 2025–26 data", "Warehouse circuit references are placeholders", "Matched circuits by name, with the Lusail/Losail alias"],
        ["Rebuilt features did not match the store", "Rounding, sprint points and clipped finishes", "Reverse-engineered the exact rules; added a self-check"],
        ["Chart order broken by colour groups", "Plotly orders categories per colour series", "Fixed the category order explicitly"],
        ["Wrong row highlighted in a table", "Highlight matched “Championship” as well as “Champion”", "Matched only “(Champion)”, with a self-check"],
    ], [3.2, 3.6, 3.2]),
])

CH8 = ("8.  CONCLUSION AND FUTURE WORK", [
    ("h2", "8.1  CONCLUSION"),
    ("p", "ApexIQ meets its objectives. A dimensional warehouse with star and snowflake schemas holds 31 seasons of Formula 1 "
          "results, answers twelve OLAP queries and is deployed to Snowflake in five layers with its main cloud features. On this "
          "foundation, FP-Growth and Apriori find the same 414 frequent itemsets and 1,393 rules; a cost-sensitive XGBoost model "
          "picks the winner of 40 of 68 unseen races, significantly better than the pole-sitter rule; and K-Means finds three "
          "driver tiers that match the championship standings without seeing them."),
    ("p", "The system also looks forward: it forecasts the next Grand Prix from every race up to the latest one, lets the user "
          "change the race parameters and see the forecast update instantly, and reports its own real-world record honestly. "
          "Everything is available in a Streamlit dashboard that runs locally and inside Snowflake, and in a Power BI report."),
    ("h2", "8.2  LIMITATIONS"),
    ("bullets", [
        "The model uses pre-race information only; retirements, safety cars, strategy and weather decide many races.",
        "On the 2025–2026 races it called 29 winners against 31 for the pole-sitter; older form is a weaker guide after the 2026 regulation change.",
        "Before qualifying, the grid is projected from recent starts, so forecasts made early in a race weekend are less certain.",
        "With 21 to 24 races per season, per-season comparisons have little statistical power.",
        "The Snowflake task scores new results with a simple pole rule, not the XGBoost model, to stay within trial credits.",
        "Power BI cannot run the model, so its forecast page uses 44 precomputed race and pole-sitter scenarios.",
        "Results after 2024 come from a community API rather than the original dataset.",
    ]),
    ("h2", "8.3  FUTURE WORK"),
    ("bullets", [
        "Update the forecast automatically after qualifying, using the real grid instead of the projected one.",
        "Run the model inside Snowflake as a Snowpark Python function, so the stream and task score new results with XGBoost.",
        "Weight recent races more heavily, or add era features, so the model adapts faster to regulation changes.",
        "Add weather, tyre and practice-session data where it is available before the race.",
        "Calibrate the probabilities and report calibration alongside ranking metrics.",
        "Model sprint races and predict podiums and points finishes as well as the winner.",
    ]),
])

CHAPTERS = [CH1, CH2, CH3, CH4, CH5, CH6, CH7, CH8]
