"""Python web server and GUI API for WaveRider SDR."""

from __future__ import annotations

import argparse
import os
import threading
import time
import webbrowser
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from flask import Flask, jsonify, render_template, request

from waverider_common import AppState, bands_as_dicts, run_startup_preflight


class SDRAutoReconnect:
    """Handles automatic reconnection to SDR devices."""
    def __init__(self, logs: LogManager):
        self.logs = logs
        self.last_connected_device_id: str | None = None
        self.was_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.lock = threading.Lock()
    
    def update(self, state: AppState) -> None:
        """Check connection status and attempt reconnect if needed."""
        with self.lock:
            is_connected = state.sdr.is_connected
            connected_device = state.sdr.connected_device
            
            # Track successful connections
            if is_connected and connected_device:
                device_id = connected_device.get("id")
                if device_id and device_id != self.last_connected_device_id:
                    self.last_connected_device_id = device_id
                    self.was_connected = True
                    self.reconnect_attempts = 0
                    self.logs.add("info", f"SDR connected: {device_id}")
            
            # Detect disconnection
            elif self.was_connected and not is_connected:
                self.was_connected = False
                if self.last_connected_device_id:
                    self.reconnect_attempts = 0
                    self.logs.add("warning", f"SDR disconnected: {self.last_connected_device_id}")
            
            # Attempt reconnection
            elif not is_connected and self.last_connected_device_id and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                self.logs.add("info", f"Reconnecting to {self.last_connected_device_id} (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                state.sdr.connect(self.last_connected_device_id)
    
    def reset(self) -> None:
        """Clear auto-reconnect state."""
        with self.lock:
            self.last_connected_device_id = None
            self.was_connected = False
            self.reconnect_attempts = 0
    """In-memory + file-based log manager with rotation."""
    def __init__(self, max_logs: int = 100, log_dir: str = "logs"):
        self.logs: deque[dict[str, str]] = deque(maxlen=max_logs)
        self.lock = threading.Lock()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "waverider.log"
        self.max_file_size = 5 * 1024 * 1024  # 5 MB rotation threshold
        self._rotate_if_needed()
    
    def _rotate_if_needed(self) -> None:
        """Rotate log file if it exceeds max_file_size."""
        if self.log_file.exists() and self.log_file.stat().st_size > self.max_file_size:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.log_dir / f"waverider_{timestamp}.log"
            self.log_file.rename(backup)
    
    def add(self, level: str, message: str) -> None:
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": level.lower(),
                "message": message
            }
            self.logs.appendleft(log_entry)
            
            # Write to file
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] {level.upper():8} | {message}\n")
                self._rotate_if_needed()
            except Exception:
                pass  # Silently fail if logging fails
    
    def get_all(self) -> list[dict[str, str]]:
        with self.lock:
            return list(self.logs)
    
    def clear(self) -> None:
        with self.lock:
            self.logs.clear()


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return cast(dict[str, Any], payload)
    return {}


def _validate_frequency(freq_mhz: Any) -> tuple[bool, str]:
    """Validate frequency is within reasonable range."""
    try:
        f = float(freq_mhz)
        if f < 0.1 or f > 6000:
            return False, "Frequency must be between 0.1 and 6000 MHz"
        return True, ""
    except (TypeError, ValueError):
        return False, "Frequency must be a number"


def _validate_sample_rate(rate_hz: Any) -> tuple[bool, str]:
    """Validate sample rate is within reasonable range."""
    try:
        r = int(rate_hz)
        valid_rates = {500000, 960000, 1024000, 1200000, 2048000, 2400000}
        if r not in valid_rates:
            return False, f"Sample rate must be one of: {sorted(valid_rates)}"
        return True, ""
    except (TypeError, ValueError):
        return False, "Sample rate must be an integer"


def _validate_fft_size(size: Any) -> tuple[bool, str]:
    """Validate FFT size is power of 2 and reasonable."""
    try:
        s = int(size)
        if s < 256 or s > 8192:
            return False, "FFT size must be between 256 and 8192"
        # Check if power of 2
        if s & (s - 1) != 0:
            return False, "FFT size must be a power of 2 (256, 512, 1024, 2048, 4096, 8192)"
        return True, ""
    except (TypeError, ValueError):
        return False, "FFT size must be an integer"


