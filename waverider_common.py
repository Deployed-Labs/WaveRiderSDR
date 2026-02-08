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

# Check for audio output support
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
    AUDIO_BACKEND = 'sounddevice'
except ImportError:
    try:
        import pyaudio
        AUDIO_AVAILABLE = True
        AUDIO_BACKEND = 'pyaudio'
    except ImportError:
        AUDIO_AVAILABLE = False
        AUDIO_BACKEND = None

from scipy import signal as scipy_signal


class BandPlan:
    """Comprehensive frequency band plan for radio navigation
    
    Includes amateur radio bands, broadcast bands, aviation, marine, and other
    commonly used frequency allocations.
    """
    
    # Comprehensive band plan with frequencies in Hz
    BANDS = {
        # AM Broadcast
        'AM Broadcast': {'start': 530e3, 'end': 1700e3, 'center': 1000e3, 'mode': 'AM', 'description': 'AM Radio Broadcasting'},
        
        # Shortwave Broadcast Bands
        'SW 120m': {'start': 2300e3, 'end': 2495e3, 'center': 2400e3, 'mode': 'AM', 'description': 'Shortwave 120m Band'},
        'SW 90m': {'start': 3200e3, 'end': 3400e3, 'center': 3300e3, 'mode': 'AM', 'description': 'Shortwave 90m Band'},
        'SW 75m': {'start': 3900e3, 'end': 4000e3, 'center': 3950e3, 'mode': 'AM', 'description': 'Shortwave 75m Band'},
        'SW 60m': {'start': 4750e3, 'end': 5060e3, 'center': 4900e3, 'mode': 'AM', 'description': 'Shortwave 60m Band'},
        'SW 49m': {'start': 5900e3, 'end': 6200e3, 'center': 6050e3, 'mode': 'AM', 'description': 'Shortwave 49m Band'},
        'SW 41m': {'start': 7200e3, 'end': 7450e3, 'center': 7325e3, 'mode': 'AM', 'description': 'Shortwave 41m Band'},
        'SW 31m': {'start': 9400e3, 'end': 9900e3, 'center': 9650e3, 'mode': 'AM', 'description': 'Shortwave 31m Band'},
        'SW 25m': {'start': 11600e3, 'end': 12100e3, 'center': 11850e3, 'mode': 'AM', 'description': 'Shortwave 25m Band'},
        'SW 22m': {'start': 13570e3, 'end': 13870e3, 'center': 13720e3, 'mode': 'AM', 'description': 'Shortwave 22m Band'},
        'SW 19m': {'start': 15100e3, 'end': 15800e3, 'center': 15450e3, 'mode': 'AM', 'description': 'Shortwave 19m Band'},
        'SW 16m': {'start': 17480e3, 'end': 17900e3, 'center': 17690e3, 'mode': 'AM', 'description': 'Shortwave 16m Band'},
        'SW 13m': {'start': 21450e3, 'end': 21850e3, 'center': 21650e3, 'mode': 'AM', 'description': 'Shortwave 13m Band'},
        'SW 11m': {'start': 25600e3, 'end': 26100e3, 'center': 25850e3, 'mode': 'AM', 'description': 'Shortwave 11m Band'},
        
        # Citizens Band (CB)
        'CB Radio': {'start': 26.965e6, 'end': 27.405e6, 'center': 27.185e6, 'mode': 'AM', 'description': 'Citizens Band Radio'},
        
        # Amateur Radio Bands (HF)
        '160m Ham': {'start': 1.8e6, 'end': 2.0e6, 'center': 1.9e6, 'mode': 'LSB', 'description': 'Amateur 160m Band'},
        '80m Ham': {'start': 3.5e6, 'end': 4.0e6, 'center': 3.75e6, 'mode': 'LSB', 'description': 'Amateur 80m Band'},
        '60m Ham': {'start': 5.3305e6, 'end': 5.4035e6, 'center': 5.357e6, 'mode': 'USB', 'description': 'Amateur 60m Band'},
        '40m Ham': {'start': 7.0e6, 'end': 7.3e6, 'center': 7.15e6, 'mode': 'LSB', 'description': 'Amateur 40m Band'},
        '30m Ham': {'start': 10.1e6, 'end': 10.15e6, 'center': 10.125e6, 'mode': 'USB', 'description': 'Amateur 30m Band'},
        '20m Ham': {'start': 14.0e6, 'end': 14.35e6, 'center': 14.175e6, 'mode': 'USB', 'description': 'Amateur 20m Band'},
        '17m Ham': {'start': 18.068e6, 'end': 18.168e6, 'center': 18.118e6, 'mode': 'USB', 'description': 'Amateur 17m Band'},
        '15m Ham': {'start': 21.0e6, 'end': 21.45e6, 'center': 21.225e6, 'mode': 'USB', 'description': 'Amateur 15m Band'},
        '12m Ham': {'start': 24.89e6, 'end': 24.99e6, 'center': 24.94e6, 'mode': 'USB', 'description': 'Amateur 12m Band'},
        '10m Ham': {'start': 28.0e6, 'end': 29.7e6, 'center': 28.85e6, 'mode': 'USB', 'description': 'Amateur 10m Band'},
        
        # VHF/UHF Bands
        'FM Broadcast': {'start': 87.5e6, 'end': 108e6, 'center': 98e6, 'mode': 'WFM', 'description': 'FM Radio Broadcasting'},
        'Air Band': {'start': 108e6, 'end': 137e6, 'center': 120e6, 'mode': 'AM', 'description': 'Aviation Communication'},
        '2m Ham': {'start': 144e6, 'end': 148e6, 'center': 146e6, 'mode': 'FM', 'description': 'Amateur 2m Band'},
        'Marine VHF': {'start': 156e6, 'end': 162e6, 'center': 156.8e6, 'mode': 'FM', 'description': 'Marine Communication'},
        'Weather Radio': {'start': 162.4e6, 'end': 162.55e6, 'center': 162.5e6, 'mode': 'FM', 'description': 'NOAA Weather Radio'},
        'PMR446': {'start': 446e6, 'end': 446.2e6, 'center': 446.1e6, 'mode': 'FM', 'description': 'Personal Mobile Radio'},
        '70cm Ham': {'start': 420e6, 'end': 450e6, 'center': 435e6, 'mode': 'FM', 'description': 'Amateur 70cm Band'},
        'GMRS/FRS': {'start': 462e6, 'end': 467e6, 'center': 464.5e6, 'mode': 'FM', 'description': 'GMRS/FRS Family Radio'},
        
        # ISM Bands
        'ISM 433': {'start': 433.05e6, 'end': 434.79e6, 'center': 433.92e6, 'mode': 'FM', 'description': 'ISM 433 MHz Band'},
        'ISM 868': {'start': 863e6, 'end': 870e6, 'center': 868e6, 'mode': 'FM', 'description': 'ISM 868 MHz Band'},
        'ISM 915': {'start': 902e6, 'end': 928e6, 'center': 915e6, 'mode': 'FM', 'description': 'ISM 915 MHz Band'},
        
        # Public Safety & Services
        'Pagers': {'start': 929e6, 'end': 932e6, 'center': 930e6, 'mode': 'FM', 'description': 'Pager Services'},
        'GSM-900': {'start': 890e6, 'end': 960e6, 'center': 925e6, 'mode': 'FM', 'description': 'GSM 900 MHz'},
        'GSM-1800': {'start': 1710e6, 'end': 1880e6, 'center': 1800e6, 'mode': 'FM', 'description': 'GSM 1800 MHz'},
        
        # Satellite & Space
        'L-Band Sat': {'start': 1530e6, 'end': 1559e6, 'center': 1545e6, 'mode': 'FM', 'description': 'L-Band Satellite'},
        'GPS L1': {'start': 1575.42e6, 'end': 1575.42e6, 'center': 1575.42e6, 'mode': 'FM', 'description': 'GPS L1 Signal'},
    }
    
    @classmethod
    def get_all_bands(cls):
        """Get list of all band names
        
        Returns:
            list: Sorted list of band names
        """
        return sorted(cls.BANDS.keys())
    
    @classmethod
    def get_band_info(cls, band_name):
        """Get information about a specific band
        
        Args:
            band_name: Name of the band
            
        Returns:
            dict: Band information (start, end, center, mode, description)
        """
        return cls.BANDS.get(band_name, None)
    
    @classmethod
    def find_band(cls, frequency):
        """Find which band a frequency belongs to
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            str: Band name or None if not in any band
        """
        for band_name, info in cls.BANDS.items():
            if info['start'] <= frequency <= info['end']:
                return band_name
        return None
    
    @classmethod
    def get_bands_by_category(cls):
        """Get bands organized by category
        
        Returns:
            dict: Bands organized by category
        """
        categories = {
            'Broadcast': [],
            'Amateur Radio': [],
            'Aviation/Marine': [],
            'ISM/Unlicensed': [],
            'Commercial': [],
        }
        
        for band_name in cls.BANDS.keys():
            if 'Ham' in band_name:
                categories['Amateur Radio'].append(band_name)
            elif 'Broadcast' in band_name or 'SW' in band_name or 'AM' in band_name or 'FM' in band_name:
                categories['Broadcast'].append(band_name)
            elif 'Air' in band_name or 'Marine' in band_name or 'Weather' in band_name:
                categories['Aviation/Marine'].append(band_name)
            elif 'ISM' in band_name or 'CB' in band_name or 'PMR' in band_name or 'GMRS' in band_name or 'FRS' in band_name:
                categories['ISM/Unlicensed'].append(band_name)
            else:
                categories['Commercial'].append(band_name)
        
        return {k: v for k, v in categories.items() if v}  # Remove empty categories


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
        self.lna_gain = 0  # Low Noise Amplifier gain
        self.vga_gain = 0  # Variable Gain Amplifier gain
        self.if_gain = 0   # Intermediate Frequency gain
        self.available_gains = []
        
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
                
                # Get available gains
                try:
                    self.available_gains = self.device.get_gains()
                except:
                    self.available_gains = []
                
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
    
    def set_lna_gain(self, gain):
        """Set LNA (Low Noise Amplifier) gain
        
        Args:
            gain: LNA gain value (device-specific)
        """
        self.lna_gain = gain
        # Note: RTL-SDR doesn't have separate LNA/VGA controls
        # This is a placeholder for devices that support it
        # For RTL-SDR, we use the combined gain setting
        if self.device and self.is_connected:
            try:
                if hasattr(self.device, 'set_tuner_gain'):
                    self.device.set_tuner_gain(gain)
            except Exception as e:
                print(f"Error setting LNA gain: {e}")
    
    def set_vga_gain(self, gain):
        """Set VGA (Variable Gain Amplifier) gain
        
        Args:
            gain: VGA gain value (device-specific)
        """
        self.vga_gain = gain
        # Note: RTL-SDR doesn't have separate LNA/VGA controls
        # This is a placeholder for devices that support it
        if self.device and self.is_connected:
            try:
                if hasattr(self.device, 'set_if_gain'):
                    self.device.set_if_gain(gain)
            except Exception as e:
                print(f"Error setting VGA gain: {e}")
    
    def get_gains(self):
        """Get available gain values for the device
        
        Returns:
            list: Available gain values in dB
        """
        if self.device and self.is_connected:
            try:
                return self.device.get_gains()
            except:
                return []
        return self.available_gains
    
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


