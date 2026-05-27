@echo off
REM WaveRider SDR Rust installer for Windows

setlocal

echo ===========================================
echo WaveRider SDR Rust Installation (Windows)
echo ===========================================

REM Check cargo availability
cargo --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] Rust is not installed.
  echo Install from https://rustup.rs/ then re-run this script.
  exit /b 1
)

echo [OK] Rust toolchain detected

echo [*] Building release binary...
cargo build --release
if %errorlevel% neq 0 (
  echo [ERROR] Build failed
  exit /b 1
)

echo [OK] Build complete
echo Run with: target\release\waverider_sdr.exe --mode web
echo or: cargo run --release -- --mode web

exit /b 0
