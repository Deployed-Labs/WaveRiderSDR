"""Python web server and GUI API for WaveRider SDR."""

from __future__ import annotations

import argparse
import json
import os
import socket
import threading
import time
import wave
import webbrowser
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
from flask import Flask, jsonify, render_template, request

from waverider_common import AppState, FrequencyScanner, bands_as_dicts, run_startup_preflight


class AudioRecorder:
    """Records audio samples to WAV files."""
    def __init__(self, recording_dir: str = "recordings"):
        self.recording_dir = Path(recording_dir)
        self.recording_dir.mkdir(exist_ok=True)
        self.recording = False
        self.current_file: str | None = None
        self.wav_file: wave.Wave_write | None = None
        self.sample_rate = 48000  # Resample to 48kHz for playback
        self.num_channels = 1
        self.sample_width = 2  # 16-bit
        self.samples_written = 0
        self.lock = threading.Lock()
    
    def start_recording(self) -> tuple[bool, str]:
        """Start recording audio to a new file."""
        with self.lock:
            if self.recording:
                return False, "Recording already in progress"
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.wav"
                filepath = self.recording_dir / filename
                
                self.wav_file = wave.open(str(filepath), 'wb')
                self.wav_file.setnchannels(self.num_channels)
                self.wav_file.setsampwidth(self.sample_width)
                self.wav_file.setframerate(self.sample_rate)
                
                self.recording = True
                self.current_file = filename
                self.samples_written = 0
                return True, filename
            except Exception as e:
                return False, f"Failed to start recording: {str(e)}"
    
    def stop_recording(self) -> tuple[bool, str]:
        """Stop recording and close the file."""
        with self.lock:
            if not self.recording:
                return False, "No recording in progress"
            
            try:
                if self.wav_file:
                    self.wav_file.close()
                filename = self.current_file
                self.recording = False
                self.current_file = None
                self.wav_file = None
                duration = self.samples_written / self.sample_rate
                return True, f"Recording saved: {filename} ({duration:.1f}s)"
            except Exception as e:
                return False, f"Failed to stop recording: {str(e)}"
    
    def write_samples(self, samples: np.ndarray) -> None:
        """Write audio samples to the current recording file."""
        if not self.recording or not self.wav_file:
            return
        
        try:
            # Convert complex IQ samples to 16-bit mono audio (simple magnitude)
            # In a real implementation, this would be properly demodulated audio
            if samples.dtype in (np.complex64, np.complex128):
                audio = np.abs(samples).astype(np.float32)
            else:
                audio = samples.astype(np.float32)
            
            # Normalize to 16-bit range (-32768 to 32767)
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 32767
            else:
                audio = audio * 32767
            
            # Convert to 16-bit integers
            audio_int16 = np.int16(audio)
            
            # Write to WAV file
            self.wav_file.writeframes(audio_int16.tobytes())
            self.samples_written += len(audio)
        except Exception:
            pass  # Silently fail if write fails
    
    def get_status(self) -> dict[str, Any]:
        """Get current recording status."""
        with self.lock:
            if self.recording:
                duration = self.samples_written / self.sample_rate
                file_size = (self.samples_written * self.sample_width) / (1024 * 1024)  # MB
                return {
                    "recording": True,
                    "filename": self.current_file,
                    "duration_seconds": duration,
                    "file_size_mb": file_size,
                }
            return {
                "recording": False,
                "filename": None,
                "duration_seconds": 0,
                "file_size_mb": 0,
            }