class WaterfallSettings:
    """Settings and configuration for waterfall display
    
    Manages color schemes, intensity, contrast, and other waterfall parameters
    """
    
    COLORMAPS = {
        'viridis': 'viridis',
        'plasma': 'plasma',
        'inferno': 'inferno',
        'magma': 'magma',
        'hot': 'hot',
        'cool': 'cool',
        'rainbow': 'jet',
        'grayscale': 'gray',
        'turbo': 'turbo',
        'wb': 'WB'  # White-Blue (SDR++ style)
    }
    
    def __init__(self):
        """Initialize waterfall settings with defaults"""
        self.colormap = 'viridis'
        self.min_db = -80  # Minimum dB level (floor)
        self.max_db = 0    # Maximum dB level (ceiling)
        self.contrast = 1.0  # Contrast multiplier
        self.brightness = 0.0  # Brightness offset
        self.averaging = 1  # Number of frames to average (smoothing)
        self.peak_hold = False  # Enable peak hold
        self.peak_decay = 0.95  # Peak decay rate
        self.waterfall_speed = 1  # Waterfall scroll speed multiplier
        self.show_grid = True  # Show frequency grid
        self.show_peak_marker = True  # Show peak frequency marker
        
        # Peak hold buffer
        self.peak_buffer = None
    
    def set_colormap(self, colormap_name):
        """Set colormap for waterfall
        
        Args:
            colormap_name: Name of colormap from COLORMAPS
        """
        if colormap_name in self.COLORMAPS:
            self.colormap = self.COLORMAPS[colormap_name]
    
    def set_range(self, min_db, max_db):
        """Set dynamic range for waterfall
        
        Args:
            min_db: Minimum dB level
            max_db: Maximum dB level
        """
        self.min_db = min(min_db, max_db - 5)  # Ensure at least 5 dB range
        self.max_db = max_db
    
    def set_contrast(self, contrast):
        """Set contrast (0.1 to 3.0)
        
        Args:
            contrast: Contrast multiplier
        """
        self.contrast = np.clip(contrast, 0.1, 3.0)
    
    def set_brightness(self, brightness):
        """Set brightness (-50 to +50 dB)
        
        Args:
            brightness: Brightness offset in dB
        """
        self.brightness = np.clip(brightness, -50, 50)
    
    def set_averaging(self, frames):
        """Set number of frames to average for smoothing
        
        Args:
            frames: Number of frames (1 = no averaging, higher = more smoothing)
        """
        self.averaging = max(1, int(frames))
    
    def apply_processing(self, fft_db):
        """Apply waterfall processing (contrast, brightness, peak hold)
        
        Args:
            fft_db: FFT magnitude in dB
            
        Returns:
            numpy.ndarray: Processed FFT data
        """
        # Apply brightness and contrast
        processed = (fft_db + self.brightness) * self.contrast
        
        # Apply peak hold if enabled
        if self.peak_hold:
            if self.peak_buffer is None or len(self.peak_buffer) != len(processed):
                self.peak_buffer = processed.copy()
            else:
                # Update peak hold buffer
                self.peak_buffer = np.maximum(processed, self.peak_buffer * self.peak_decay)
                processed = self.peak_buffer.copy()
        
        # Clip to range
        processed = np.clip(processed, self.min_db, self.max_db)
        
        return processed
    
    def get_settings_dict(self):
        """Get all settings as dictionary
        
        Returns:
            dict: Current settings
        """
        return {
            'colormap': self.colormap,
            'min_db': self.min_db,
            'max_db': self.max_db,
            'contrast': self.contrast,
            'brightness': self.brightness,
            'averaging': self.averaging,
            'peak_hold': self.peak_hold,
            'waterfall_speed': self.waterfall_speed,
            'show_grid': self.show_grid,
            'show_peak_marker': self.show_peak_marker
        }


