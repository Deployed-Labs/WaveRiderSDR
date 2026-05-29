# WaveRider SDR Rust installer for Windows PowerShell
#Requires -Version 5.0

Write-Host "==========================================="
Write-Host "WaveRider SDR MSI Build (Windows)"
Write-Host "==========================================="

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Rust is not installed." -ForegroundColor Red
    Write-Host "Install rustup from https://rustup.rs/" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Rust toolchain detected" -ForegroundColor Green

Write-Host "[*] Checking cargo-wix..." -ForegroundColor Cyan
cargo wix --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[*] Installing cargo-wix..." -ForegroundColor Cyan
    cargo install cargo-wix --locked
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install cargo-wix" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[*] Building release binary..." -ForegroundColor Cyan
cargo build --release
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path dist)) {
    New-Item -ItemType Directory -Path dist | Out-Null
}

$msiPath = Join-Path (Get-Location) "dist\\waverider_sdr.msi"
Write-Host "[*] Building MSI installer..." -ForegroundColor Cyan
cargo wix --no-build --output $msiPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] MSI build failed" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] MSI created: $msiPath" -ForegroundColor Green
Write-Host "Install with: msiexec /i $msiPath"
