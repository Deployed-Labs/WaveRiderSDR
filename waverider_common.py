"""Shared Python SDR runtime used by web and desktop launchers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
import importlib.util
import math
import shutil
import threading
from typing import Optional

import numpy as np

try:
	import serial.tools.list_ports as serial_ports
except Exception:  # pragma: no cover - serial support is optional
	serial_ports = None


@dataclass(frozen=True)
class BandInfo:
	name: str
	start_hz: float
	end_hz: float
	center_hz: float
	mode: str
	description: str


BANDS = [
	BandInfo("FM Broadcast", 88_000_000.0, 108_000_000.0, 98_000_000.0, "FM", "Broadcast FM radio"),
	BandInfo("Airband", 118_000_000.0, 137_000_000.0, 127_500_000.0, "AM", "Aircraft voice communications"),
	BandInfo("2m Amateur", 144_000_000.0, 148_000_000.0, 146_000_000.0, "FM", "2 meter amateur radio"),
	BandInfo("70cm Amateur", 420_000_000.0, 450_000_000.0, 435_000_000.0, "FM", "70 centimeter amateur radio"),
	BandInfo("NOAA Weather", 162_400_000.0, 162_550_000.0, 162_475_000.0, "FM", "NOAA weather radio"),
	BandInfo("20m Amateur", 14_000_000.0, 14_350_000.0, 14_175_000.0, "USB", "20 meter amateur HF band"),
]


def get_band(name: str) -> Optional[BandInfo]:
	lower = name.strip().lower()
	for band in BANDS:
		if band.name.lower() == lower:
			return band
	return None


class SignalGenerator:
	def __init__(self, sample_rate: float, center_freq: float) -> None:
		self.sample_rate = sample_rate
		self.center_freq = center_freq
		self.time = 0.0

	def generate_samples(self, count: int) -> np.ndarray:
		dt = 1.0 / self.sample_rate
		t = self.time + np.arange(count, dtype=np.float32) * dt

		c0 = np.exp(1j * (2.0 * np.pi * 0.0 * t))
		c1 = 0.3 * np.exp(1j * (2.0 * np.pi * (self.sample_rate * 0.15) * t))
		c2 = 0.2 * np.exp(1j * (2.0 * np.pi * (self.sample_rate * -0.2) * t))
		modulation = 0.05 * np.sin(2.0 * np.pi * 1000.0 * t)
		c3 = 0.4 * np.exp(1j * ((2.0 * np.pi * (self.sample_rate * 0.3) * t) + modulation))

		noise = (
			np.random.normal(0.0, 0.1, count).astype(np.float32)
			+ 1j * np.random.normal(0.0, 0.1, count).astype(np.float32)
		)
		self.time += count * dt
		return c0 + c1 + c2 + c3 + noise


def compute_fft_db(samples: np.ndarray, fft_size: int) -> np.ndarray:
	padded = np.zeros(fft_size, dtype=np.complex64)
	length = min(fft_size, len(samples))
	if length > 0:
		window = np.hamming(length).astype(np.float32)
		padded[:length] = samples[:length] * window

	spec = np.fft.fftshift(np.fft.fft(padded, n=fft_size))
	mag = np.abs(spec)
	return 20.0 * np.log10(mag + 1e-10)


class WaterfallSettings:
	def __init__(self) -> None:
		self.min_db = -80.0
		self.max_db = 0.0
		self.peak_hold = False
		self.peak_buffer: Optional[np.ndarray] = None

	def apply_processing(self, spectrum: np.ndarray) -> np.ndarray:
		out = np.asarray(spectrum, dtype=np.float32).copy()

		if self.peak_hold:
			if self.peak_buffer is None or len(self.peak_buffer) != len(out):
				self.peak_buffer = out.copy()
			else:
				self.peak_buffer = np.maximum(self.peak_buffer, out)
			out = self.peak_buffer.copy()
		else:
			self.peak_buffer = None

		return np.clip(out, self.min_db, self.max_db)


class Demodulator:
	def __init__(self) -> None:
		self.squelch_db = -50.0

	def set_squelch(self, value_db: float) -> None:
		self.squelch_db = value_db

	def signal_strength_db(self, samples: np.ndarray) -> float:
		if len(samples) == 0:
			return -120.0
		power = np.mean(np.abs(samples) ** 2)
		rms = math.sqrt(max(power, 1e-12))
		return float(20.0 * math.log10(rms + 1e-10))

	def detect_signal(self, samples: np.ndarray) -> bool:
		return self.signal_strength_db(samples) >= self.squelch_db

	def demodulate_cw(self, samples: np.ndarray) -> np.ndarray:
		return np.abs(samples).astype(np.float32)


class MorseDecoder:
	def __init__(self, sample_rate: float, wpm: float) -> None:
		self.sample_rate = sample_rate
		self.wpm = max(1.0, wpm)
		self.threshold = 0.3
		self.decoded_text = ""
		self.current_symbol = ""
		self.last_state = False
		self.state_duration_s = 0.0
		self.map = {
			".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F", "--.": "G",
			"....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L", "--": "M", "-.": "N",
			"---": "O", ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T", "..-": "U",
			"...-": "V", ".--": "W", "-..-": "X", "-.--": "Y", "--..": "Z", ".----": "1", "..---": "2",
			"...--": "3", "....-": "4", ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
			"-----": "0",
		}

	def reset(self) -> None:
		self.decoded_text = ""
		self.current_symbol = ""
		self.last_state = False
		self.state_duration_s = 0.0

	def process_samples(self, envelope: np.ndarray) -> Optional[str]:
		if len(envelope) == 0:
			return None

		avg = float(np.mean(envelope))
		current_state = avg > self.threshold
		duration_s = len(envelope) / self.sample_rate

		dot = 1.2 / self.wpm
		dash = 3.0 * dot
		char_gap = 3.0 * dot
		word_gap = 7.0 * dot

		new_text = ""

		if current_state != self.last_state:
			if self.last_state:
				if self.state_duration_s >= dash * 0.7:
					self.current_symbol += "-"
				elif self.state_duration_s >= dot * 0.5:
					self.current_symbol += "."
			else:
				if self.state_duration_s >= word_gap * 0.7:
					if self.current_symbol:
						new_text += self.map.get(self.current_symbol, "?") + " "
						self.current_symbol = ""
				elif self.state_duration_s >= char_gap * 0.7 and self.current_symbol:
					new_text += self.map.get(self.current_symbol, "?")
					self.current_symbol = ""
			self.state_duration_s = 0.0

		self.state_duration_s += duration_s
		self.last_state = current_state

		if new_text:
			self.decoded_text += new_text
			return new_text
		return None


class MeshtasticDetector:
	MESHTASTIC_VIDS = {0x239A, 0x303A, 0x10C4, 0x1A86}

	def detect_devices(self) -> list[dict[str, object]]:
		if serial_ports is None:
			return []

		devices: list[dict[str, object]] = []
		for port in serial_ports.comports():
			vid = port.vid
			product = (port.product or "").lower()
			if (vid in self.MESHTASTIC_VIDS) or ("meshtastic" in product):
				devices.append(
					{
						"port": port.device,
						"vid": vid,
						"pid": port.pid,
						"manufacturer": port.manufacturer,
						"product": port.product,
					}
				)
		return devices


class SdrDevice:
	def __init__(self) -> None:
		self.is_connected = False
		self.connected_device: Optional[dict[str, str]] = None
		self._rtl_device = None
		self._hackrf_device = None
		self._hackrf_stream = None
		self.last_error: Optional[str] = None

	def detect_devices(self) -> list[dict[str, str]]:
		devices: list[dict[str, str]] = []

		# Try to enumerate actual RTL-SDR devices
		try:
			rtlsdr = importlib.import_module("rtlsdr")
			get_devices = getattr(rtlsdr, "open", None)
			if get_devices:
				try:
					# Use rtlsdr.get_device_info_by_index() if available
					get_device_info = getattr(rtlsdr, "get_device_info_by_index", None)
					if get_device_info:
						index = 0
						while True:
							try:
								info = get_device_info(index)
								devices.append({
									"id": f"rtl_sdr_{index}",
									"device_type": "RTL-SDR",
									"backend": "rtlsdr",
									"name": f"RTL-SDR #{index}",
									"description": str(info) if info else "RTL-SDR USB device",
								})
								index += 1
							except (IndexError, OSError, ValueError):
								break
							
						# If no devices found via enumeration, offer generic entry
						if not devices:
							devices.append({
								"id": "rtl_sdr_0",
								"device_type": "RTL-SDR",
								"backend": "rtlsdr",
								"name": "RTL-SDR",
								"description": "RTL-SDR (connected USB device)",
							})
				except Exception:
					# If enumeration fails, offer generic entry
					devices.append({
						"id": "rtl_sdr_0",
						"device_type": "RTL-SDR",
						"backend": "rtlsdr",
						"name": "RTL-SDR",
						"description": "RTL-SDR (connected USB device)",
					})
		except (ImportError, ModuleNotFoundError):
			pass

		# Try to enumerate actual HackRF devices via SoapySDR
		try:
			soapysdr = importlib.import_module("SoapySDR")
			try:
				devices_found = soapysdr.Device.enumerate({"driver": "hackrf"})
				for idx, dev in enumerate(devices_found):
					devices.append({
						"id": f"hackrf_{idx}",
						"device_type": "HackRF",
						"backend": "hackrf",
						"name": f"HackRF #{idx}",
						"description": str(dev) if dev else "HackRF USB device",
					})
				
				# If no devices found via enumeration, offer generic entry
				if not any(d.get("backend") == "hackrf" for d in devices):
					devices.append({
						"id": "hackrf_0",
						"device_type": "HackRF",
						"backend": "hackrf",
						"name": "HackRF",
						"description": "HackRF (connected USB device)",
					})
			except Exception:
				# If enumeration fails, offer generic entry
				devices.append({
					"id": "hackrf_0",
					"device_type": "HackRF",
					"backend": "hackrf",
					"name": "HackRF",
					"description": "HackRF (connected USB device)",
				})
		except (ImportError, ModuleNotFoundError):
			pass

		return devices

	def diagnostics(self) -> dict[str, object]:
		rtl_module = importlib.util.find_spec("rtlsdr") is not None
		hackrf_module = importlib.util.find_spec("SoapySDR") is not None
		rtl_tool = bool(shutil.which("rtl_test"))
		hackrf_tool = bool(shutil.which("SoapySDRUtil"))
		connected_backend = None
		if self.connected_device:
			connected_backend = self.connected_device.get("backend")

		return {
			"rtl_module": rtl_module,
			"hackrf_module": hackrf_module,
			"rtl_tool": rtl_tool,
			"hackrf_tool": hackrf_tool,
			"connected_backend": connected_backend,
			"last_error": self.last_error,
		}

	def connect(self, device_id: str) -> bool:
		self.disconnect()
		self.last_error = None

		for device in self.detect_devices():
			if device["id"] == device_id:
				backend = device.get("backend")
				try:
					if backend == "rtlsdr":
						self._connect_rtlsdr()
					elif backend == "hackrf":
						self._connect_hackrf()
					else:
						raise RuntimeError("Unknown SDR backend")
					self.connected_device = device
					self.is_connected = True
					return True
				except Exception as exc:
					self.last_error = str(exc)
					self.disconnect()
					return False
		self.connected_device = None
		self.is_connected = False
		return False

	def disconnect(self) -> None:
		if self._rtl_device is not None:
			try:
				self._rtl_device.close()
			except Exception:
				pass
			self._rtl_device = None

		if self._hackrf_device is not None:
			try:
				if self._hackrf_stream is not None:
					self._hackrf_device.deactivateStream(self._hackrf_stream)
					self._hackrf_device.closeStream(self._hackrf_stream)
			except Exception:
				pass
			self._hackrf_stream = None
			self._hackrf_device = None

		self.connected_device = None
		self.is_connected = False

	def source_label(self) -> str:
		if not self.connected_device:
			return "Simulated"
		return f"{self.connected_device['device_type']} ({self.connected_device['name']})"

	def read_samples(self, num_samples: int, sample_rate: float, center_freq: float) -> np.ndarray:
		if not self.connected_device:
			raise RuntimeError("No SDR device connected")

		backend = self.connected_device.get("backend")
		if backend == "rtlsdr":
			if self._rtl_device is None:
				raise RuntimeError("RTL-SDR backend not initialized")
			try:
				self._rtl_device.sample_rate = float(sample_rate)
				self._rtl_device.center_freq = float(center_freq)
				raw = self._rtl_device.read_samples(int(num_samples))
				return np.asarray(raw, dtype=np.complex64)
			except Exception as e:
				raise RuntimeError(f"RTL-SDR read failed: {e}") from e

		if backend == "hackrf":
			if self._hackrf_device is None or self._hackrf_stream is None:
				raise RuntimeError("HackRF backend not initialized")
			try:
				return self._read_hackrf_samples(int(num_samples), float(sample_rate), float(center_freq))
			except Exception as e:
				raise RuntimeError(f"HackRF read failed: {e}") from e

		raise RuntimeError("Unknown SDR backend")

	def _connect_rtlsdr(self) -> None:
		try:
			rtlsdr = importlib.import_module("rtlsdr")
			RtlSdr = getattr(rtlsdr, "RtlSdr")
			self._rtl_device = RtlSdr()
			# Set default parameters
			if hasattr(self._rtl_device, "gain"):
				self._rtl_device.gain = "auto"
		except ImportError as e:
			raise RuntimeError(
				f"RTL-SDR module not installed. Install with: pip install pyrtlsdr. Error: {e}"
			) from e
		except AttributeError as e:
			raise RuntimeError(
				f"RTL-SDR module structure unexpected. Install with: pip install pyrtlsdr. Error: {e}"
			) from e
		except Exception as e:
			raise RuntimeError(f"Failed to initialize RTL-SDR device: {e}") from e

	def _connect_hackrf(self) -> None:
		try:
			soapysdr = importlib.import_module("SoapySDR")
			kwargs = {"driver": "hackrf"}
			try:
				self._hackrf_device = soapysdr.Device(kwargs)
			except Exception as device_err:
				raise RuntimeError(
					f"Failed to open HackRF device. Ensure device is connected and drivers are installed. Error: {device_err}"
				) from device_err
			
			try:
				self._hackrf_stream = self._hackrf_device.setupStream(
					soapysdr.SOAPY_SDR_RX,
					soapysdr.SOAPY_SDR_CF32,
				)
				self._hackrf_device.activateStream(self._hackrf_stream)
			except Exception as stream_err:
				raise RuntimeError(
					f"Failed to setup HackRF stream. Error: {stream_err}"
				) from stream_err
		except ImportError as e:
			raise RuntimeError(
				f"SoapySDR module not installed. Install with: pip install SoapySDR. Error: {e}"
			) from e
		except Exception as e:
			raise RuntimeError(f"Failed to initialize HackRF device: {e}") from e

	def _read_hackrf_samples(self, num_samples: int, sample_rate: float, center_freq: float) -> np.ndarray:
		try:
			soapysdr = importlib.import_module("SoapySDR")
			self._hackrf_device.setSampleRate(soapysdr.SOAPY_SDR_RX, 0, sample_rate)  # type: ignore
			self._hackrf_device.setFrequency(soapysdr.SOAPY_SDR_RX, 0, center_freq)  # type: ignore
			buff = np.empty(num_samples, np.complex64)
			result = self._hackrf_device.readStream(self._hackrf_stream, [buff], num_samples)  # type: ignore
			if result.ret <= 0:
				raise RuntimeError(f"HackRF readStream returned {result.ret}")
			return buff[: result.ret].copy()
		except Exception as e:
			if isinstance(e, RuntimeError):
				raise
			raise RuntimeError(f"HackRF sample read failed: {e}") from e


class AppState:
	def __init__(self) -> None:
		self.lock = threading.Lock()

		self.running = False
		self.sample_rate = 2_400_000.0
		self.center_freq = 100_000_000.0
		self.fft_size = 1024
		self.waterfall_height = 100

		self.waveform_data = np.zeros(self.fft_size, dtype=np.float32)
		self.waterfall_data = np.zeros((self.waterfall_height, self.fft_size), dtype=np.float32)

		self.generator = SignalGenerator(self.sample_rate, self.center_freq)
		self.detector = MeshtasticDetector()
		self.sdr = SdrDevice()
		self.demodulator = Demodulator()
		self.morse_decoder = MorseDecoder(self.sample_rate, 20.0)

		self.modulation_mode = "None"
		self.morse_enabled = False
		self.signal_strength_db = -120.0
		self.signal_detected = False
		self.active_source = "Simulated"
		self.source_notice: Optional[str] = None
		self.waterfall_settings = WaterfallSettings()

	def _resize_buffers(self) -> None:
		self.waveform_data = np.zeros(self.fft_size, dtype=np.float32)
		self.waterfall_data = np.zeros((self.waterfall_height, self.fft_size), dtype=np.float32)
		self.waterfall_settings.peak_buffer = None

	def configure(
		self,
		frequency_mhz: Optional[float] = None,
		sample_rate_hz: Optional[float] = None,
		fft_size: Optional[int] = None,
		modulation_mode: Optional[str] = None,
		min_db: Optional[float] = None,
		max_db: Optional[float] = None,
		squelch_db: Optional[float] = None,
		morse_enabled: Optional[bool] = None,
	) -> None:
		if frequency_mhz is not None:
			self.center_freq = max(0.0, float(frequency_mhz) * 1_000_000.0)
			self.generator.center_freq = self.center_freq
		if sample_rate_hz is not None:
			self.sample_rate = max(1000.0, float(sample_rate_hz))
			self.generator.sample_rate = self.sample_rate
			self.morse_decoder.sample_rate = self.sample_rate
		if fft_size is not None:
			new_size = int(fft_size)
			if new_size > 0 and (new_size & (new_size - 1)) == 0:
				self.fft_size = new_size
				self._resize_buffers()
		if modulation_mode is not None:
			self.modulation_mode = str(modulation_mode)
		if min_db is not None:
			self.waterfall_settings.min_db = float(min_db)
		if max_db is not None:
			self.waterfall_settings.max_db = float(max_db)
		if squelch_db is not None:
			self.demodulator.set_squelch(float(squelch_db))
		if morse_enabled is not None:
			self.morse_enabled = bool(morse_enabled)

		if self.waterfall_settings.min_db >= self.waterfall_settings.max_db:
			self.waterfall_settings.max_db = self.waterfall_settings.min_db + 1.0

	def set_band(self, band_name: str) -> bool:
		band = get_band(band_name)
		if not band:
			return False
		self.center_freq = band.center_hz
		self.modulation_mode = band.mode
		self.generator.center_freq = self.center_freq
		return True

	def start(self) -> None:
		self.running = True

	def stop(self) -> None:
		self.running = False

	def tick(self) -> None:
		samples: np.ndarray
		if self.sdr.is_connected:
			connected_label = self.sdr.source_label()
			try:
				samples = self.sdr.read_samples(self.fft_size, self.sample_rate, self.center_freq)
				self.active_source = connected_label
				self.source_notice = None
			except Exception as exc:
				self.active_source = "Simulated"
				self.source_notice = (
					f"Hardware source unavailable: {exc}. Falling back to simulated samples."
				)
				samples = self.generator.generate_samples(self.fft_size)
		else:
			self.active_source = "Simulated"
			self.source_notice = None
			samples = self.generator.generate_samples(self.fft_size)

		self.signal_strength_db = self.demodulator.signal_strength_db(samples)
		self.signal_detected = self.demodulator.detect_signal(samples)

		if self.morse_enabled and self.modulation_mode.lower() == "cw":
			env = self.demodulator.demodulate_cw(samples)
			self.morse_decoder.process_samples(env)

		fft_db = compute_fft_db(samples, self.fft_size)
		processed = self.waterfall_settings.apply_processing(fft_db)
		self.waveform_data = processed.astype(np.float32)
		self.waterfall_data = np.roll(self.waterfall_data, 1, axis=0)
		self.waterfall_data[0, :] = processed

	def get_frame(self) -> dict[str, object]:
		return {
			"waveform": self.waveform_data.tolist(),
			"waterfall": self.waterfall_data.tolist(),
			"min_db": self.waterfall_settings.min_db,
			"max_db": self.waterfall_settings.max_db,
		}

	def get_status(self) -> dict[str, object]:
		connected_id = None
		if self.sdr.connected_device:
			connected_id = self.sdr.connected_device.get("id")

		return {
			"running": self.running,
			"sample_rate": self.sample_rate,
			"center_freq": self.center_freq,
			"fft_size": self.fft_size,
			"modulation_mode": self.modulation_mode,
			"morse_enabled": self.morse_enabled,
			"morse_text": self.morse_decoder.decoded_text[-80:],
			"signal_strength_db": self.signal_strength_db,
			"signal_detected": self.signal_detected,
			"source": self.active_source,
			"source_notice": self.source_notice,
			"sdr_last_error": self.sdr.last_error,
			"meshtastic_devices": self.detector.detect_devices(),
			"sdr_devices": self.sdr.detect_devices(),
			"connected_sdr_id": connected_id,
		}


def bands_as_dicts() -> list[dict[str, object]]:
	return [asdict(band) for band in BANDS]

