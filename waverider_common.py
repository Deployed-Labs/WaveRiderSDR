"""
WaveRiderSDR Common Module
Shared classes and utilities used by both desktop and web versions
"""

import numpy as np

# Check for pyserial availability
try:
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False

# Check for RTL-SDR support
try:
    from rtlsdr import RtlSdr
    RTLSDR_AVAILABLE = True
except ImportError:
    RTLSDR_AVAILABLE = False

# Check for HackRF support via SoapySDR
try:
    import SoapySDR
    from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
    HACKRF_AVAILABLE = True
except ImportError:
    HACKRF_AVAILABLE = False


class SDRDevice:
    """Interface for SDR devices (RTL-SDR, HackRF, etc.)
    
    This class provides a unified interface for detecting and reading from
    various SDR hardware devices.
    """
    
    def __init__(self):
        """Initialize SDR device interface"""
        self.device = None
        self.device_type = None
        self.is_connected = False
        self.sample_rate = 2.4e6
        self.center_freq = 100e6
        self.gain = 'auto'
        
    def detect_devices(self):
        """Detect available SDR devices
        
        Returns:
            list: List of detected SDR devices with their info
        """
        devices = []
        
        # Check for RTL-SDR devices
        if RTLSDR_AVAILABLE:
            try:
                # Try to get device count
                from rtlsdr import librtlsdr
                device_count = librtlsdr.rtlsdr_get_device_count()
                
                for i in range(device_count):
                    name = librtlsdr.rtlsdr_get_device_name(i)
                    devices.append({
                        'index': i,
                        'type': 'RTL-SDR',
                        'name': name.decode('utf-8') if isinstance(name, bytes) else str(name),
                        'description': f'RTL-SDR Device #{i}'
                    })
            except Exception as e:
                print(f"Error detecting RTL-SDR devices: {e}")
        
        # Check for HackRF devices via SoapySDR
        if HACKRF_AVAILABLE:
            try:
                # Enumerate all SoapySDR devices
                results = SoapySDR.Device.enumerate()
                hackrf_count = 0
                for result in results:
                    # Check if this is a HackRF device
                    if 'hackrf' in result.get('driver', '').lower():
                        devices.append({
                            'index': hackrf_count,
                            'type': 'HackRF',
                            'name': result.get('label', f'HackRF #{hackrf_count}'),
                            'description': f"HackRF Device #{hackrf_count}: {result.get('serial', 'N/A')}"
                        })
                        hackrf_count += 1
            except Exception as e:
                print(f"Error detecting HackRF devices: {e}")
        
        return devices
    
    def connect(self, device_index=0, device_type='RTL-SDR'):
        """Connect to an SDR device
        
        Args:
            device_index: Index of the device to connect to
            device_type: Type of device ('RTL-SDR', 'HackRF', etc.)
            
        Returns:
            bool: True if connection successful
        """
        try:
            if device_type == 'RTL-SDR' and RTLSDR_AVAILABLE:
                self.device = RtlSdr(device_index)
                self.device_type = 'RTL-SDR'
                
                # Configure device with default parameters
                self.device.sample_rate = self.sample_rate
                self.device.center_freq = self.center_freq
                self.device.gain = self.gain
                
                self.is_connected = True
                return True
            elif device_type == 'HackRF' and HACKRF_AVAILABLE:
                # Connect to HackRF via SoapySDR
                results = SoapySDR.Device.enumerate()
                hackrf_devices = [r for r in results if 'hackrf' in r.get('driver', '').lower()]
                
                if device_index < len(hackrf_devices):
                    self.device = SoapySDR.Device(hackrf_devices[device_index])
                    self.device_type = 'HackRF'
                    
                    # Setup RX stream
                    self.hackrf_stream = self.device.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
                    
                    # Configure device with default parameters
                    self.device.setSampleRate(SOAPY_SDR_RX, 0, self.sample_rate)
                    self.device.setFrequency(SOAPY_SDR_RX, 0, self.center_freq)
                    
                    # Set gain (HackRF has different gain controls)
                    if self.gain != 'auto':
                        self.device.setGain(SOAPY_SDR_RX, 0, float(self.gain))
                    
                    # Activate the stream
                    self.device.activateStream(self.hackrf_stream)
                    
                    self.is_connected = True
                    return True
                else:
                    print(f"HackRF device index {device_index} not found")
                    return False
            else:
                print(f"Device type {device_type} not supported or library not available")
                return False
                
        except Exception as e:
            print(f"Failed to connect to SDR device: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the SDR device"""
        if self.device:
            try:
                if self.device_type == 'HackRF' and hasattr(self, 'hackrf_stream'):
                    self.device.deactivateStream(self.hackrf_stream)
                    self.device.closeStream(self.hackrf_stream)
                self.device.close()
            except Exception as e:
                print(f"Error closing SDR device: {e}")
        self.device = None
        self.is_connected = False
    
    def set_sample_rate(self, rate):
        """Set sample rate
        
        Args:
            rate: Sample rate in Hz
        """
        self.sample_rate = rate
        if self.device and self.is_connected:
            try:
                if self.device_type == 'RTL-SDR':
                    self.device.sample_rate = rate
                elif self.device_type == 'HackRF':
                    self.device.setSampleRate(SOAPY_SDR_RX, 0, rate)
            except Exception as e:
                print(f"Error setting sample rate: {e}")
    
    def set_center_freq(self, freq):
        """Set center frequency
        
        Args:
            freq: Center frequency in Hz
        """
        self.center_freq = freq
        if self.device and self.is_connected:
            try:
                if self.device_type == 'RTL-SDR':
                    self.device.center_freq = freq
                elif self.device_type == 'HackRF':
                    self.device.setFrequency(SOAPY_SDR_RX, 0, freq)
            except Exception as e:
                print(f"Error setting center frequency: {e}")
    
    def set_gain(self, gain):
        """Set gain
        
        Args:
            gain: Gain value or 'auto'
        """
        self.gain = gain
        if self.device and self.is_connected:
            try:
                if self.device_type == 'RTL-SDR':
                    self.device.gain = gain
                elif self.device_type == 'HackRF' and gain != 'auto':
                    self.device.setGain(SOAPY_SDR_RX, 0, float(gain))
            except Exception as e:
                print(f"Error setting gain: {e}")
    
    def read_samples(self, num_samples):
        """Read IQ samples from the SDR device
        
        Args:
            num_samples: Number of samples to read
            
        Returns:
            numpy.ndarray: Complex IQ samples, or None if not connected
        """
        if not self.is_connected or not self.device:
            return None
        
        try:
            if self.device_type == 'RTL-SDR':
                samples = self.device.read_samples(num_samples)
                return samples
            elif self.device_type == 'HackRF':
                # Read samples from HackRF via SoapySDR
                buff = np.zeros(num_samples, dtype=np.complex64)
                sr = self.device.readStream(self.hackrf_stream, [buff], num_samples)
                if sr.ret > 0:
                    return buff[:sr.ret]
                else:
                    return None
        except Exception as e:
            print(f"Error reading samples from SDR: {e}")
            return None
    
    def get_status(self):
        """Get current SDR device status
        
        Returns:
            dict: Status information
        """
        return {
            'connected': self.is_connected,
            'device_type': self.device_type,
            'sample_rate': self.sample_rate,
            'center_freq': self.center_freq,
            'gain': self.gain
        }


class MeshtasticDetector:
    """Detect Meshtastic devices via USB
    
    This class provides cross-platform detection of Meshtastic devices
    connected via USB by checking for known vendor IDs.
    """
    
    # Known Meshtastic device vendor IDs
    MESHTASTIC_VIDS = {
        0x239a,  # RAK (RAK4631, T-Echo)
        0x303a,  # Heltec Tracker
        0x10c4,  # Silicon Labs CP210x (Heltec, T-Lora)
        0x1a86,  # WCH CH340/341 (T-Beam, T-Lora, Nano G1)
    }
    
    def __init__(self):
        """Initialize the detector"""
        self.detected_ports = []
        
    def detect_devices(self):
        """Detect Meshtastic devices connected via USB
        
        Returns:
            list: List of serial port objects for detected Meshtastic devices
        """
        if not PYSERIAL_AVAILABLE:
            return []
            
        self.detected_ports = []
        
        try:
            for port in serial.tools.list_ports.comports():
                if port.vid in self.MESHTASTIC_VIDS:
                    self.detected_ports.append(port)
        except Exception as e:
            print(f"Error detecting devices: {e}")
                
        return self.detected_ports
    
    def get_device_info(self, port):
        """Get information about a detected device
        
        Args:
            port: Serial port object
            
        Returns:
            dict: Device information including device path, VID, PID, description, and manufacturer
        """
        return {
            'device': port.device,
            'vid': hex(port.vid) if port.vid else 'N/A',
            'pid': hex(port.pid) if port.pid else 'N/A',
            'description': port.description,
            'manufacturer': port.manufacturer
        }


class LoRaCommunication:
    """Manage LoRa communication with Meshtastic devices
    
    This class handles connection and configuration of LoRa parameters
    for Meshtastic devices.
    """
    
    def __init__(self, port=None):
        """Initialize LoRa communication
        
        Args:
            port: Optional serial port device path
        """
        self.port = port
        self.serial_connection = None
        self.is_connected = False
        self.frequency = 915.0  # Default LoRa frequency in MHz (US)
        self.bandwidth = 125  # kHz
        self.spreading_factor = 7
        
    def connect(self, port):
        """Connect to a Meshtastic device
        
        Args:
            port: Serial port device path
            
        Returns:
            bool: True if connection successful
        """
        try:
            self.port = port
            # Note: Actual serial connection would be opened here
            # For now, we'll simulate the connection
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to {port}: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the Meshtastic device"""
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except Exception as e:
                print(f"Warning: Error while disconnecting from serial port: {e}")
        self.is_connected = False
        
    def configure_lora_params(self, frequency=None, bandwidth=None, spreading_factor=None):
        """Configure LoRa communication parameters
        
        Args:
            frequency: LoRa frequency in MHz (optional)
            bandwidth: Bandwidth in kHz (optional)
            spreading_factor: LoRa spreading factor 7-12 (optional)
        """
        if frequency is not None:
            self.frequency = frequency
        if bandwidth is not None:
            self.bandwidth = bandwidth
        if spreading_factor is not None:
            self.spreading_factor = spreading_factor
            
    def get_status(self):
        """Get current LoRa communication status
        
        Returns:
            dict: Status information including connection state, port, frequency, bandwidth, and spreading factor
        """
        return {
            'connected': self.is_connected,
            'port': self.port,
            'frequency': self.frequency,
            'bandwidth': self.bandwidth,
            'spreading_factor': self.spreading_factor
        }


class SignalGenerator:
    """Generate simulated SDR signals for demonstration
    
    This class creates realistic simulated RF signals with multiple carriers,
    FM modulation, and noise for testing and demonstration purposes.
    """
    
    def __init__(self, sample_rate=2.4e6, center_freq=100e6):
        """Initialize signal generator
        
        Args:
            sample_rate: Sample rate in Hz (default: 2.4 MHz)
            center_freq: Center frequency in Hz (default: 100 MHz)
        """
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.time = 0
        
    def generate_samples(self, num_samples):
        """Generate simulated RF samples
        
        Creates a complex IQ signal with multiple components:
        - Multiple carrier waves at different frequencies
        - FM-modulated signal
        - Background noise
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            numpy.ndarray: Complex IQ samples
        """
        # Generate time array
        t = np.arange(num_samples) / self.sample_rate + self.time
        self.time += num_samples / self.sample_rate
        
        # Create a complex signal with multiple components
        # 1. Carrier wave at center
        signal = np.exp(2j * np.pi * 0 * t)
        
        # 2. Add modulated signals at different frequencies
        signal += 0.3 * np.exp(2j * np.pi * (self.sample_rate * 0.15) * t)
        signal += 0.2 * np.exp(2j * np.pi * (self.sample_rate * -0.2) * t)
        
        # 3. Add FM-like signal
        fm_freq = self.sample_rate * 0.3
        modulation = 0.05 * np.sin(2 * np.pi * 1000 * t)
        signal += 0.4 * np.exp(2j * np.pi * fm_freq * t + modulation)
        
        # 4. Add noise
        noise = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * 0.1
        signal += noise
        
        return signal


def compute_fft_db(samples, fft_size=None):
    """Compute FFT and convert to dB scale
    
    Args:
        samples: Complex IQ samples
        fft_size: FFT size (optional, defaults to length of samples)
        
    Returns:
        numpy.ndarray: FFT magnitude in dB
    """
    if fft_size is None:
        fft_size = len(samples)
    
    # Apply Hamming window
    window = np.hamming(len(samples))
    samples_windowed = samples * window
    
    # Compute FFT
    fft = np.fft.fftshift(np.fft.fft(samples_windowed, n=fft_size))
    
    # Convert to dB
    magnitude = np.abs(fft)
    magnitude_db = 20 * np.log10(magnitude + 1e-10)  # Add small value to avoid log(0)
    
    return magnitude_db


class Demodulator:
    """Demodulate various modulation schemes (AM, FM, SSB, CW)
    
    This class provides demodulation capabilities for common analog modulation types.
    """
    
    def __init__(self, sample_rate=2.4e6):
        """Initialize demodulator
        
        Args:
            sample_rate: Sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.prev_phase = 0
        
    def demodulate_am(self, samples):
        """Demodulate AM (Amplitude Modulation) signal
        
        Args:
            samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio signal
        """
        # AM demodulation: simply take the magnitude
        return np.abs(samples)
    
    def demodulate_fm(self, samples):
        """Demodulate FM (Frequency Modulation) signal
        
        Args:
            samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio signal
        """
        # FM demodulation: compute phase difference
        phase = np.angle(samples)
        phase_diff = np.diff(phase)
        
        # Unwrap phase to handle wraparound
        phase_diff = np.unwrap(phase_diff)
        
        # Prepend a zero to maintain array length
        phase_diff = np.insert(phase_diff, 0, self.prev_phase)
        self.prev_phase = phase_diff[-1]
        
        return phase_diff
    
    def demodulate_usb(self, samples):
        """Demodulate USB (Upper Sideband) signal
        
        Args:
            samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio signal
        """
        # USB demodulation: take the real part after shifting frequency
        return np.real(samples)
    
    def demodulate_lsb(self, samples):
        """Demodulate LSB (Lower Sideband) signal
        
        Args:
            samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio signal
        """
        # LSB demodulation: take the real part after frequency reversal
        return np.real(np.conj(samples))
    
    def demodulate_cw(self, samples):
        """Demodulate CW (Morse code) signal
        
        Args:
            samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated envelope for Morse detection
        """
        # CW demodulation: envelope detection
        return np.abs(samples)


class MorseDecoder:
    """Decode Morse code (CW) signals from demodulated audio
    
    This class detects Morse code patterns and converts them to text.
    """
    
    # Morse code dictionary
    MORSE_CODE = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
        '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
        '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
        '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
        '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
        '--..': 'Z', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
        '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9',
        '-----': '0', '..--..': '?', '-..-.': '/', '-.-.--': '!',
        '.--.-.': '@', '.-...': '&', '---...': ':', '-.-.-.': ';',
        '-...-': '=', '.-.-.': '+', '-....-': '-', '..--.-': '_',
        '.-..-.': '"', '...-..-': '$', '.-.-.-': '.'
    }
    
    def __init__(self, sample_rate=2.4e6, wpm=20):
        """Initialize Morse decoder
        
        Args:
            sample_rate: Sample rate in Hz
            wpm: Words per minute (affects timing)
        """
        self.sample_rate = sample_rate
        self.wpm = wpm
        
        # Calculate timing thresholds based on WPM
        # Standard: 1 dot = 1.2 / WPM seconds
        self.dot_duration = 1.2 / wpm
        self.dash_duration = 3 * self.dot_duration
        self.element_gap = self.dot_duration
        self.char_gap = 3 * self.dot_duration
        self.word_gap = 7 * self.dot_duration
        
        # Detection state
        self.current_symbol = ""
        self.current_word = ""
        self.decoded_text = ""
        self.last_state = 0
        self.state_duration = 0
        
        # Threshold for signal detection
        self.threshold = 0.3
        
    def process_samples(self, envelope):
        """Process envelope samples to detect Morse code
        
        Args:
            envelope: Demodulated envelope signal
            
        Returns:
            str: Newly decoded text (if any)
        """
        # Average the envelope to get signal strength
        avg_signal = np.mean(envelope)
        
        # Detect on/off state
        current_state = 1 if avg_signal > self.threshold else 0
        
        # Calculate duration in samples
        samples_per_second = self.sample_rate
        duration_samples = len(envelope)
        duration_seconds = duration_samples / samples_per_second
        
        new_text = ""
        
        # If state changed
        if current_state != self.last_state:
            if self.last_state == 1:  # End of a tone (dot or dash)
                if self.state_duration >= self.dash_duration * 0.7:
                    self.current_symbol += '-'
                elif self.state_duration >= self.dot_duration * 0.5:
                    self.current_symbol += '.'
            else:  # End of a gap
                if self.state_duration >= self.word_gap * 0.7:
                    # End of word
                    if self.current_symbol:
                        char = self.MORSE_CODE.get(self.current_symbol, '?')
                        new_text += char + ' '
                        self.current_symbol = ""
                elif self.state_duration >= self.char_gap * 0.7:
                    # End of character
                    if self.current_symbol:
                        char = self.MORSE_CODE.get(self.current_symbol, '?')
                        new_text += char
                        self.current_symbol = ""
            
            self.state_duration = 0
        
        # Accumulate duration
        self.state_duration += duration_seconds
        self.last_state = current_state
        
        if new_text:
            self.decoded_text += new_text
        
        return new_text
    
    def get_decoded_text(self):
        """Get all decoded text
        
        Returns:
            str: Complete decoded text
        """
        return self.decoded_text
    
    def reset(self):
        """Reset decoder state"""
        self.current_symbol = ""
        self.current_word = ""
        self.decoded_text = ""
        self.last_state = 0
        self.state_duration = 0
