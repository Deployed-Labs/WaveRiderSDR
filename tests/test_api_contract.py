import unittest

from waverider_common import AppState
from waverider_web import create_app


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = AppState()
        self.app = create_app(self.state)
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


if __name__ == "__main__":
    unittest.main()