class AudioDemodulator:
    """Base class for audio demodulation
    
    This is the parent class for various demodulation methods (FM, AM, SSB, etc.)
    """
    
    def __init__(self, sample_rate=2.4e6, audio_rate=48000, cutoff_freq=15000, squelch_threshold=-50):
        """Initialize audio demodulator
        
        Args:
            sample_rate: Input IQ sample rate in Hz
            audio_rate: Output audio sample rate in Hz (default: 48 kHz)
            cutoff_freq: Low-pass filter cutoff frequency in Hz
            squelch_threshold: Squelch threshold in dB (default: -50 dB)
        """
        self.sample_rate = sample_rate
        self.audio_rate = audio_rate
        self.cutoff_freq = cutoff_freq
        
        # Calculate decimation factor
        self.decimation = int(sample_rate / audio_rate)
        
        # Design low-pass filter for audio
        self.audio_filter = scipy_signal.butter(5, cutoff_freq / (audio_rate / 2), btype='low')
        
        # Squelch parameters
        self.squelch_threshold = squelch_threshold  # dB threshold for squelch
        self.squelch_enabled = True
        self.squelch_alpha = 0.1  # Smoothing factor for power estimation
        self.smoothed_power = -100  # Initialize to very low value
        self.last_signal_detected = False
        self.squelch_hysteresis = 3  # dB hysteresis to prevent chattering
        
    def detect_signal(self, iq_samples):
        """Detect if there's a strong signal present (with squelch)
        
        Args:
            iq_samples: Complex IQ samples
            
        Returns:
            bool: True if signal detected above threshold
        """
        # Calculate instantaneous power in dB
        power = np.mean(np.abs(iq_samples) ** 2)
        power_db = 10 * np.log10(power + 1e-10)
        
        # Apply exponential smoothing for more stable squelch
        self.smoothed_power = (self.squelch_alpha * power_db + 
                              (1 - self.squelch_alpha) * self.smoothed_power)
        
        # Apply hysteresis to prevent chattering
        if self.squelch_enabled:
            if self.last_signal_detected:
                # Signal was on, use lower threshold to turn off
                threshold = self.squelch_threshold - self.squelch_hysteresis
            else:
                # Signal was off, use higher threshold to turn on
                threshold = self.squelch_threshold
            
            signal_detected = self.smoothed_power > threshold
        else:
            # Squelch disabled, always pass signal
            signal_detected = True
        
        self.last_signal_detected = signal_detected
        return signal_detected
    
    def set_squelch(self, threshold_db):
        """Set squelch threshold
        
        Args:
            threshold_db: Threshold in dB (-100 to 0)
        """
        self.squelch_threshold = np.clip(threshold_db, -100, 0)
    
    def enable_squelch(self, enabled):
        """Enable or disable squelch
        
        Args:
            enabled: True to enable squelch, False to disable
        """
        self.squelch_enabled = enabled
    
    def get_signal_strength(self):
        """Get current signal strength in dB
        
        Returns:
            float: Signal strength in dB
        """
        return self.smoothed_power
    
    def lowpass_filter(self, audio):
        """Apply low-pass filter to audio
        
        Args:
            audio: Audio samples
            
        Returns:
            numpy.ndarray: Filtered audio
        """
        filtered = scipy_signal.lfilter(self.audio_filter[0], self.audio_filter[1], audio)
        return filtered
    
    def demodulate(self, iq_samples):
        """Demodulate IQ samples to audio
        
        Must be implemented by subclasses
        
        Args:
            iq_samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio samples
        """
        raise NotImplementedError("Subclasses must implement demodulate()")


