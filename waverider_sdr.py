"""
WaveRiderSDR - Software Defined Radio with Waterfall Visualization
Main application entry point - Desktop GUI version
"""

import sys
import numpy as np

# Import common utilities
from waverider_common import MeshtasticDetector, LoRaCommunication, SignalGenerator, compute_fft_db, SDRDevice, RTLSDR_AVAILABLE

# Check for PyQt5 availability
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QLabel, QSlider, 
                                 QComboBox, QSpinBox, QDoubleSpinBox)
    from PyQt5.QtCore import QTimer, Qt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    print("Warning: PyQt5 not available. Please install it for desktop GUI support.")
    print("Or use the web version: python waverider_web.py")

from matplotlib.figure import Figure
import matplotlib.pyplot as plt


# Only define GUI classes if PyQt5 is available
if PYQT5_AVAILABLE:
    class WaterfallWidget(FigureCanvas):
        """Widget for displaying waterfall (spectrogram) visualization"""
        
        def __init__(self, parent=None, width=8, height=6, dpi=100):
            self.fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = self.fig.add_subplot(111)
            super(WaterfallWidget, self).__init__(self.fig)
            self.setParent(parent)
            
            # Waterfall display parameters
            self.waterfall_height = 100  # Number of rows in waterfall
            self.fft_size = 1024
            self.waterfall_data = np.zeros((self.waterfall_height, self.fft_size))
            
            # Initialize the waterfall plot
            self.im = self.axes.imshow(self.waterfall_data, 
                                       aspect='auto', 
                                       cmap='viridis',
                                       interpolation='bilinear',
                                       vmin=-80, vmax=0)
            
            self.axes.set_xlabel('Frequency Bins')
            self.axes.set_ylabel('Time')
            self.axes.set_title('Waterfall Display (Spectrogram)')
            self.fig.colorbar(self.im, ax=self.axes, label='Power (dB)')
            self.fig.tight_layout()
            
        def update_waterfall(self, fft_data):
            """Update waterfall display with new FFT data
            
            Args:
                fft_data: FFT magnitude data in dB
            """
            # Shift waterfall data down by one row
            self.waterfall_data = np.roll(self.waterfall_data, 1, axis=0)
            # Add new data to the top row
            self.waterfall_data[0, :] = fft_data
            
            # Update the image
            self.im.set_data(self.waterfall_data)
            self.draw()
            
        def set_frequency_labels(self, center_freq, sample_rate):
            """Update frequency axis labels
            
            Args:
                center_freq: Center frequency in Hz
                sample_rate: Sample rate in Hz
            """
            freq_start = (center_freq - sample_rate / 2) / 1e6  # Convert to MHz
            freq_end = (center_freq + sample_rate / 2) / 1e6
            
            # Update x-axis ticks and labels
            num_ticks = 5
            tick_positions = np.linspace(0, self.fft_size - 1, num_ticks)
            tick_labels = [f'{freq:.2f}' for freq in np.linspace(freq_start, freq_end, num_ticks)]
            
            self.axes.set_xticks(tick_positions)
            self.axes.set_xticklabels(tick_labels)
            self.axes.set_xlabel('Frequency (MHz)')


    class WaveRiderSDR(QMainWindow):
        """Main application window for WaveRiderSDR"""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle('WaveRiderSDR - Waterfall Visualization')
            self.setGeometry(100, 100, 1000, 700)
            
            # Initialize SDR device interface
            self.sdr_device = SDRDevice()
            self.use_real_sdr = False  # Flag to indicate if using real SDR or simulated
            
            # Initialize signal source (for fallback when no SDR present)
            self.sample_rate = 2.4e6  # 2.4 MHz
            self.center_freq = 100e6  # 100 MHz
            self.signal_source = SignalGenerator(self.sample_rate, self.center_freq)
            
            # Initialize Meshtastic detector and LoRa communication
            self.meshtastic_detector = MeshtasticDetector()
            self.lora_comm = LoRaCommunication()
            
            # FFT parameters
            self.fft_size = 1024
            self.update_interval = 50  # ms
            
            # Setup UI
            self.setup_ui()
            
            # Setup update timer (initially stopped)
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_display)
            self.is_running = False  # Track whether acquisition is running
            
            # Setup device detection timer (check every 5 seconds)
            self.device_check_timer = QTimer()
            self.device_check_timer.timeout.connect(self.check_meshtastic_devices)
            self.device_check_timer.start(5000)  # 5 seconds
            
            # Perform initial device checks
            self.check_meshtastic_devices()
            self.scan_sdr_devices()
            
        def setup_ui(self):
            """Setup the user interface"""
            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            
            # Create waterfall widget
            self.waterfall = WaterfallWidget(self, width=8, height=5)
            self.waterfall.set_frequency_labels(self.center_freq, self.sample_rate)
            main_layout.addWidget(self.waterfall)
            
            # Create controls panel
            controls_layout = QHBoxLayout()
            
            # Center frequency control
            freq_layout = QVBoxLayout()
            freq_label = QLabel('Center Frequency (MHz):')
            self.freq_spinbox = QDoubleSpinBox()
            self.freq_spinbox.setRange(24, 1766)
            self.freq_spinbox.setValue(self.center_freq / 1e6)
            self.freq_spinbox.setSingleStep(1)
            self.freq_spinbox.valueChanged.connect(self.on_frequency_changed)
            freq_layout.addWidget(freq_label)
            freq_layout.addWidget(self.freq_spinbox)
            controls_layout.addLayout(freq_layout)
            
            # Sample rate control
            sr_layout = QVBoxLayout()
            sr_label = QLabel('Sample Rate:')
            self.sr_combo = QComboBox()
            self.sr_combo.addItems(['2.4 MHz', '2.048 MHz', '1.024 MHz'])
            self.sr_combo.currentTextChanged.connect(self.on_sample_rate_changed)
            sr_layout.addWidget(sr_label)
            sr_layout.addWidget(self.sr_combo)
            controls_layout.addLayout(sr_layout)
            
            # FFT size control
            fft_layout = QVBoxLayout()
            fft_label = QLabel('FFT Size:')
            self.fft_combo = QComboBox()
            self.fft_combo.addItems(['512', '1024', '2048', '4096'])
            self.fft_combo.setCurrentText('1024')
            self.fft_combo.currentTextChanged.connect(self.on_fft_size_changed)
            fft_layout.addWidget(fft_label)
            fft_layout.addWidget(self.fft_combo)
            controls_layout.addLayout(fft_layout)
            
            # Update rate control
            rate_layout = QVBoxLayout()
            rate_label = QLabel('Update Rate (ms):')
            self.rate_spinbox = QSpinBox()
            self.rate_spinbox.setRange(10, 500)
            self.rate_spinbox.setValue(self.update_interval)
            self.rate_spinbox.setSingleStep(10)
            self.rate_spinbox.valueChanged.connect(self.on_update_rate_changed)
            rate_layout.addWidget(rate_label)
            rate_layout.addWidget(self.rate_spinbox)
            controls_layout.addLayout(rate_layout)
            
            # Start/Stop button
            self.start_stop_btn = QPushButton('Start')
            self.start_stop_btn.clicked.connect(self.toggle_acquisition)
            controls_layout.addWidget(self.start_stop_btn)
            
            main_layout.addLayout(controls_layout)
            
            # SDR device selection panel
            sdr_layout = QHBoxLayout()
            sdr_label = QLabel('SDR Device:')
            self.sdr_combo = QComboBox()
            self.sdr_combo.addItem('No Device Detected')
            self.sdr_combo.currentIndexChanged.connect(self.on_sdr_device_changed)
            sdr_layout.addWidget(sdr_label)
            sdr_layout.addWidget(self.sdr_combo)
            
            # Scan button
            self.scan_btn = QPushButton('Scan for Devices')
            self.scan_btn.clicked.connect(self.scan_sdr_devices)
            sdr_layout.addWidget(self.scan_btn)
            
            # SDR status label
            self.sdr_status_label = QLabel('No SDR connected')
            self.sdr_status_label.setStyleSheet("color: orange;")
            sdr_layout.addWidget(self.sdr_status_label)
            sdr_layout.addStretch()
            
            main_layout.addLayout(sdr_layout)
            
            # Meshtastic device status panel
            meshtastic_layout = QHBoxLayout()
            meshtastic_label = QLabel('Meshtastic Device:')
            self.meshtastic_status_label = QLabel('Not detected')
            self.meshtastic_status_label.setStyleSheet("color: orange;")
            meshtastic_layout.addWidget(meshtastic_label)
            meshtastic_layout.addWidget(self.meshtastic_status_label)
            meshtastic_layout.addStretch()
            
            # LoRa status
            lora_label = QLabel('LoRa Status:')
            self.lora_status_label = QLabel('Disabled')
            self.lora_status_label.setStyleSheet("color: gray;")
            meshtastic_layout.addWidget(lora_label)
            meshtastic_layout.addWidget(self.lora_status_label)
            meshtastic_layout.addStretch()
            
            main_layout.addLayout(meshtastic_layout)
            
            # Status bar
            self.statusBar().showMessage('Ready - Click Start to begin acquisition')
            
        def update_display(self):
            """Update the waterfall display with new data"""
            if self.use_real_sdr and self.sdr_device.is_connected:
                # Get samples from real SDR device
                samples = self.sdr_device.read_samples(self.fft_size)
                if samples is None:
                    # Error reading from SDR, show message
                    self.statusBar().showMessage('Error reading from SDR device')
                    return
            else:
                # Get samples from simulated signal source (fallback)
                samples = self.signal_source.generate_samples(self.fft_size)
            
            # Compute FFT and convert to dB
            fft_db = compute_fft_db(samples, self.fft_size)
            
            # Update waterfall
            self.waterfall.update_waterfall(fft_db)
            
        def on_frequency_changed(self, value):
            """Handle center frequency change"""
            self.center_freq = value * 1e6
            self.signal_source.center_freq = self.center_freq
            
            # Update SDR device if connected
            if self.use_real_sdr and self.sdr_device.is_connected:
                self.sdr_device.set_center_freq(self.center_freq)
            
            self.waterfall.set_frequency_labels(self.center_freq, self.sample_rate)
            self.statusBar().showMessage(f'Center frequency: {value} MHz')
            
        def on_sample_rate_changed(self, value):
            """Handle sample rate change"""
            rate_map = {
                '2.4 MHz': 2.4e6,
                '2.048 MHz': 2.048e6,
                '1.024 MHz': 1.024e6
            }
            self.sample_rate = rate_map[value]
            self.signal_source.sample_rate = self.sample_rate
            
            # Update SDR device if connected
            if self.use_real_sdr and self.sdr_device.is_connected:
                self.sdr_device.set_sample_rate(self.sample_rate)
            
            self.waterfall.set_frequency_labels(self.center_freq, self.sample_rate)
            self.statusBar().showMessage(f'Sample rate: {value}')
            
        def on_fft_size_changed(self, value):
            """Handle FFT size change"""
            self.fft_size = int(value)
            self.waterfall.fft_size = self.fft_size
            # Reinitialize waterfall data
            self.waterfall.waterfall_data = np.zeros((self.waterfall.waterfall_height, self.fft_size))
            self.statusBar().showMessage(f'FFT size: {value}')
            
        def on_update_rate_changed(self, value):
            """Handle update rate change"""
            self.update_interval = value
            self.timer.setInterval(self.update_interval)
            self.statusBar().showMessage(f'Update rate: {value} ms')
            
        def toggle_acquisition(self):
            """Toggle signal acquisition on/off"""
            if self.is_running:
                # Stop acquisition
                self.timer.stop()
                self.is_running = False
                self.start_stop_btn.setText('Start')
                
                if self.use_real_sdr:
                    self.statusBar().showMessage('Stopped - SDR acquisition paused')
                else:
                    self.statusBar().showMessage('Stopped')
            else:
                # Start acquisition
                self.timer.start(self.update_interval)
                self.is_running = True
                self.start_stop_btn.setText('Stop')
                
                if self.use_real_sdr and self.sdr_device.is_connected:
                    self.statusBar().showMessage(f'Running - Reading from {self.sdr_device.device_type}')
                else:
                    self.statusBar().showMessage('Running - Using simulated data (no SDR connected)')
        
        def check_meshtastic_devices(self):
            """Check for Meshtastic devices and enable LoRa if detected"""
            detected_devices = self.meshtastic_detector.detect_devices()
            
            if detected_devices:
                # Device detected - enable LoRa communication
                device = detected_devices[0]  # Use first detected device
                device_info = self.meshtastic_detector.get_device_info(device)
                
                # Update UI
                device_text = f"{device_info['description']} ({device_info['device']})"
                self.meshtastic_status_label.setText(device_text)
                self.meshtastic_status_label.setStyleSheet("color: green;")
                
                # Connect LoRa communication if not already connected
                if not self.lora_comm.is_connected:
                    if self.lora_comm.connect(device_info['device']):
                        self.lora_status_label.setText('Enabled (915 MHz)')
                        self.lora_status_label.setStyleSheet("color: green;")
                        self.statusBar().showMessage(f'Meshtastic device connected: {device_text}')
                    else:
                        self.lora_status_label.setText('Connection failed')
                        self.lora_status_label.setStyleSheet("color: red;")
            else:
                # No device detected
                if self.lora_comm.is_connected:
                    self.lora_comm.disconnect()
                    self.statusBar().showMessage('Meshtastic device disconnected')
                
                self.meshtastic_status_label.setText('Not detected')
                self.meshtastic_status_label.setStyleSheet("color: orange;")
                self.lora_status_label.setText('Disabled')
                self.lora_status_label.setStyleSheet("color: gray;")
        
        def scan_sdr_devices(self):
            """Scan for available SDR devices and populate the combo box"""
            # Clear existing items
            self.sdr_combo.clear()
            
            # Check if RTL-SDR library is available
            if not RTLSDR_AVAILABLE:
                self.sdr_combo.addItem('RTL-SDR library not installed')
                self.sdr_status_label.setText('Install pyrtlsdr to use SDR devices')
                self.sdr_status_label.setStyleSheet("color: red;")
                self.statusBar().showMessage('RTL-SDR library not available. Install with: pip install pyrtlsdr')
                return
            
            # Scan for devices
            devices = self.sdr_device.detect_devices()
            
            if devices:
                # Add detected devices to combo box
                for dev in devices:
                    display_text = f"{dev['type']} - {dev['description']}"
                    self.sdr_combo.addItem(display_text, dev)
                
                # Update status
                self.sdr_status_label.setText(f'Found {len(devices)} device(s)')
                self.sdr_status_label.setStyleSheet("color: green;")
                self.statusBar().showMessage(f'Found {len(devices)} SDR device(s). Select a device and click Start.')
                
                # Auto-select first device
                if len(devices) > 0:
                    self.on_sdr_device_changed(0)
            else:
                # No devices found
                self.sdr_combo.addItem('No SDR devices found')
                self.sdr_status_label.setText('No SDR devices detected')
                self.sdr_status_label.setStyleSheet("color: orange;")
                self.statusBar().showMessage('No SDR devices found. Using simulated data.')
                self.use_real_sdr = False
        
        def on_sdr_device_changed(self, index):
            """Handle SDR device selection change"""
            device_data = self.sdr_combo.itemData(index)
            
            # Disconnect from any previous device
            if self.sdr_device.is_connected:
                self.sdr_device.disconnect()
                self.use_real_sdr = False
            
            if device_data is None:
                # No valid device selected
                self.use_real_sdr = False
                self.sdr_status_label.setText('No SDR connected')
                self.sdr_status_label.setStyleSheet("color: orange;")
                return
            
            # Try to connect to the selected device
            device_index = device_data['index']
            device_type = device_data['type']
            
            if self.sdr_device.connect(device_index, device_type):
                self.use_real_sdr = True
                self.sdr_status_label.setText(f'Connected to {device_type}')
                self.sdr_status_label.setStyleSheet("color: green;")
                self.statusBar().showMessage(f'Connected to {device_type}. Click Start to begin acquisition.')
                
                # Update device with current parameters
                self.sdr_device.set_sample_rate(self.sample_rate)
                self.sdr_device.set_center_freq(self.center_freq)
            else:
                self.use_real_sdr = False
                self.sdr_status_label.setText('Failed to connect')
                self.sdr_status_label.setStyleSheet("color: red;")
                self.statusBar().showMessage(f'Failed to connect to {device_type}')
    
    


def main():
    """Main entry point"""
    if not PYQT5_AVAILABLE:
        print("\n❌ ERROR: PyQt5 is not installed!")
        print("\nTo use the desktop GUI version, install PyQt5:")
        print("  pip install PyQt5")
        print("\nAlternatively, use the web version which works on all platforms:")
        print("  python waverider_web.py")
        print("\nOr use the universal launcher:")
        print("  python run.py")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    window = WaveRiderSDR()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
