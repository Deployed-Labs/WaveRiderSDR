@echo off
REM WaveRider SDR Python setup helper for Windows

setlocal

echo ===========================================
echo WaveRider SDR Python Setup (Windows)
echo ===========================================

REM Check Python availability
python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Python is not installed.
  echo Install Python 3.10+ then re-run this script.
  exit /b 1
)

echo [OK] Python detected

echo [*] Installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo [ERROR] Dependency installation failed
  exit /b 1
)

echo [*] Verifying Python modules...
python -m py_compile run.py waverider_common.py waverider_web.py waverider_sdr.py
if %errorlevel% neq 0 (
  echo [ERROR] Python module validation failed
  exit /b 1
)

echo [OK] Setup complete
echo Run with: python run.py --mode desktop

exit /b 0