class FMDemodulator(AudioDemodulator):
    """FM (Frequency Modulation) demodulator
    
    Implements wideband FM demodulation for broadcast FM and NFM for
    narrowband communications.
    """
    
    def __init__(self, sample_rate=2.4e6, audio_rate=48000, deviation=75000):
        """Initialize FM demodulator
        
        Args:
            sample_rate: Input IQ sample rate in Hz
            audio_rate: Output audio sample rate in Hz
            deviation: FM deviation in Hz (75 kHz for broadcast, 5 kHz for NFM)
        """
        super().__init__(sample_rate, audio_rate)
        self.deviation = deviation
        self.last_phase = 0
        
    def demodulate(self, iq_samples):
        """Demodulate FM signal to audio
        
        Uses phase differentiation method for FM demodulation
        
        Args:
            iq_samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio samples
        """
        # Calculate instantaneous phase
        phase = np.angle(iq_samples)
        
        # Calculate phase difference (frequency)
        phase_diff = np.diff(phase, prepend=self.last_phase)
        self.last_phase = phase[-1]
        
        # Unwrap phase to handle discontinuities
        phase_diff = np.unwrap(phase_diff)
        
        # Convert to audio (scale by sample rate)
        audio = phase_diff * self.sample_rate / (2 * np.pi * self.deviation)
        
        # Decimate to audio rate
        audio_decimated = scipy_signal.decimate(audio, self.decimation, ftype='iir')
        
        # Apply de-emphasis filter (75 µs time constant for broadcast FM)
        tau = 75e-6  # Time constant
        alpha = 1 / (1 + self.audio_rate * tau)
        audio_deemph = scipy_signal.lfilter([alpha], [1, alpha - 1], audio_decimated)
        
        # Normalize audio
        audio_norm = np.clip(audio_deemph, -1, 1)
        
        return audio_norm.astype(np.float32)


