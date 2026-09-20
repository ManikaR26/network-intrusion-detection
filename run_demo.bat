@echo off
setlocal
cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup_windows.bat first.
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat
python -m src.generate_demo_data --rows 6000
if %errorlevel% neq 0 goto :error

python -m src.train_all --data data\demo\demo_network_traffic.csv --epochs 15
if %errorlevel% neq 0 goto :error

echo.
echo Starting dashboard...
streamlit run app.py
exit /b 0

:error
echo.
echo Demo failed. Copy the error shown above and share it for debugging.
pause
