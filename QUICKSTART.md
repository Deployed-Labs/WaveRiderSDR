# Quickstart (Rust)

## Prerequisites

- Rust toolchain installed via rustup

## Windows (Release)

1. Download and run the MSI from Releases.
2. Launch WaveRiderSDR from the desktop shortcut.

## Run

```bash
cargo run --release -- --mode web
```

Then open:

- http://localhost:5000

## Alternate Commands

```bash
cargo build --release
```

Windows binary:

```powershell
.\target\release\waverider_sdr.exe --mode web
```

Linux/macOS binary:

```bash
./target/release/waverider_sdr --mode web
```

