"""Python web server and GUI API for WaveRider SDR."""

from __future__ import annotations

import argparse
import threading
import time
import webbrowser

from flask import Flask, jsonify, render_template, request

from waverider_common import AppState, bands_as_dicts


def create_app(state: AppState) -> Flask:
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
        return jsonify({"ok": True})

    @app.post("/api/stop")
    def api_stop():
        with state.lock:
            state.stop()
        return jsonify({"ok": True})

    @app.post("/api/config")
    def api_config():
        payload = request.get_json(silent=True) or {}
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
        payload = request.get_json(silent=True) or {}
        band_name = str(payload.get("band", ""))
        with state.lock:
            ok = state.set_band(band_name)
            status = state.get_status()
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
        payload = request.get_json(silent=True) or {}
        device_id = str(payload.get("device_id", ""))
        with state.lock:
            ok = state.sdr.connect(device_id)
        code = 200 if ok else 404
        return jsonify({"ok": ok}), code

    @app.post("/api/disconnect_sdr")
    def api_disconnect_sdr():
        with state.lock:
            state.sdr.disconnect()
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
    state = AppState()
    app = create_app(state)

    stop_event = threading.Event()
    tick_thread = threading.Thread(target=_run_tick_loop, args=(state, stop_event), daemon=True)
    tick_thread.start()

    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{browser_host}:{port}"

    if open_browser:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        print(f"WaveRider SDR Python web server running at {url}")
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

