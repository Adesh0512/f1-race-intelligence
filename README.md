# Formula 1 Race Intelligence & Winner Prediction System (1994–2024)

**Authors:** Adesh Patankar · Dhruv Sakhare (MIT School of Computing, DWDM 2025–26) · **Maintained by** Adesh Patankar ([@Adesh0512](https://github.com/Adesh0512))

An enterprise machine learning and pattern mining framework designed to classify and predict Formula 1 Grand Prix race winners using historical data across 31 FIA World Championship seasons (1994–2024).

This repository is structured into **12 Production Engineering Modules**:

1. **01 Architecture Diagram:** Complete end-to-end data and model pipeline with Apriori / FP-Growth association branches.
2. **02 Input / Output Specification:** 16 pre-race features, JSON Schemas, and sample prediction payloads.
3. **03 Class Labels:** Mathematical target definitions, class imbalance audit (20.42:1), and zero missing labels.
4. **04 Pattern Matching: Apriori and FP-Growth:** Association rule mining on 12,358 race transactions, runtime benchmarks, and equivalence proof.
5. **05 Algorithm Comparison and Validation:** Benchmark of 7 classification models on chronological holdout and 6-fold expanding window.
6. **06 Classification Algorithm:** Production XGBoost pipeline with cost-sensitive weighting, artifact persistence, and group softmax.
7. **07 Innovation:** Leakage-safe multi-horizon rolling form, circuit affinity, and teammate relational deltas (+4.36% ROC-AUC, +20.15% PR-AUC).
8. **08 Performance Metrics:** Empirical holdout metrics: Accuracy, Precision, Recall, F1, Confusion Matrix, ROC-AUC, Brier score, and Log Loss across Train, Validation, and Test partitions.
9. **09 Unsupervised Dataset (Dashboard 3):** 703 unlabelled driver-season performance profiles with 9 standardised features.
10. **10 Clustering Algorithm Comparison (Dashboard 3):** K-Means, Agglomerative (Ward), Gaussian Mixture, BIRCH and DBSCAN, with elbow and silhouette k-selection.
11. **11 Clustering Algorithm (Dashboard 3):** Champion K-Means (k = 3): Title Contenders, Midfield Regulars, Backmarkers.
12. **12 Clustering Performance Metrics (Dashboard 3):** Silhouette, Davies-Bouldin, Calinski-Harabasz, seed/bootstrap stability ARI, and an external check against championship standings.

---

## End-Semester Jury: Run the Dashboard

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # one-time setup
.venv/bin/python run_all_modules.py                                    # regenerate every number (≈20 s)
.venv/bin/streamlit run streamlit_app.py                               # open http://localhost:8501
.venv/bin/python -m unittest discover -s tests                         # 61 automated checks
```

The sidebar follows the rubric: **Dashboard 1 · Data Warehouse** (warehouse design, Snowflake deployment), **Dashboard 2 · Supervised Learning** (dataset, FP-Growth vs Apriori, classifier comparison & validation, classification algorithm) and **Dashboard 3 · Unsupervised Learning** (dataset, clustering comparison, K-Means, clustering metrics). Oral prep: `JURY_QA_PREP.md`. Report: `PROJECT_REPORT_DWDM_APEXIQ.pdf`.

> Use the project `.venv`: the saved models need NumPy 2 and scikit-learn ≥ 1.9.

## Quickstart: Reproducing All Engineering Modules

All modules are self-contained and executable using standard Python (`py -3` or `python`):

```bash
# Navigate to the project root
cd f1-race-intelligence

# 1. Module 03: Verify Class Labels & Target Distributions
py -3 03_class_labels/label_generation.py

# 2. Module 04: Execute FP-Growth & Apriori Association Mining
py -3 04_pattern_mining/fp_growth_analysis.py

# 3. Module 05: Run 7-Model Chronological Comparison & Expanding-Window Validation
py -3 05_algorithm_comparison/train_comparison.py
py -3 05_algorithm_comparison/temporal_validation.py

# 4. Module 06: Train Champion XGBoost Classifier & Persist Artifacts
py -3 06_classification_algorithm/improved_classifier.py

# 5. Module 07: Run Head-to-Head Innovation Experiment (Baseline vs. Improved)
py -3 07_innovation/baseline_vs_improved.py

# 6. Module 08: Calculate Comprehensive Performance Metrics & Export CSVs
py -3 08_performance_metrics/calculate_metrics.py

# 7. Dashboard 3: Unsupervised Clustering (run in order)
py -3 09_unsupervised_dataset/build_unsupervised_dataset.py
py -3 10_clustering_comparison/clustering_comparison.py
py -3 11_clustering_algorithm/kmeans_clustering.py
py -3 12_clustering_metrics/clustering_metrics.py
```

---

## Directory Organization

```
f1-race-intelligence/
├── README.md                                  # Repository overview and execution guide
├── EVALUATION_INDEX.md                        # Master capability & architecture mapping
├── PROJECT_STATUS.md                          # Implementation and verification status
│
├── 01_architecture/                           # Pipeline Architecture
│   ├── architecture_diagram.mmd               # Mermaid source
│   ├── architecture_diagram.md                # Diagram document
│   └── architecture_explanation.md            # Structural description
│
├── 02_input_output/                           # Input / Output Specification
│   ├── input_output_specification.md          # 16-feature tabular specification
│   ├── input_schema.json                      # JSON Schema for inference payload
│   ├── output_schema.json                     # JSON Schema for predictions
│   └── sample_prediction.json                 # Sample payload (2024 British GP)
│
├── 03_class_labels/                           # Class Labels & Target Formulation
│   ├── class_label_definitions.md             # Mathematical label rules
│   ├── label_generation.py                    # Label generator & validation audit
│   └── class_distribution_report.md           # Imbalance ratios & null audit
│
├── 04_pattern_mining/                         # Pattern Matching & Mining
│   ├── pattern_analysis.md                    # Unsupervised association mining theory
│   ├── apriori_analysis.py                    # Apriori algorithm script
│   ├── fp_growth_analysis.py                  # FP-Growth algorithm script
│   ├── association_rules.csv                  # 1,393 discovered rules
│   └── pattern_mining_report.md               # Empirical benchmark & equivalence proof
│
├── 05_algorithm_comparison/                   # Algorithm Comparison & Validation
│   ├── algorithms_and_rationale.md            # Inductive bias analysis of 7 models
│   ├── train_comparison.py                    # Chronological multi-model benchmark
│   ├── temporal_validation.py                 # 6-fold expanding-window leakage proof
│   ├── comparison_results.csv                 # Benchmark tabular metrics
│   └── comparison_report.md                   # Evaluation report
│
├── 06_classification_algorithm/               # Classification Algorithm Engine
│   ├── classification_methodology.md          # End-to-end methodology
│   ├── baseline_classifier.py                 # Grid-only linear baseline
│   ├── improved_classifier.py                 # Champion XGBoost pipeline
│   ├── feature_engineering.py                 # Preprocessing & 16-feature module
│   └── model_card.md                          # Standard ML Model Card
│
├── 07_innovation/                             # Innovation & Feature Engineering
│   ├── innovation_proposal.md                 # Theoretical motivation & design
│   ├── innovation_implementation.py           # Multi-horizon rolling features & softmax
│   ├── baseline_vs_improved.py                # Direct head-to-head evaluation
│   └── innovation_results.md                  # Measured deltas & limitation analysis
│
├── 08_performance_metrics/                    # Performance Metrics & Verification
│   ├── calculate_metrics.py                   # Master evaluation metric script
│   ├── classification_report.csv              # Per-class classification metrics
│   ├── confusion_matrix.csv                   # TN, FP, FN, TP holdout matrix
│   ├── metric_definitions.md                  # Mathematical definitions of metrics
│   └── performance_analysis.md                # Quantitative Train/Val/Test analysis
│
├── data/                                      # Datasets
│   ├── README.md                              # Data dictionary & lineage
│   ├── raw/F1_ML_Winner_Prediction_Dataset.csv# Master raw historical dataset
│   └── processed/F1_RACE_LAB_FEATURES_1994_2024.csv # 12,358 processed race records
│
├── src/                                       # Reusable Service Layer
│   └── race_lab_service.py                    # In-memory inference engine
│
├── app/                                       # Interactive Dashboard
│   └── race_lab.html                          # Race Lab interactive UI
│
├── models/                                    # Serialized Model Artifacts
│   ├── champion_xgboost_classifier.joblib     # Persisted XGBoost champion
│   ├── f1_race_lab_models.joblib              # Multi-target bundle
│   └── f1_winner_model.joblib                 # Winner prediction joblib
│
├── results/                                   # Benchmark Logs
│   ├── f1_classification_benchmark_results.csv
│   ├── f1_ablation_study_results.csv
│   └── race_lab_metrics.json
│
└── tests/                                     # Automated Test Suites
    ├── test_f1_architecture_qa.py
    ├── test_f1_input_output_qa.py
    ├── test_f1_class_labels_qa.py
    ├── test_f1_pattern_matching_qa.py
    ├── test_f1_classification_comparison_qa.py
    ├── test_f1_dataset_qa.py
    └── test_race_lab_engine_qa.py
```

---

## Running the Automated Test Suites

To verify end-to-end functionality across all components:

```bash
# Run all test suites
py -3 -m unittest discover -s tests -p "test_*.py"
```
