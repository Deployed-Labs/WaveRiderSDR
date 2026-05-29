@echo off
setlocal

REM WaveRider SDR Windows launcher

python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Python is not installed or not in PATH.
  echo Install Python 3.10+ and try again.
  exit /b 1
)

if "%~1"=="" (
  python run.py --mode desktop
) else (
  python run.py %*
)

exit /b %errorlevel%
