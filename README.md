# WaveRider SDR (Rust)

WaveRider SDR has been migrated from Python to Rust.

## What Is Implemented

- Universal Rust launcher with mode selection
- Web SDR interface served from Rust using Axum
- Simulated IQ signal generation
- FFT + waterfall + waveform processing
- CW envelope decoding with Morse text extraction
- Band presets API and UI

## Project Layout

- `src/main.rs`: launcher and mode selection
- `src/web.rs`: HTTP server and SDR API routes
- `src/state.rs`: shared runtime state and update tick
- `src/dsp.rs`: signal generator, FFT, demod basics
- `src/morse.rs`: Morse decoder
- `src/band_plan.rs`: frequency band definitions
- `src/common.rs`: waterfall settings and hardware placeholders
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

## Modes

- `--mode web`: starts the web UI server
- `--mode desktop`: reserved placeholder for native desktop UI
- `--mode auto`: chooses desktop on GUI-capable hosts, otherwise web

## Compatibility Notes

Legacy Python files remain only as compatibility shims and no longer contain SDR logic.

## Status

- Rust migration complete for launcher, shared DSP engine, and web interface.
- Hardware SDR backends (RTL-SDR/HackRF) are currently placeholders in Rust and can be added behind feature flags in a follow-up.

