# WaveRider SDR (Python)

WaveRider SDR now runs fully in Python with a GUI-focused web dashboard and desktop launcher.

## What Is Implemented

- Universal Python launcher with mode selection
- Web SDR interface served from Flask
- Simulated IQ signal generation
- FFT + waterfall + waveform processing
- CW envelope decoding with Morse text extraction
- Band presets API and UI
- Meshtastic USB detection via serial ports (VID/product matching)
- SDR management endpoints for scan/connect/disconnect

## Project Layout

- `run.py`: universal launcher (`auto`, `web`, `desktop`)
- `waverider_web.py`: Flask app and SDR API routes
- `waverider_sdr.py`: desktop-mode launcher
- `waverider_common.py`: shared runtime state, DSP, bands, Morse decoder
- `templates/index.html`: web dashboard

## Quick Start

### 1. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Run Desktop GUI Mode

```bash
python run.py --mode desktop
```

### 3. Run Web Mode

```bash
python run.py --mode web --host 0.0.0.0 --port 5000
```

Open `http://localhost:5000` in your browser.

### Alternate launchers

- Desktop launcher: `python waverider_sdr.py`
- Web launcher: `python waverider_web.py --open-browser`

## Packaging

Python entrypoints are the runtime and packaging source of truth for this repository.

## Modes

- `--mode web`: starts the web UI server only
- `--mode desktop`: starts the local server and opens the GUI automatically in your default browser
- `--mode auto`: chooses desktop on GUI-capable hosts, otherwise web

## Status

- Python runtime restored for launcher, DSP engine, and web interface.
- Hardware tool detection for RTL-SDR/HackRF is implemented (PATH/tool based).
- Direct IQ capture is available when Python bindings are installed:
	- RTL-SDR: `pyrtlsdr`
	- HackRF: `SoapySDR` Python bindings
- Without those bindings, signal processing runs on simulated samples with graceful fallback.

## Device APIs

- `GET /api/sdr_devices`: returns detected SDR tool-backed devices and current connection id
- `POST /api/connect_sdr` with `{ "device_id": "..." }`: marks selected SDR device as active source
- `POST /api/disconnect_sdr`: clears active SDR source
- `GET /api/status`: includes source label, Meshtastic devices, SDR devices, and signal telemetry