def create_app(state: AppState, logs: LogManager) -> Flask:
    app = Flask(__name__, template_folder="templates")

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/frame")
    def api_frame():
        with state.lock:
            return jsonify(state.get_frame())

    @app.get("/api/status")
    def api_status():
        with state.lock:
            return jsonify(state.get_status())

    @app.post("/api/start")
    def api_start():
        with state.lock:
            state.start()
        logs.add("info", "SDR started")
        return jsonify({"ok": True})

    @app.post("/api/stop")
    def api_stop():
        with state.lock:
            state.stop()
        logs.add("info", "SDR stopped")
        return jsonify({"ok": True})

    @app.post("/api/config")
    def api_config():
        payload = _json_payload()
        
        # Validate frequency if provided
        if "frequency_mhz" in payload and payload["frequency_mhz"] is not None:
            valid, error = _validate_frequency(payload["frequency_mhz"])
            if not valid:
                logs.add("error", f"Config validation failed: {error}")
                return jsonify({"ok": False, "error": error}), 400
        
        # Validate sample rate if provided
        if "sample_rate_hz" in payload and payload["sample_rate_hz"] is not None:
            valid, error = _validate_sample_rate(payload["sample_rate_hz"])
            if not valid:
                logs.add("error", f"Config validation failed: {error}")
                return jsonify({"ok": False, "error": error}), 400
        
        # Validate FFT size if provided
        if "fft_size" in payload and payload["fft_size"] is not None:
            valid, error = _validate_fft_size(payload["fft_size"])
            if not valid:
                logs.add("error", f"Config validation failed: {error}")
                return jsonify({"ok": False, "error": error}), 400
        
        try:
            with state.lock:
                state.configure(
                    frequency_mhz=payload.get("frequency_mhz"),
                    sample_rate_hz=payload.get("sample_rate_hz"),
                    fft_size=payload.get("fft_size"),
                    modulation_mode=payload.get("modulation_mode"),
                    min_db=payload.get("min_db"),
                    max_db=payload.get("max_db"),
                    squelch_db=payload.get("squelch_db"),
                    morse_enabled=payload.get("morse_enabled"),
                )
            logs.add("debug", "Config updated")
            return jsonify({"ok": True})
        except Exception as e:
            error_msg = str(e)
            logs.add("error", f"Config error: {error_msg}")
            return jsonify({"ok": False, "error": error_msg}), 500

    @app.get("/api/bands")
    def api_bands():
        return jsonify(bands_as_dicts())

    @app.post("/api/set_band")
    def api_set_band():
        payload = _json_payload()
        band_name = str(payload.get("band", ""))
        with state.lock:
            ok = state.set_band(band_name)
            status = state.get_status()
        logs.add("info" if ok else "warning", f"Set band: {band_name}")
        code = 200 if ok else 404
        return jsonify({"ok": ok, "status": status}), code

    @app.get("/api/sdr_devices")
    def api_sdr_devices():
        with state.lock:
            devices = state.sdr.detect_devices()
            connected = None
            if state.sdr.connected_device:
                connected = state.sdr.connected_device.get("id")
        return jsonify({"devices": devices, "connected_sdr_id": connected})

    @app.post("/api/connect_sdr")
    def api_connect_sdr():
        payload = _json_payload()
        device_id = str(payload.get("device_id", ""))
        with state.lock:
            ok = state.sdr.connect(device_id)
        logs.add("info" if ok else "error", f"Connect SDR: {device_id}")
        code = 200 if ok else 404
        return jsonify({"ok": ok}), code

    @app.post("/api/disconnect_sdr")
    def api_disconnect_sdr():
        with state.lock:
            state.sdr.disconnect()
        logs.add("info", "SDR disconnected")
        return jsonify({"ok": True})

    @app.get("/api/logs")
    def api_logs():
        return jsonify(logs.get_all())

    @app.post("/api/logs/clear")
    def api_logs_clear():
        logs.clear()
        return jsonify({"ok": True})

    @app.get("/api/diagnostics")
    def api_diagnostics():
        with state.lock:
            return jsonify({
                "sdr": state.sdr.diagnostics(),
                "running": state.running,
                "sample_rate": state.sample_rate,
                "center_freq": state.center_freq,
            })

    return app


def _run_tick_loop(state: AppState, stop_event: threading.Event, auto_reconnect: SDRAutoReconnect) -> None:
    while not stop_event.is_set():
        with state.lock:
            if state.running:
                state.tick()
            # Check for SDR disconnection and attempt reconnect
            auto_reconnect.update(state)
        time.sleep(0.08)


def run_web(host: str = "0.0.0.0", port: int = 5000, open_browser: bool = False) -> int:
    preflight = run_startup_preflight(auto_install=True)
    print(preflight.summary())
    for warning in preflight.warnings:
        print(f"[startup] {warning}")

    logs = LogManager()
    logs.add("info", "WaveRider SDR initialized")
    
    state = AppState()
    auto_reconnect = SDRAutoReconnect(logs)
    
    if preflight.short_notice():
        state.source_notice = preflight.short_notice()
        logs.add("warning", f"Startup notice: {preflight.short_notice()}")
    
    app = create_app(state, logs)

    stop_event = threading.Event()
    tick_thread = threading.Thread(target=_run_tick_loop, args=(state, stop_event, auto_reconnect), daemon=True)
    tick_thread.start()

    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{browser_host}:{port}"

    if open_browser:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        print(f"WaveRider SDR Python web server running at {url}")
        logs.add("info", f"Server running at {url}")
        app.run(host=host, port=port, threaded=True, use_reloader=False)
        return 0
    finally:
        stop_event.set()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WaveRider SDR Python web server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--open-browser", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    return run_web(host=args.host, port=args.port, open_browser=args.open_browser)


if __name__ == "__main__":
    raise SystemExit(main())

