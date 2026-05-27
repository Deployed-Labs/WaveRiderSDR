"""
Legacy build.py retained for compatibility only.
WaveRider SDR now builds with Cargo.
"""

import subprocess

if __name__ == "__main__":
    raise SystemExit(subprocess.call(["cargo", "build", "--release"]))

