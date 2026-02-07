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
                self.device.sample_rate = rate
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
                self.device.center_freq = freq
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
                self.device.gain = gain
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
            samples = self.device.read_samples(num_samples)
            return samples
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
