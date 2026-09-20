# Project Processing Flow

```text
CIC-IDS2017 CSV files
        |
        v
prepare_cicids2017.py
- normalize column names
- map detailed labels to broad attack families
- cap rows/class for laptop-friendly training
        |
        v
prepared CSV
        |
        +------------------------+
        |                        |
        v                        v
XGBoost classifier        StandardScaler
known class prediction           |
                                 v
                         Autoencoder trained
                         only on BENIGN rows
                                 |
                                 v
                         reconstruction error
        |                        |
        +-----------+------------+
                    v
              combined risk
                    |
                    v
            Streamlit dashboard
```

## Phase 1 — Verify setup
Run the bundled synthetic demo end-to-end.

## Phase 2 — Real dataset
Download CIC-IDS2017 MachineLearningCSV and place extracted CSVs in `data/raw/`.

## Phase 3 — Train
Prepare a laptop-sized balanced dataset, then train both models.

## Phase 4 — Evaluate
Review `reports/classification_report.csv`, `reports/confusion_matrix.csv`, and `reports/training_metrics.json`.

## Phase 5 — Resume/GitHub
Only quote metrics from the real dataset run. Add screenshots of the dashboard and a short limitations section.
