# Network Intrusion Detection & Anomaly Monitoring System

A student-friendly cybersecurity project that combines:

- **XGBoost** for known network-attack classification
- **PyTorch Autoencoder** for anomaly detection
- **Streamlit + Plotly** for an interactive security dashboard
- **CIC-IDS2017** as the intended real cybersecurity dataset

> The bundled synthetic demo data is only for checking that the complete code pipeline runs on your laptop. Final experiments and resume metrics should come from the real CIC-IDS2017 data.

## What the project does

1. Reads network-flow records from CSV.
2. Cleans and selects numeric traffic features.
3. Trains XGBoost to classify known traffic/attack families.
4. Trains an autoencoder only on BENIGN traffic so unusual records can be flagged by reconstruction error.
5. Combines classifier + anomaly signals into LOW/MEDIUM/HIGH risk.
6. Shows results in a Streamlit dashboard and exports predictions.

## Screenshots

### 1. Model Summary
![Model Summary](Screenshots/model_summary.png)

### 2. DDoS Traffic Analysis Dashboard
![DDoS Analysis Dashboard](Screenshots/ddos_analysis_dashboard.png)

## Folder structure

```text
network_intrusion_project/
├── app.py
├── config.py
├── requirements.txt
├── setup_windows.bat
├── run_demo.bat
├── run_dashboard.bat
├── train_real_cicids.bat
├── data/
│   ├── raw/          # Put extracted CIC-IDS2017 MachineLearningCSV files here
│   ├── processed/    # Prepared balanced dataset is written here
│   └── demo/         # Synthetic pipeline-check data
├── models/           # Trained model artifacts
├── reports/          # Metrics/confusion matrix/predictions
└── src/
    ├── common.py
    ├── generate_demo_data.py
    ├── prepare_cicids2017.py
    ├── train_all.py
    ├── inference.py
    └── predict_csv.py
```

## Recommended Windows setup

Use **Python 3.11 (64-bit)**. This is a conservative choice for compatibility with the project libraries.

### First-time setup

1. Install Python 3.11 from https://www.python.org/downloads/ if needed.
2. During installation enable **Add Python to PATH**.
3. Extract this project ZIP.
4. Double-click `setup_windows.bat`.
5. After installation finishes, you can double-click `run_dashboard.bat` to open the bundled verified demo model immediately, or `run_demo.bat` to reproduce training yourself.

`run_demo.bat` will:
- create synthetic demo traffic,
- train XGBoost,
- train the autoencoder,
- save all model files,
- start the Streamlit dashboard.

Your browser should open at a local address such as `http://localhost:8501`.

## Real dataset: CIC-IDS2017

Official dataset information page:
https://www.unb.ca/cic/datasets/ids-2017.html

Download the **MachineLearningCSV** version, extract it, and copy all CSV files into:

```text
data/raw/
```

Then double-click:

```text
train_real_cicids.bat
```

By default, the preparation step keeps up to 5,000 records per broad attack family. This keeps training manageable on a normal student laptop while preserving multiple classes. You can later increase this value.

The preparation script groups detailed CICIDS labels into:
- BENIGN
- DDoS
- DoS
- PortScan
- BruteForce
- Bot
- WebAttack
- Infiltration
- Heartbleed

(Only classes found in your downloaded CSVs will be used.)

## Run manually in VS Code / terminal

From the project folder:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.generate_demo_data --rows 6000
python -m src.train_all --data data\demo\demo_network_traffic.csv --epochs 15
streamlit run app.py
```

For real CICIDS data:

```bat
python -m src.prepare_cicids2017 --input-dir data\raw --max-per-class 5000
python -m src.train_all --data data\processed\cicids2017_prepared.csv --epochs 20
streamlit run app.py
```

## Command-line prediction

After training:

```bat
python -m src.predict_csv data\demo\upload_sample.csv
```

Predictions are written to `reports/predictions.csv`.

## Important project honesty note

Do **not** report metrics from the synthetic demo dataset on your resume. The demo data is deliberately easy and exists only to confirm that installation, training, inference and the dashboard work end to end. Use the real CIC-IDS2017 preparation/training flow for final metrics.

## Common Windows issues

### `py -3.11` is not recognized
Install Python 3.11 and enable the Python launcher / PATH option.

### XGBoost DLL error
Install the current Microsoft Visual C++ Redistributable (x64), then reopen the terminal.

### PyTorch installation is large
That is normal; the CPU package can still take substantial disk space. A GPU is not required for this project.

### Streamlit says model files are missing
Run `run_demo.bat` once, or train on CICIDS using `train_real_cicids.bat`.

### CICIDS preparation says no CSV files were found
Make sure you extracted the MachineLearningCSV ZIP and put the `.csv` files (not the ZIP itself) inside `data/raw/`.

## Resume-safe description (after real training)

**Network Intrusion Detection & Anomaly Monitoring System**  
*Python, XGBoost, PyTorch, Scikit-learn, Streamlit, Plotly*

- Built a network-flow intrusion detection pipeline using XGBoost to classify known attack patterns from labelled security traffic.
- Implemented an autoencoder trained on benign traffic to flag anomalous network behavior using reconstruction error.
- Developed an interactive dashboard for attack distribution, anomaly alerts, risk levels and CSV-based traffic analysis.

Replace/extend these bullets only with features and metrics you have actually run and verified.
