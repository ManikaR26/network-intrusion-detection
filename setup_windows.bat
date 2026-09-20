@echo off
setlocal
cd /d %~dp0

echo ==============================================
echo Network Intrusion Detection - Windows Setup
echo ==============================================

where py >nul 2>nul
if %errorlevel% neq 0 (
  echo Python launcher 'py' was not found.
  echo Install Python 3.11 from python.org and check 'Add Python to PATH'.
  pause
  exit /b 1
)

py -3.11 --version >nul 2>nul
if %errorlevel% neq 0 (
  echo Python 3.11 is not installed.
  echo Please install Python 3.11, then run this file again.
  pause
  exit /b 1
)

if not exist .venv (
  echo Creating virtual environment...
  py -3.11 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
  echo.
  echo Installation failed. Check internet connection and the troubleshooting section in README.md.
  pause
  exit /b 1
)

echo.
echo Setup complete.
echo Next: double-click run_demo.bat
pause