class IQRecorder:
    """Records raw I/Q samples to .cf32 binary files (complex float32).
    
    .cf32 format is compatible with GNU Radio, SDR#, and most SDR analysis tools.
    Each sample is stored as 2x float32 values: [real, imag, real, imag, ...].
    """
    def __init__(self, recording_dir: str = "recordings"):
        self.recording_dir = Path(recording_dir)
        self.recording_dir.mkdir(exist_ok=True)
        self.recording = False
        self.current_file: str | None = None
        self._file_handle: Any = None
        self.samples_written = 0
        self.sample_rate = 2_400_000  # Updated when recording starts
        self.center_freq = 0.0
        self.lock = threading.Lock()
    
    def start_recording(self, sample_rate: float, center_freq: float) -> tuple[bool, str]:
        """Start recording IQ samples to a .cf32 file."""
        with self.lock:
            if self.recording:
                return False, "IQ recording already in progress"
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                freq_mhz = center_freq / 1_000_000
                filename = f"iq_{freq_mhz:.3f}MHz_{timestamp}.cf32"
                filepath = self.recording_dir / filename
                self._file_handle = open(str(filepath), 'wb')
                self.recording = True
                self.current_file = filename
                self.samples_written = 0
                self.sample_rate = sample_rate
                self.center_freq = center_freq
                return True, filename
            except Exception as e:
                return False, f"Failed to start IQ recording: {str(e)}"
    
    def stop_recording(self) -> tuple[bool, str]:
        """Stop recording and close the file."""
        with self.lock:
            if not self.recording:
                return False, "No IQ recording in progress"
            try:
                if self._file_handle:
                    self._file_handle.close()
                filename = self.current_file
                duration = self.samples_written / max(self.sample_rate, 1)
                file_size_mb = (self.samples_written * 8) / (1024 * 1024)  # 2x float32 = 8 bytes/sample
                self.recording = False
                self.current_file = None
                self._file_handle = None
                return True, f"IQ saved: {filename} ({duration:.1f}s, {file_size_mb:.1f}MB)"
            except Exception as e:
                return False, f"Failed to stop IQ recording: {str(e)}"
    
    def write_samples(self, samples: np.ndarray) -> None:
        """Write complex IQ samples as interleaved float32 bytes."""
        if not self.recording or not self._file_handle:
            return
        try:
            if samples.dtype == np.complex64:
                iq = samples
            else:
                iq = samples.astype(np.complex64)
            # Interleave as [real, imag, real, imag, ...] float32
            interleaved = np.empty(len(iq) * 2, dtype=np.float32)
            interleaved[0::2] = np.real(iq)
            interleaved[1::2] = np.imag(iq)
            self._file_handle.write(interleaved.tobytes())
            self.samples_written += len(iq)
        except Exception:
            pass
    
    def get_status(self) -> dict[str, Any]:
        """Get current IQ recording status."""
        with self.lock:
            if self.recording:
                duration = self.samples_written / max(self.sample_rate, 1)
                file_size_mb = (self.samples_written * 8) / (1024 * 1024)
                return {
                    "recording": True,
                    "filename": self.current_file,
                    "duration_seconds": duration,
                    "file_size_mb": file_size_mb,
                    "samples_written": self.samples_written,
                    "center_freq_mhz": self.center_freq / 1_000_000,
                }
            return {
                "recording": False,
                "filename": None,
                "duration_seconds": 0,
                "file_size_mb": 0,
                "samples_written": 0,
                "center_freq_mhz": 0,
            }


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


def _validate_bandwidth(bw: Any) -> tuple[bool, str]:
    """Validate bandwidth is non-negative and within reasonable range."""
    try:
        b = float(bw)
        if b < 0:
            return False, "Bandwidth must be 0 or greater (0 = no filtering)"
        if b > 10_000_000:
            return False, "Bandwidth must not exceed 10 MHz"
        return True, ""
    except (TypeError, ValueError):
        return False, "Bandwidth must be a number"


def _validate_ppm(ppm: Any) -> tuple[bool, str]:
    """Validate PPM correction is within typical RTL-SDR range."""
    try:
        p = float(ppm)
        if p < -200 or p > 200:
            return False, "PPM correction must be between -200 and +200"
        return True, ""
    except (TypeError, ValueError):
        return False, "PPM correction must be a number"