class AMDemodulator(AudioDemodulator):
    """AM (Amplitude Modulation) demodulator
    
    Implements envelope detection for AM demodulation.
    """
    
    def demodulate(self, iq_samples):
        """Demodulate AM signal to audio
        
        Uses envelope detection method
        
        Args:
            iq_samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio samples
        """
        # Calculate envelope (magnitude)
        envelope = np.abs(iq_samples)
        
        # Remove DC component
        envelope = envelope - np.mean(envelope)
        
        # Decimate to audio rate
        audio_decimated = scipy_signal.decimate(envelope, self.decimation, ftype='iir')
        
        # Apply low-pass filter
        audio_filtered = self.lowpass_filter(audio_decimated)
        
        # Normalize
        max_val = np.max(np.abs(audio_filtered))
        if max_val > 0:
            audio_norm = audio_filtered / max_val
        else:
            audio_norm = audio_filtered
            
        return audio_norm.astype(np.float32)


class SSBDemodulator(AudioDemodulator):
    """SSB (Single Sideband) demodulator
    
    Implements USB (Upper Sideband) and LSB (Lower Sideband) demodulation.
    """
    
    def __init__(self, sample_rate=2.4e6, audio_rate=48000, mode='USB'):
        """Initialize SSB demodulator
        
        Args:
            sample_rate: Input IQ sample rate in Hz
            audio_rate: Output audio sample rate in Hz
            mode: 'USB' for upper sideband or 'LSB' for lower sideband
        """
        super().__init__(sample_rate, audio_rate, cutoff_freq=3000)
        self.mode = mode
        
        # Design bandpass filter for SSB (300 Hz to 3000 Hz)
        self.ssb_filter = scipy_signal.butter(5, [300 / (audio_rate / 2), 3000 / (audio_rate / 2)], 
                                              btype='band')
        
    def demodulate(self, iq_samples):
        """Demodulate SSB signal to audio
        
        Args:
            iq_samples: Complex IQ samples
            
        Returns:
            numpy.ndarray: Demodulated audio samples
        """
        # For SSB, we take either the real or imaginary part depending on sideband
        if self.mode == 'USB':
            audio = np.real(iq_samples)
        else:  # LSB
            audio = np.imag(iq_samples)
        
        # Decimate to audio rate
        audio_decimated = scipy_signal.decimate(audio, self.decimation, ftype='iir')
        
        # Apply SSB bandpass filter
        audio_filtered = scipy_signal.lfilter(self.ssb_filter[0], self.ssb_filter[1], 
                                              audio_decimated)
        
        # Normalize
        max_val = np.max(np.abs(audio_filtered))
        if max_val > 0:
            audio_norm = audio_filtered / max_val
        else:
            audio_norm = audio_filtered
            
        return audio_norm.astype(np.float32)


