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
            except Exception:
                pass
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
