@echo off
REM WaveRider SDR Installation Script for Windows
REM This script automates the installation process for WaveRider SDR

setlocal enabledelayedexpansion

REM Check if running with admin privileges (optional for some features)
net session >nul 2>&1
if %errorlevel% == 0 (
    set "IS_ADMIN=1"
) else (
    set "IS_ADMIN=0"
)

:banner
cls
echo.
echo ============================================================
echo.
echo          WAVERIDER SDR - Windows Installation
echo.
echo          Platform: Windows
echo.
echo ============================================================
echo.

:check_python
echo [*] Checking Python installation...

REM Try python3 first
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON_CMD=python3"
    goto python_found
)

REM Try python
python --version >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON_CMD=python"
    goto python_found
)

REM Try py launcher
py --version >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON_CMD=py"
    goto python_found
)

:python_not_found
echo [ERROR] Python 3 is not installed or not in PATH
echo.
echo Please install Python 3 from:
echo   https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH" during installation!
echo.
pause
exit /b 1

:python_found
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION% found
echo.

:check_pip
echo [*] Checking pip installation...

%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed
    echo.
    echo Installing pip...
    %PYTHON_CMD% -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pip
        pause
        exit /b 1
    )
)

echo [OK] pip is available
echo.

:upgrade_pip
echo [*] Upgrading pip to latest version...
%PYTHON_CMD% -m pip install --upgrade pip
echo.

:install_dependencies
echo [*] Installing Python dependencies...
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully
echo.

:install_sdr_support
echo.
set /p SDR_SUPPORT="Would you like to install SDR hardware support? (y/n): "
if /i "%SDR_SUPPORT%"=="y" (
    echo.
    echo [*] Installing SDR hardware libraries...
    %PYTHON_CMD% -m pip install pyrtlsdr
    
    echo.
    echo [INFO] For HackRF support, you need to install SoapySDR:
    echo   1. Download from: https://github.com/pothosware/SoapySDR/wiki
    echo   2. Install HackRF drivers: https://github.com/greatscottgadgets/hackrf
    echo.
    pause
)

:create_launcher
echo.
echo [*] Creating launcher batch files...

REM Create simple launcher
echo @echo off > waverider.bat
echo cd /d "%%~dp0" >> waverider.bat
echo %PYTHON_CMD% run.py %%* >> waverider.bat

REM Create web version launcher
echo @echo off > waverider-web.bat
echo cd /d "%%~dp0" >> waverider-web.bat
echo %PYTHON_CMD% run.py --web >> waverider-web.bat

REM Create desktop version launcher
echo @echo off > waverider-desktop.bat
echo cd /d "%%~dp0" >> waverider-desktop.bat
echo %PYTHON_CMD% run.py --desktop >> waverider-desktop.bat

echo [OK] Launcher scripts created
echo.

:create_shortcut
echo.
set /p CREATE_SHORTCUT="Would you like to create a desktop shortcut? (y/n): "
if /i "%CREATE_SHORTCUT%"=="y" (
    echo.
    echo [*] Creating desktop shortcut...
    
    REM Create VBS script to make shortcut
    echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
    echo sLinkFile = oWS.ExpandEnvironmentStrings("%%USERPROFILE%%\Desktop\WaveRider SDR.lnk") >> "%TEMP%\create_shortcut.vbs"
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
    echo oLink.TargetPath = "%CD%\waverider.bat" >> "%TEMP%\create_shortcut.vbs"
    echo oLink.WorkingDirectory = "%CD%" >> "%TEMP%\create_shortcut.vbs"
    echo oLink.Description = "WaveRider SDR - Universal Cross-Platform Application" >> "%TEMP%\create_shortcut.vbs"
    echo oLink.Save >> "%TEMP%\create_shortcut.vbs"
    
    cscript //nologo "%TEMP%\create_shortcut.vbs"
    del "%TEMP%\create_shortcut.vbs"
    
    echo [OK] Desktop shortcut created
)

:configure_firewall
echo.
if "%IS_ADMIN%"=="1" (
    set /p CONFIG_FIREWALL="Would you like to configure Windows Firewall for local network mobile access (restricted to local subnet)? (y/n): "
    if /i "!CONFIG_FIREWALL!"=="y" (
        echo.
        echo [*] Configuring Windows Firewall (local network only)...
        netsh advfirewall firewall add rule name="WaveRider SDR" dir=in action=allow protocol=TCP localport=5000 remoteip=localsubnet profile=private
        if %errorlevel% == 0 (
            echo [OK] Firewall rule added successfully
        ) else (
            echo [WARNING] Failed to add firewall rule
        )
    )
) else (
    echo [INFO] To configure firewall for mobile access, run this script as Administrator
)

:test_installation
echo.
echo [*] Testing installation...
%PYTHON_CMD% -c "import numpy, scipy, matplotlib" 2>nul
if %errorlevel% == 0 (
    echo [OK] Core dependencies verified
) else (
    echo [WARNING] Some dependencies may not be properly installed
)

:completion
echo.
echo ============================================================
echo.
echo      INSTALLATION COMPLETED SUCCESSFULLY!
echo.
echo ============================================================
echo.
echo Quick Start:
echo.
echo   1. Run WaveRider SDR:
echo      waverider.bat
echo      or: %PYTHON_CMD% run.py
echo.
echo   2. For web version (access from mobile):
echo      waverider-web.bat
echo      or: %PYTHON_CMD% run.py --web
echo.
echo   3. For desktop GUI version:
echo      waverider-desktop.bat
echo      or: %PYTHON_CMD% run.py --desktop
echo.
echo Documentation:
echo   * README.md - Full documentation
echo   * PLATFORM_GUIDE.md - Platform-specific guides
echo.
echo Need help?
echo   * GitHub: https://github.com/1090mb/WaveRiderSDR
echo.
echo ============================================================
echo.
pause