def create_app(state: AppState, logs: LogManager, recorder: AudioRecorder, iq_recorder: IQRecorder, signal_history: SignalHistory, scanner: FrequencyScanner) -> Flask:
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

        # Validate bandwidth if provided
        if "bandwidth_hz" in payload and payload["bandwidth_hz"] is not None:
            valid, error = _validate_bandwidth(payload["bandwidth_hz"])
            if not valid:
                logs.add("error", f"Config validation failed: {error}")
                return jsonify({"ok": False, "error": error}), 400

        # Validate PPM if provided
        if "ppm_correction" in payload and payload["ppm_correction"] is not None:
            valid, error = _validate_ppm(payload["ppm_correction"])
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
                    bandwidth_hz=payload.get("bandwidth_hz"),
                    noise_blanker=payload.get("noise_blanker"),
                    noise_blanker_threshold=payload.get("noise_blanker_threshold"),
                    ppm_correction=payload.get("ppm_correction"),
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

    @app.post("/api/record/start")
    def api_record_start():
        ok, message = recorder.start_recording()
        if ok:
            logs.add("info", f"Recording started: {message}")
            return jsonify({"ok": True, "filename": message}), 200
        else:
            logs.add("warning", f"Recording start failed: {message}")
            return jsonify({"ok": False, "error": message}), 400

    @app.post("/api/record/stop")
    def api_record_stop():
        ok, message = recorder.stop_recording()
        if ok:
            logs.add("info", f"Recording stopped: {message}")
            return jsonify({"ok": True, "message": message}), 200
        else:
            logs.add("warning", f"Recording stop failed: {message}")
            return jsonify({"ok": False, "error": message}), 400

    @app.get("/api/record/status")
    def api_record_status():
        return jsonify(recorder.get_status())

    @app.post("/api/iq/start")
    def api_iq_start():
        with state.lock:
            sr = state.sample_rate
            cf = state.center_freq
        ok, message = iq_recorder.start_recording(sr, cf)
        if ok:
            logs.add("info", f"IQ recording started: {message}")
            return jsonify({"ok": True, "filename": message}), 200
        else:
            logs.add("warning", f"IQ recording start failed: {message}")
            return jsonify({"ok": False, "error": message}), 400

    @app.post("/api/iq/stop")
    def api_iq_stop():
        ok, message = iq_recorder.stop_recording()
        if ok:
            logs.add("info", f"IQ recording stopped: {message}")
            return jsonify({"ok": True, "message": message}), 200
        else:
            logs.add("warning", f"IQ recording stop failed: {message}")
            return jsonify({"ok": False, "error": message}), 400

    @app.get("/api/iq/status")
    def api_iq_status():
        return jsonify(iq_recorder.get_status())

    @app.get("/api/signal_history")
    def api_signal_history():
        return jsonify(signal_history.as_dict())

    @app.post("/api/scan/start")
    def api_scan_start():
        data = request.get_json(silent=True) or {}
        try:
            start_hz = float(data.get("start_hz", 88_000_000))
            stop_hz = float(data.get("stop_hz", 108_000_000))
            step_hz = float(data.get("step_hz", 100_000))
            dwell_ms = int(data.get("dwell_ms", 200))
            pause_on_signal = bool(data.get("pause_on_signal", True))
        except (TypeError, ValueError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        if start_hz >= stop_hz:
            return jsonify({"ok": False, "error": "start_hz must be less than stop_hz"}), 400
        if not (100_000 <= start_hz <= 6_000_000_000 and 100_000 <= stop_hz <= 6_000_000_000):
            return jsonify({"ok": False, "error": "Frequency out of range"}), 400
        if not (10 <= dwell_ms <= 10_000):
            return jsonify({"ok": False, "error": "dwell_ms must be 10–10000"}), 400
        if not (1_000 <= step_hz <= 100_000_000):
            return jsonify({"ok": False, "error": "step_hz must be 1 kHz – 100 MHz"}), 400
        scanner.start(start_hz, stop_hz, step_hz, dwell_ms, pause_on_signal)
        logs.add("info", f"Scan started: {start_hz/1e6:.3f}–{stop_hz/1e6:.3f} MHz, step {step_hz/1e3:.1f} kHz")
        return jsonify({"ok": True}), 200

    @app.post("/api/scan/stop")
    def api_scan_stop():
        scanner.stop()
        logs.add("info", "Scan stopped")
        return jsonify({"ok": True}), 200

    @app.get("/api/scan/status")
    def api_scan_status():
        return jsonify(scanner.get_status())

    return app


class SignalHistory:
    """Rolling buffer of (timestamp, signal_db) samples for the sparkline chart."""

    MAX_POINTS = 300  # ~24 seconds at 12.5 Hz tick rate

    def __init__(self) -> None:
        self._buf: deque[tuple[float, float]] = deque(maxlen=self.MAX_POINTS)
        self._lock = threading.Lock()

    def push(self, signal_db: float) -> None:
        with self._lock:
            self._buf.append((time.time(), signal_db))

    def as_dict(self) -> dict[str, object]:
        with self._lock:
            points = list(self._buf)
        if not points:
            return {"history": [], "max_points": self.MAX_POINTS}
        t0 = points[0][0]
        return {
            "history": [[round(t - t0, 2), round(db, 1)] for t, db in points],
            "max_points": self.MAX_POINTS,
        }
    """GQRX-compatible TCP remote control server (default port 7356).

    Supported commands (case-insensitive):
      F           — get center frequency (Hz)
      F <hz>      — set center frequency
      M           — get modulation mode
      M <mode>    — set mode (AM/FM/USB/LSB/CW)
      L SQUELCH   — get squelch level (dB)
      L SQUELCH <db> — set squelch level
      P           — get PPM correction
      P <ppm>     — set PPM correction
      R / STATUS  — get full JSON status
      Q / QUIT    — close connection
    """

    DEFAULT_PORT = 7356

    def __init__(self, state: AppState, logs: "LogManager") -> None:
        self._state = state
        self._logs = logs
        self._server_sock: socket.socket | None = None
        self._stop_event = threading.Event()

    def start(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
        self._stop_event.clear()
        t = threading.Thread(target=self._serve, args=(host, port), daemon=True)
        t.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass

    def _serve(self, host: str, port: int) -> None:
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((host, port))
            srv.listen(5)
            srv.settimeout(1.0)
            self._server_sock = srv
            self._logs.add("info", f"TCP control server listening on {host}:{port}")
            while not self._stop_event.is_set():
                try:
                    conn, addr = srv.accept()
                except socket.timeout:
                    continue
                ct = threading.Thread(
                    target=self._handle_client, args=(conn, addr), daemon=True
                )
                ct.start()
        except OSError as exc:
            self._logs.add("warning", f"TCP control server failed to start: {exc}")
        finally:
            if self._server_sock:
                self._server_sock.close()

    def _handle_client(self, conn: socket.socket, addr: tuple) -> None:
        self._logs.add("info", f"TCP control: connection from {addr[0]}:{addr[1]}")
        try:
            conn.settimeout(60.0)
            buf = ""
            while not self._stop_event.is_set():
                try:
                    data = conn.recv(256)
                except socket.timeout:
                    continue
                if not data:
                    break
                buf += data.decode("ascii", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    resp = self._dispatch(line)
                    if resp is None:  # QUIT command
                        conn.sendall(b"RPRT 0\n")
                        return
                    conn.sendall((resp + "\n").encode())
        except (OSError, ConnectionResetError):
            pass
        finally:
            conn.close()
            self._logs.add("info", f"TCP control: {addr[0]}:{addr[1]} disconnected")

    def _dispatch(self, line: str) -> str | None:
        """Parse one command line. Returns response string, or None to close."""
        parts = line.split()
        if not parts:
            return "RPRT 0"
        cmd = parts[0].upper()
        state = self._state

        if cmd in ("Q", "QUIT"):
            return None

        # Frequency
        if cmd == "F":
            if len(parts) == 1:
                with state.lock:
                    return str(int(state.center_freq))
            try:
                freq = int(float(parts[1]))
                if not (100_000 <= freq <= 6_000_000_000):
                    return "RPRT -8"
                with state.lock:
                    state.center_freq = float(freq)
                    state.generator.center_freq = float(freq)
                self._logs.add("info", f"TCP control: frequency → {freq} Hz")
                return "RPRT 0"
            except (ValueError, IndexError):
                return "RPRT -8"

        # Mode
        if cmd == "M":
            if len(parts) == 1:
                with state.lock:
                    return state.modulation_mode
            mode = parts[1].upper()
            if mode == "NFM":
                mode = "FM"
            valid = {"AM", "FM", "USB", "LSB", "CW", "NONE"}
            if mode not in valid:
                return "RPRT -8"
            with state.lock:
                state.modulation_mode = mode
            self._logs.add("info", f"TCP control: mode → {mode}")
            return "RPRT 0"

        # Squelch (GQRX: L SQUELCH / L SQUELCH <db>)
        if cmd == "L":
            if len(parts) >= 2 and parts[1].upper() == "SQUELCH":
                if len(parts) == 2:
                    with state.lock:
                        return str(state.demodulator.squelch_db)
                try:
                    db = max(-120.0, min(0.0, float(parts[2])))
                    with state.lock:
                        state.demodulator.set_squelch(db)
                    return "RPRT 0"
                except (ValueError, IndexError):
                    return "RPRT -8"
            return "RPRT -8"

        # PPM correction
        if cmd == "P":
            if len(parts) == 1:
                with state.lock:
                    return str(state.ppm_correction)
            try:
                ppm = max(-200.0, min(200.0, float(parts[1])))
                with state.lock:
                    state.ppm_correction = ppm
                return "RPRT 0"
            except (ValueError, IndexError):
                return "RPRT -8"

        # Full JSON status
        if cmd in ("R", "STATUS"):
            with state.lock:
                st = state.get_status()
            return json.dumps(st)

        return "RPRT -8"


def _run_tick_loop(state: AppState, stop_event: threading.Event, auto_reconnect: SDRAutoReconnect, recorder: AudioRecorder, iq_recorder: IQRecorder, signal_history: SignalHistory, scanner: FrequencyScanner) -> None:
    while not stop_event.is_set():
        with state.lock:
            if state.running:
                scanner.update(state)
                state.tick()
                # Write audio samples to WAV recording if active
                if recorder.recording and state.waveform_data is not None:
                    recorder.write_samples(state.waveform_data)
                # Write raw IQ samples if IQ recording is active
                if iq_recorder.recording and state.raw_samples is not None:
                    iq_recorder.write_samples(state.raw_samples)
            signal_history.push(state.signal_strength_db)
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
    
    recorder = AudioRecorder()
    logs.add("info", "Audio recorder initialized")

    iq_recorder = IQRecorder()
    logs.add("info", "IQ recorder initialized")

    state = AppState()
    auto_reconnect = SDRAutoReconnect(logs)
    tcp_control = TCPControlServer(state, logs)
    signal_history = SignalHistory()
    scanner = FrequencyScanner()
    
    if preflight.short_notice():
        state.source_notice = preflight.short_notice()
        logs.add("warning", f"Startup notice: {preflight.short_notice()}")

    app = create_app(state, logs, recorder, iq_recorder, signal_history, scanner)

    stop_event = threading.Event()
    tick_thread = threading.Thread(target=_run_tick_loop, args=(state, stop_event, auto_reconnect, recorder, iq_recorder, signal_history, scanner), daemon=True)
    tick_thread.start()
    tcp_control.start(host="127.0.0.1", port=TCPControlServer.DEFAULT_PORT)

    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{browser_host}:{port}"

    if open_browser:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        print(f"WaveRider SDR Python web server running at {url}")
        print(f"TCP remote control on 127.0.0.1:{TCPControlServer.DEFAULT_PORT} (GQRX protocol)")
        logs.add("info", f"Server running at {url}")
        app.run(host=host, port=port, threaded=True, use_reloader=False)
        return 0
    finally:
        stop_event.set()
        tcp_control.stop()


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

