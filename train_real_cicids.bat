@echo off
setlocal
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat

echo Preparing CIC-IDS2017 CSV files from data\raw ...
python -m src.prepare_cicids2017 --input-dir data\raw --max-per-class 5000
if %errorlevel% neq 0 goto :error

echo Training XGBoost + Autoencoder on prepared CIC-IDS2017 data...
python -m src.train_all --data data\processed\cicids2017_prepared.csv --epochs 20
if %errorlevel% neq 0 goto :error

echo Training complete. Starting dashboard...
streamlit run app.py
exit /b 0

:error
echo.
echo Training failed. Copy the error shown above and share it for debugging.
pause
