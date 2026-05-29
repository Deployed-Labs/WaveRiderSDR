# WaveRider SDR Python installer for Windows PowerShell
#Requires -Version 5.0

Write-Host "==========================================="
Write-Host "WaveRider SDR Python Setup (Windows)"
Write-Host "==========================================="

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed." -ForegroundColor Red
    Write-Host "Install Python 3.10+ and re-run this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Python detected" -ForegroundColor Green

Write-Host "[*] Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Dependency installation failed" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Verifying Python modules..." -ForegroundColor Cyan
python -m py_compile run.py waverider_common.py waverider_web.py waverider_sdr.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python module validation failed" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Setup complete" -ForegroundColor Green
Write-Host "Run with: python run.py --mode desktop"
