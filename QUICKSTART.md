# Quickstart (Rust)

## Prerequisites

- Rust toolchain installed via rustup

## Windows (Release)

1. Download the latest MSI:
	https://github.com/Deployed-Labs/WaveRiderSDR/releases/latest/download/WaveRiderSDR-windows-x64.msi
2. Run the MSI installer.
3. Launch WaveRiderSDR from the desktop shortcut.

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