class AudioPlayer:
    """Real-time audio playback
    
    Handles audio output to speakers using sounddevice or pyaudio.
    """
    
    def __init__(self, sample_rate=48000, channels=1, buffer_size=2048):
        """Initialize audio player
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono, 2 for stereo)
            buffer_size: Audio buffer size in samples
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = buffer_size
        self.is_playing = False
        self.stream = None
        
        if not AUDIO_AVAILABLE:
            print("Warning: No audio library available. Install sounddevice or pyaudio for audio playback.")
            
    def start(self):
        """Start audio playback"""
        if not AUDIO_AVAILABLE:
            return False
            
        try:
            if AUDIO_BACKEND == 'sounddevice':
                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    blocksize=self.buffer_size,
                    dtype='float32'
                )
                self.stream.start()
            elif AUDIO_BACKEND == 'pyaudio':
                self.pa = pyaudio.PyAudio()
                self.stream = self.pa.open(
                    format=pyaudio.paFloat32,
                    channels=self.channels,
                    rate=self.sample_rate,
                    output=True,
                    frames_per_buffer=self.buffer_size
                )
            
            self.is_playing = True
            return True
            
        except Exception as e:
            print(f"Failed to start audio playback: {e}")
            return False
    
    def play(self, audio_data):
        """Play audio data
        
        Args:
            audio_data: Audio samples to play (numpy array)
        """
        if not self.is_playing or self.stream is None:
            return
            
        try:
            # Ensure audio data is the right type and shape
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
                
            if self.channels == 1 and len(audio_data.shape) == 1:
                # Mono audio
                if AUDIO_BACKEND == 'sounddevice':
                    self.stream.write(audio_data)
                elif AUDIO_BACKEND == 'pyaudio':
                    self.stream.write(audio_data.tobytes())
            elif self.channels == 2:
                # Stereo - duplicate mono to both channels
                if len(audio_data.shape) == 1:
                    stereo_data = np.column_stack((audio_data, audio_data))
                else:
                    stereo_data = audio_data
                    
                if AUDIO_BACKEND == 'sounddevice':
                    self.stream.write(stereo_data)
                elif AUDIO_BACKEND == 'pyaudio':
                    self.stream.write(stereo_data.tobytes())
                    
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def stop(self):
        """Stop audio playback"""
        self.is_playing = False
        
        if self.stream:
            try:
                if AUDIO_BACKEND == 'sounddevice':
                    self.stream.stop()
                    self.stream.close()
                elif AUDIO_BACKEND == 'pyaudio':
                    self.stream.stop_stream()
                    self.stream.close()
                    self.pa.terminate()
            except Exception as e:
                print(f"Error stopping audio: {e}")
                
        self.stream = None
    
    def is_active(self):
        """Check if audio is currently playing
        
        Returns:
            bool: True if audio playback is active
        """
        return self.is_playing
