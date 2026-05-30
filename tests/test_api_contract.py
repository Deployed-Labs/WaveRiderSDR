import unittest

from waverider_common import AppState, FrequencyScanner
from waverider_web import AudioRecorder, IQRecorder, LogManager, SignalHistory, TCPControlServer, create_app


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = AppState()
        self.logs = LogManager(max_logs=100)
        self.recorder = AudioRecorder(recording_dir="recordings_test")
        self.iq_recorder = IQRecorder(recording_dir="recordings_test")
        self.signal_history = SignalHistory()
        self.scanner = FrequencyScanner()
        self.app = create_app(
            self.state,
            self.logs,
            self.recorder,
            self.iq_recorder,
            self.signal_history,
            self.scanner,
        )
        self.client = self.app.test_client()

    def test_status_endpoint_shape(self) -> None:
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("running", payload)
        self.assertIn("center_freq", payload)
        self.assertIn("fft_size", payload)
        self.assertIn("signal_strength_db", payload)
        self.assertIn("sdr_devices", payload)

    def test_start_stop_and_config_flow(self) -> None:
        start_res = self.client.post("/api/start")
        self.assertEqual(start_res.status_code, 200)
        self.assertTrue(start_res.get_json().get("ok"))

        cfg_res = self.client.post(
            "/api/config",
            json={
                "frequency_mhz": 146.52,
                "sample_rate_hz": 1_024_000,
                "fft_size": 512,
                "modulation_mode": "FM",
                "min_db": -90,
                "max_db": -5,
                "squelch_db": -40,
                "morse_enabled": False,
            },
        )
        self.assertEqual(cfg_res.status_code, 200)
        self.assertTrue(cfg_res.get_json().get("ok"))

        status = self.client.get("/api/status").get_json()
        self.assertTrue(status["running"])
        self.assertEqual(status["fft_size"], 512)
        self.assertEqual(status["modulation_mode"], "FM")
        self.assertAlmostEqual(status["center_freq"], 146_520_000.0)

        stop_res = self.client.post("/api/stop")
        self.assertEqual(stop_res.status_code, 200)
        self.assertTrue(stop_res.get_json().get("ok"))

    def test_bands_and_set_band(self) -> None:
        bands_res = self.client.get("/api/bands")
        self.assertEqual(bands_res.status_code, 200)
        bands = bands_res.get_json()
        self.assertTrue(isinstance(bands, list) and len(bands) > 0)

        valid = self.client.post("/api/set_band", json={"band": "NOAA Weather"})
        self.assertEqual(valid.status_code, 200)
        self.assertTrue(valid.get_json().get("ok"))

        invalid = self.client.post("/api/set_band", json={"band": "Not A Real Band"})
        self.assertEqual(invalid.status_code, 404)
        self.assertFalse(invalid.get_json().get("ok"))

    def test_sdr_connect_disconnect_contract(self) -> None:
        # Force one fake SDR so API contract can be tested without hardware.
        self.state.sdr.detect_devices = lambda: [
            {
                "id": "rtl_sdr_0",
                "device_type": "RTL-SDR",
                "backend": "rtlsdr",
                "name": "RTL-SDR",
                "description": "fake",
            }
        ]
        self.state.sdr.connect = lambda device_id: device_id == "rtl_sdr_0"

        devices = self.client.get("/api/sdr_devices")
        self.assertEqual(devices.status_code, 200)
        self.assertEqual(len(devices.get_json()["devices"]), 1)

        connected = self.client.post("/api/connect_sdr", json={"device_id": "rtl_sdr_0"})
        self.assertEqual(connected.status_code, 200)
        self.assertTrue(connected.get_json().get("ok"))

        disconnected = self.client.post("/api/disconnect_sdr")
        self.assertEqual(disconnected.status_code, 200)
        self.assertTrue(disconnected.get_json().get("ok"))

    def test_diagnostics_endpoint_shape(self) -> None:
        response = self.client.get("/api/diagnostics")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("sdr", payload)
        self.assertIn("running", payload)
        self.assertIn("sample_rate", payload)
        self.assertIn("center_freq", payload)
        self.assertIn("rtl_module", payload["sdr"])
        self.assertIn("hackrf_module", payload["sdr"])
        self.assertIn("last_error", payload["sdr"])

    def test_signal_history_endpoint_shape(self) -> None:
        response = self.client.get("/api/signal_history")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("history", payload)
        self.assertIn("max_points", payload)
        self.assertTrue(isinstance(payload["history"], list))

    def test_scan_start_stop_and_status(self) -> None:
        start = self.client.post(
            "/api/scan/start",
            json={
                "start_hz": 88_000_000,
                "stop_hz": 89_000_000,
                "step_hz": 100_000,
                "dwell_ms": 200,
                "pause_on_signal": True,
            },
        )
        self.assertEqual(start.status_code, 200)
        self.assertTrue(start.get_json().get("ok"))

        status = self.client.get("/api/scan/status")
        self.assertEqual(status.status_code, 200)
        payload = status.get_json()
        self.assertTrue(payload["active"])
        self.assertEqual(payload["start_hz"], 88_000_000.0)
        self.assertEqual(payload["stop_hz"], 89_000_000.0)

        stop = self.client.post("/api/scan/stop")
        self.assertEqual(stop.status_code, 200)
        self.assertTrue(stop.get_json().get("ok"))

        status2 = self.client.get("/api/scan/status").get_json()
        self.assertFalse(status2["active"])

    def test_scan_start_rejects_invalid_range(self) -> None:
        bad = self.client.post(
            "/api/scan/start",
            json={
                "start_hz": 100_000_000,
                "stop_hz": 90_000_000,
            },
        )
        self.assertEqual(bad.status_code, 400)
        self.assertFalse(bad.get_json().get("ok"))


class TcpControlDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = AppState()
        self.logs = LogManager(max_logs=50)
        self.tcp = TCPControlServer(self.state, self.logs)

    def test_frequency_get_and_set(self) -> None:
        with self.state.lock:
            self.state.center_freq = 101_700_000.0
            self.state.generator.center_freq = 101_700_000.0

        self.assertEqual(self.tcp._dispatch("F"), "101700000")
        self.assertEqual(self.tcp._dispatch("F 145000000"), "RPRT 0")
        with self.state.lock:
            self.assertEqual(self.state.center_freq, 145_000_000.0)

    def test_mode_get_and_set(self) -> None:
        with self.state.lock:
            self.state.modulation_mode = "AM"

        self.assertEqual(self.tcp._dispatch("M"), "AM")
        self.assertEqual(self.tcp._dispatch("M NFM"), "RPRT 0")
        with self.state.lock:
            self.assertEqual(self.state.modulation_mode, "FM")

    def test_squelch_get_and_set(self) -> None:
        with self.state.lock:
            self.state.demodulator.set_squelch(-55.0)

        self.assertEqual(self.tcp._dispatch("L SQUELCH"), "-55.0")
        self.assertEqual(self.tcp._dispatch("L SQUELCH -35"), "RPRT 0")
        with self.state.lock:
            self.assertEqual(self.state.demodulator.squelch_db, -35.0)

    def test_ppm_get_and_set(self) -> None:
        with self.state.lock:
            self.state.ppm_correction = 2.5

        self.assertEqual(self.tcp._dispatch("P"), "2.5")
        self.assertEqual(self.tcp._dispatch("P -12"), "RPRT 0")
        with self.state.lock:
            self.assertEqual(self.state.ppm_correction, -12.0)

    def test_status_returns_json(self) -> None:
        res = self.tcp._dispatch("R")
        self.assertTrue(isinstance(res, str))
        self.assertIn('"running"', res)
        self.assertIn('"center_freq"', res)

    def test_quit_returns_none(self) -> None:
        self.assertIsNone(self.tcp._dispatch("Q"))

    def test_invalid_command_returns_error(self) -> None:
        self.assertEqual(self.tcp._dispatch("XYZ"), "RPRT -8")


if __name__ == "__main__":
    unittest.main()
