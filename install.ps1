# WaveRider SDR Rust installer for Windows PowerShell
#Requires -Version 5.0

Write-Host "==========================================="
Write-Host "WaveRider SDR Rust Installation (Windows)"
Write-Host "==========================================="

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Rust is not installed." -ForegroundColor Red
    Write-Host "Install rustup from https://rustup.rs/" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Rust toolchain detected" -ForegroundColor Green
Write-Host "[*] Building release binary..." -ForegroundColor Cyan
cargo build --release
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Build complete" -ForegroundColor Green
Write-Host "Run with: target\\release\\waverider_sdr.exe --mode web"
Write-Host "or: cargo run --release -- --mode web"
