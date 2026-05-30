"""Python web server and GUI API for WaveRider SDR."""

from __future__ import annotations

import argparse
import threading
import time
import webbrowser
from collections import deque
from datetime import datetime
from typing import Any, cast

from flask import Flask, jsonify, render_template, request

from waverider_common import AppState, bands_as_dicts, run_startup_preflight


class LogManager:
    """Simple in-memory log manager."""
    def __init__(self, max_logs: int = 100):
        self.logs: deque[dict[str, str]] = deque(maxlen=max_logs)
        self.lock = threading.Lock()
    
    def add(self, level: str, message: str) -> None:
        with self.lock:
            self.logs.appendleft({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": level.lower(),
                "message": message
            })
    
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
        return jsonify({"ok": True})

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


def _run_tick_loop(state: AppState, stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        with state.lock:
            if state.running:
                state.tick()
        time.sleep(0.08)


def run_web(host: str = "0.0.0.0", port: int = 5000, open_browser: bool = False) -> int:
    preflight = run_startup_preflight(auto_install=True)
    print(preflight.summary())
    for warning in preflight.warnings:
        print(f"[startup] {warning}")

    logs = LogManager()
    logs.add("info", "WaveRider SDR initialized")
    
    state = AppState()
    if preflight.short_notice():
        state.source_notice = preflight.short_notice()
        logs.add("warning", f"Startup notice: {preflight.short_notice()}")
    
    app = create_app(state, logs)

    stop_event = threading.Event()
    tick_thread = threading.Thread(target=_run_tick_loop, args=(state, stop_event), daemon=True)
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

