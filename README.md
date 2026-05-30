# WaveRider SDR (Python)

WaveRider SDR now runs fully in Python with a GUI-focused web dashboard and desktop launcher.

## Quick Start (Windows)

1. Download and extract this repository.
2. Install dependencies:

```bat
python -m pip install -r requirements.txt
```

3. Launch the native desktop GUI:

```bat
launch_gui.bat
```

## What Is Implemented

- Universal Python launcher with mode selection
- Web SDR interface served from Flask with modern UI
- **Dark mode** toggle for comfortable night operation
- **Band preset search** with real-time filtering
- Simulated IQ signal generation
- FFT + waterfall + waveform processing
- CW envelope decoding with Morse text extraction
- Band presets API and UI with center frequency tuning
- Meshtastic USB detection via serial ports (VID/product matching)
- SDR management endpoints for scan/connect/disconnect
- **Connection status indicator** showing active SDR device
- **Log message display** with filtering (debug, info, warning, error)
- **Input validation** with error messages for invalid settings
- **Server-side logging** to persistent files with automatic rotation
- **Sample rate presets** optimized for common SDR hardware

## Project Layout

- `run.py`: universal launcher (`auto`, `web`, `desktop`)
- `waverider_web.py`: Flask app and SDR API routes
- `waverider_sdr.py`: desktop-mode launcher
- `waverider_tk_gui.py`: native Tkinter desktop window frontend
- `waverider_common.py`: shared runtime state, DSP, bands, Morse decoder
- `launch.bat`: Windows launcher (passes arguments to `run.py`)
- `launch_gui.bat`: Windows native GUI launcher (Tkinter)
- `templates/index.html`: web dashboard with modern UI
- `logs/`: server-side log files (auto-created on first run)

## Web Interface Features

The modern web dashboard includes:

- **Theme Toggle**: Dark mode (default) or light mode, saved to browser
- **Band Search**: Real-time search through 40+ frequency bands
- **Center Tuner**: One-click button to jump to selected band's center frequency
- **Connection Status**: Live display of active SDR device, sample rate, and frequency
- **Log Viewer**: Filterable message display (all, debug, info, warning, error)
- **Input Validation**: Errors displayed immediately for invalid frequency/sample rate/FFT size
- **Sample Rate Presets**: 2.4M, 2.048M, 1.2M, 1.024M, 960k, 500k
- **Auto-rotating Logs**: Server writes to persistent log files with automatic rotation at 5MB

## Download

### Option 1: Download ZIP (easiest)

1. Open the repository page: https://github.com/Deployed-Labs/WaveRiderSDR
2. Select **Code**.
3. Select **Download ZIP**.
4. Extract the ZIP to a folder, for example `F:\WaveRiderSDR`.

### Option 2: Clone with Git

```bash
git clone https://github.com/Deployed-Labs/WaveRiderSDR.git
cd WaveRiderSDR
```

## Install

Install Python 3.10+ first, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Operating

### Native desktop window (recommended on Windows)

Starts the program in its own Tkinter window.

```bat
launch_gui.bat
```

### Desktop browser mode

Starts the local server and opens your browser automatically.

```bat
launch.bat
```

### Web mode (manual open)

Starts the server without auto-opening the browser.

```bash
python run.py --mode web --host 0.0.0.0 --port 5000
```

Then open `http://localhost:5000` in your browser.

### CLI launch alternatives

```bash
python run.py --mode desktop
python waverider_sdr.py
python waverider_web.py --open-browser
```

### Basic operation flow

1. Start the app with one of the launch options above.
2. Choose a band preset or set frequency manually.
3. Select sample rate, FFT size, and modulation mode.
4. Press **Start** to begin signal updates.
5. Watch spectrum/waterfall and status telemetry.
6. Use **Stop** to pause processing.
7. Close the window or stop the terminal process to exit.

### Optional SDR hardware support

For live hardware capture, install optional Python packages:

```bash
pip install pyrtlsdr
# HackRF path requires SoapySDR Python bindings installed for your platform
```

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

