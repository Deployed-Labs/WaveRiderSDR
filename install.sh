#!/bin/bash
# WaveRider SDR Rust installer for Linux and macOS

set -e

echo "==========================================="
echo "WaveRider SDR Rust Installation"
echo "==========================================="

if ! command -v cargo >/dev/null 2>&1; then
  echo "[ERROR] Rust is not installed."
  echo "Install rustup from https://rustup.rs/"
  exit 1
fi

echo "[OK] Rust toolchain detected"
echo "[*] Building release binary..."
cargo build --release
echo "[OK] Build complete"
echo "Run with: ./target/release/waverider_sdr --mode web"
echo "or: cargo run --release -- --mode web"
