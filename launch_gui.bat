@echo off
setlocal

REM WaveRider SDR GUI launcher for Windows

pythonw --version >nul 2>&1
if %errorlevel% equ 0 (
  pythonw waverider_tk_gui.py
  exit /b %errorlevel%
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Python is not installed or not in PATH.
  echo Install Python 3.10+ and try again.
  exit /b 1
)

python waverider_tk_gui.py
exit /b %errorlevel%
