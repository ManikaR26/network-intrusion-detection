@echo off
setlocal
cd /d %~dp0

echo ==============================================
echo Repair environment + train on CIC-IDS2017
echo ==============================================

if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found.
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)

echo.
echo [1/4] Repairing Python packages inside .venv ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 goto :error

echo.
echo [2/4] Checking imports ...
".venv\Scripts\python.exe" -c "import numpy,pandas,sklearn,xgboost,torch,streamlit,plotly,joblib; print('Environment OK'); print('NumPy:', numpy.__version__)"
if %errorlevel% neq 0 goto :error

echo.
echo [3/4] Preparing CIC-IDS2017 CSV files from data\raw ...
".venv\Scripts\python.exe" -m src.prepare_cicids2017 --input-dir data\raw --max-per-class 5000
if %errorlevel% neq 0 goto :error

echo.
echo [4/4] Training XGBoost + Autoencoder ...
".venv\Scripts\python.exe" -m src.train_all --data data\processed\cicids2017_prepared.csv --epochs 20
if %errorlevel% neq 0 goto :error

echo.
echo Training complete. Starting dashboard ...
".venv\Scripts\python.exe" -m streamlit run app.py
exit /b 0

:error
echo.
echo Something failed. Take a screenshot of the last 15-20 lines and send it here.
pause
