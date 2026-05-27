"""
Legacy compatibility launcher.
WaveRider SDR is now implemented in Rust.
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).parent
    cargo_toml = repo / "Cargo.toml"
    if not cargo_toml.exists():
        print("Cargo.toml not found. The Rust project is missing.")
        return 1

    args = ["cargo", "run", "--release", "--"] + sys.argv[1:]
    try:
        return subprocess.call(args, cwd=str(repo))
    except FileNotFoundError:
        print("Rust toolchain is not installed. Install rustup from https://rustup.rs/")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

