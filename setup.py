"""
Legacy setup.py retained for compatibility only.
WaveRider SDR is now packaged via Cargo.
"""

if __name__ == "__main__":
    print("WaveRider SDR is now a Rust project.")
    print("Build with: cargo build --release")
    print("Run with: cargo run --release -- --mode web")
    raise SystemExit(0)

