# WaveRider SDR (Rust)

WaveRider SDR has been migrated from Python to Rust.

## What Is Implemented

- Universal Rust launcher with mode selection
- Web SDR interface served from Rust using Axum
- Simulated IQ signal generation
- FFT + waterfall + waveform processing
- CW envelope decoding with Morse text extraction
- Band presets API and UI
- Meshtastic USB detection via serial ports (VID/product matching)
- SDR management endpoints for scan/connect/disconnect

## Project Layout

- `src/main.rs`: launcher and mode selection
- `src/web.rs`: HTTP server and SDR API routes
- `src/state.rs`: shared runtime state and update tick
- `src/dsp.rs`: signal generator, FFT, demod basics
- `src/morse.rs`: Morse decoder
- `src/band_plan.rs`: frequency band definitions
- `src/common.rs`: waterfall settings and hardware placeholders
	Device detection and SDR connection state management
- `templates/index.html`: web dashboard

## Quick Start

### 1. Install Rust

Use rustup: https://rustup.rs/

### 2. Build

```bash
cargo build --release
```

### 3. Run Web Interface

```bash
cargo run --release -- --mode web --host 0.0.0.0 --port 5000
```

Open http://localhost:5000 in your browser.

### 4. Run Executable (GUI or Web)

After building, run the executable directly:

```bash
target/release/waverider_sdr --mode desktop
```

On Windows:

```powershell
.\target\release\waverider_sdr.exe --mode desktop
```

For web-only mode with explicit host/port:

```powershell
.\target\release\waverider_sdr.exe --mode web --host 0.0.0.0 --port 5000
```

## Portable ZIP Releases (Windows)

GitHub Actions now builds a portable Windows ZIP on every push to `main` and every `v*` tag.

- Main branch artifacts: downloadable from the workflow run artifacts
- Tag builds: attached to the GitHub Release

Each portable ZIP includes:

- `waverider_sdr.exe`
- `templates/`
- `run-gui.bat` (starts GUI mode)
- `run-web.bat` (starts web mode, optional port argument)
- `README.md` and `LICENSE`

## Modes

- `--mode web`: starts the web UI server only
- `--mode desktop`: starts the local server and opens the GUI automatically in your default browser
- `--mode auto`: chooses desktop on GUI-capable hosts, otherwise web

## Compatibility Notes

Legacy Python files remain only as compatibility shims and no longer contain SDR logic.

## Status

- Rust migration complete for launcher, shared DSP engine, and web interface.
- Hardware tool detection for RTL-SDR/HackRF is implemented (PATH/tool based).
- Direct IQ capture backends for RTL-SDR/HackRF are still pending; signal processing currently runs on simulated samples.

## Device APIs

- `GET /api/sdr_devices`: returns detected SDR tool-backed devices and current connection id
- `POST /api/connect_sdr` with `{ "device_id": "..." }`: marks selected SDR device as active source
- `POST /api/disconnect_sdr`: clears active SDR source
- `GET /api/status`: includes source label, Meshtastic devices, SDR devices, and signal telemetry

