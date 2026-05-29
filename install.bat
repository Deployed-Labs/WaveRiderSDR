@echo off
REM WaveRider SDR MSI build helper for Windows

setlocal

echo ===========================================
echo WaveRider SDR MSI Build (Windows)
echo ===========================================

REM Check cargo availability
cargo --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Rust is not installed.
  echo Install from https://rustup.rs/ then re-run this script.
  exit /b 1
)

echo [OK] Rust toolchain detected

echo [*] Checking cargo-wix...
cargo wix --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [*] Installing cargo-wix...
  cargo install cargo-wix --locked
  if %errorlevel% neq 0 (
    echo [ERROR] Failed to install cargo-wix
    exit /b 1
  )
)

echo [*] Building release binary...
cargo build --release
if %errorlevel% neq 0 (
  echo [ERROR] Build failed
  exit /b 1
)

if not exist dist mkdir dist

echo [*] Building MSI installer...
cargo wix --no-build --output dist\waverider_sdr.msi
if %errorlevel% neq 0 (
  echo [ERROR] MSI build failed
  exit /b 1
)

echo [OK] MSI created: dist\waverider_sdr.msi
echo Install with: msiexec /i dist\waverider_sdr.msi

exit /b 0
