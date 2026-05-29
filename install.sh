#!/bin/bash
# WaveRider SDR Python installer for Linux and macOS

set -e

echo "==========================================="
echo "WaveRider SDR Python Setup"
echo "==========================================="

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] Python 3 is not installed."
  echo "Install Python 3.10+ and re-run this script."
  exit 1
fi

echo "[OK] Python detected"
echo "[*] Installing Python dependencies..."
python3 -m pip install -r requirements.txt
echo "[*] Verifying Python modules..."
python3 -m py_compile run.py waverider_common.py waverider_web.py waverider_sdr.py
echo "[OK] Setup complete"
echo "Run with: python3 run.py --mode desktop"
