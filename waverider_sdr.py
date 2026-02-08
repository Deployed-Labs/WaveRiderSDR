"""
WaveRiderSDR - Software Defined Radio with Waterfall Visualization
Main application entry point - Desktop GUI version
"""

import sys
import numpy as np

# Import common utilities
from waverider_common import (MeshtasticDetector, LoRaCommunication, SignalGenerator, 
                             compute_fft_db, SDRDevice, RTLSDR_AVAILABLE,
                             AudioDemodulator, FMDemodulator, AMDemodulator, SSBDemodulator,
                             AudioPlayer, AUDIO_AVAILABLE, WaterfallSettings, BandPlan)

# Check for PyQt5 availability
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QLabel, QSlider, 
                                 QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox)
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
        
        def set_colormap(self, colormap):
            """Set waterfall colormap
            
            Args:
                colormap: Matplotlib colormap name
            """
            self.im.set_cmap(colormap)
            self.draw()
        
        def set_range(self, min_db, max_db):
            """Set display range
            
            Args:
                min_db: Minimum dB level
                max_db: Maximum dB level
            """
            self.im.set_clim(vmin=min_db, vmax=max_db)
            self.draw()
            
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
            
            # Audio demodulation and playback
            self.audio_enabled = False
            self.modulation_mode = 'FM'  # Default modulation
            self.audio_rate = 48000
            self.audio_player = AudioPlayer(sample_rate=self.audio_rate)
            self.demodulator = FMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
            
            # Waterfall settings
            self.waterfall_settings = WaterfallSettings()
            
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
            
            # Band plan selector
            band_layout = QVBoxLayout()
            band_label = QLabel('Quick Band:')
            self.band_combo = QComboBox()
            self.band_combo.addItem('-- Select Band --')
            for band_name in BandPlan.get_all_bands():
                self.band_combo.addItem(band_name)
            self.band_combo.currentTextChanged.connect(self.on_band_selected)
            band_layout.addWidget(band_label)
            band_layout.addWidget(self.band_combo)
            controls_layout.addLayout(band_layout)
            
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
            
            # Audio controls panel
            audio_layout = QHBoxLayout()
            
            # Audio enable checkbox
            self.audio_enable_check = QCheckBox('Enable Audio Output')
            self.audio_enable_check.setChecked(False)
            self.audio_enable_check.stateChanged.connect(self.on_audio_enable_changed)
            audio_layout.addWidget(self.audio_enable_check)
            
            # Modulation selector
            mod_label = QLabel('Modulation:')
            self.mod_combo = QComboBox()
            self.mod_combo.addItems(['FM', 'AM', 'USB', 'LSB'])
            self.mod_combo.setCurrentText('FM')
            self.mod_combo.currentTextChanged.connect(self.on_modulation_changed)
            audio_layout.addWidget(mod_label)
            audio_layout.addWidget(self.mod_combo)
            
            # Squelch control
            squelch_label = QLabel('Squelch (dB):')
            self.squelch_slider = QSlider(Qt.Horizontal)
            self.squelch_slider.setRange(-100, 0)
            self.squelch_slider.setValue(-50)
            self.squelch_slider.setTickPosition(QSlider.TicksBelow)
            self.squelch_slider.setTickInterval(10)
            self.squelch_slider.valueChanged.connect(self.on_squelch_changed)
            self.squelch_value_label = QLabel('-50')
            audio_layout.addWidget(squelch_label)
            audio_layout.addWidget(self.squelch_slider)
            audio_layout.addWidget(self.squelch_value_label)
            
            # Audio status label
            self.audio_status_label = QLabel('Audio: Disabled')
            self.audio_status_label.setStyleSheet("color: gray;")
            audio_layout.addWidget(self.audio_status_label)
            
            # Show warning if audio not available
            if not AUDIO_AVAILABLE:
                audio_warning = QLabel('⚠️ Audio library not installed')
                audio_warning.setStyleSheet("color: orange;")
                audio_layout.addWidget(audio_warning)
                self.audio_enable_check.setEnabled(False)
            
            audio_layout.addStretch()
            main_layout.addLayout(audio_layout)
            
            # Gain controls panel
            gain_layout = QHBoxLayout()
            
            # RF Gain
            rf_gain_label = QLabel('RF Gain (dB):')
            self.rf_gain_slider = QSlider(Qt.Horizontal)
            self.rf_gain_slider.setRange(0, 50)
            self.rf_gain_slider.setValue(40)
            self.rf_gain_slider.setTickPosition(QSlider.TicksBelow)
            self.rf_gain_slider.setTickInterval(10)
            self.rf_gain_slider.valueChanged.connect(self.on_rf_gain_changed)
            self.rf_gain_value_label = QLabel('40')
            gain_layout.addWidget(rf_gain_label)
            gain_layout.addWidget(self.rf_gain_slider)
            gain_layout.addWidget(self.rf_gain_value_label)
            
            gain_layout.addStretch()
            main_layout.addLayout(gain_layout)
            
            # Waterfall settings panel
            waterfall_layout = QHBoxLayout()
            
            # Colormap selector
            colormap_label = QLabel('Colormap:')
            self.colormap_combo = QComboBox()
            self.colormap_combo.addItems(['viridis', 'plasma', 'inferno', 'magma', 'hot', 'cool', 'rainbow', 'grayscale', 'turbo'])
            self.colormap_combo.setCurrentText('viridis')
            self.colormap_combo.currentTextChanged.connect(self.on_colormap_changed)
            waterfall_layout.addWidget(colormap_label)
            waterfall_layout.addWidget(self.colormap_combo)
            
            # Min dB range
            min_db_label = QLabel('Min (dB):')
            self.min_db_spinbox = QSpinBox()
            self.min_db_spinbox.setRange(-120, -10)
            self.min_db_spinbox.setValue(-80)
            self.min_db_spinbox.valueChanged.connect(self.on_range_changed)
            waterfall_layout.addWidget(min_db_label)
            waterfall_layout.addWidget(self.min_db_spinbox)
            
            # Max dB range
            max_db_label = QLabel('Max (dB):')
            self.max_db_spinbox = QSpinBox()
            self.max_db_spinbox.setRange(-10, 20)
            self.max_db_spinbox.setValue(0)
            self.max_db_spinbox.valueChanged.connect(self.on_range_changed)
            waterfall_layout.addWidget(max_db_label)
            waterfall_layout.addWidget(self.max_db_spinbox)
            
            # Peak hold checkbox
            self.peak_hold_check = QCheckBox('Peak Hold')
            self.peak_hold_check.setChecked(False)
            self.peak_hold_check.stateChanged.connect(self.on_peak_hold_changed)
            waterfall_layout.addWidget(self.peak_hold_check)
            
            waterfall_layout.addStretch()
            main_layout.addLayout(waterfall_layout)
            
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
            
            # Apply waterfall processing (contrast, brightness, peak hold)
            fft_processed = self.waterfall_settings.apply_processing(fft_db)
            
            # Update waterfall
            self.waterfall.update_waterfall(fft_processed)
            
            # Process audio if enabled (with squelch)
            if self.audio_enabled and self.audio_player.is_active():
                # Detect if signal is strong enough (squelch)
                if self.demodulator.detect_signal(samples):
                    # Demodulate to audio
                    audio_samples = self.demodulator.demodulate(samples)
                    
                    # Play audio
                    self.audio_player.play(audio_samples)
                    
                    # Update status with signal strength
                    signal_strength = self.demodulator.get_signal_strength()
                    self.audio_status_label.setText(f'Audio: Playing ({self.modulation_mode}) {signal_strength:.1f} dB')
                    self.audio_status_label.setStyleSheet("color: green;")
                else:
                    # No strong signal detected (below squelch)
                    signal_strength = self.demodulator.get_signal_strength()
                    self.audio_status_label.setText(f'Audio: Squelched ({signal_strength:.1f} dB)')
                    self.audio_status_label.setStyleSheet("color: orange;")
            
        def on_frequency_changed(self, value):
            """Handle center frequency change"""
            self.center_freq = value * 1e6
            self.signal_source.center_freq = self.center_freq
            
            # Update SDR device if connected
            if self.use_real_sdr and self.sdr_device.is_connected:
                self.sdr_device.set_center_freq(self.center_freq)
            
            self.waterfall.set_frequency_labels(self.center_freq, self.sample_rate)
            self.statusBar().showMessage(f'Center frequency: {value} MHz')
        
        def on_band_selected(self, band_name):
            """Handle band plan selection"""
            if band_name == '-- Select Band --':
                return
            
            band_info = BandPlan.get_band_info(band_name)
            if band_info:
                # Set center frequency
                center_freq_mhz = band_info['center'] / 1e6
                self.freq_spinbox.setValue(center_freq_mhz)
                
                # Optionally set modulation mode
                recommended_mode = band_info.get('mode', 'FM')
                if recommended_mode in ['FM', 'AM', 'USB', 'LSB']:
                    self.mod_combo.setCurrentText(recommended_mode)
                elif recommended_mode == 'WFM':
                    self.mod_combo.setCurrentText('FM')  # Use FM for wideband
                
                # Show info
                desc = band_info.get('description', band_name)
                freq_range = f"{band_info['start']/1e6:.3f} - {band_info['end']/1e6:.3f} MHz"
                self.statusBar().showMessage(f'{desc} | {freq_range} | Mode: {recommended_mode}')
            
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
        
        def on_audio_enable_changed(self, state):
            """Handle audio enable/disable"""
            self.audio_enabled = (state == Qt.Checked)
            
            if self.audio_enabled:
                if self.audio_player.start():
                    self.audio_status_label.setText(f'Audio: Ready ({self.modulation_mode})')
                    self.audio_status_label.setStyleSheet("color: blue;")
                    self.statusBar().showMessage('Audio output enabled')
                else:
                    self.audio_enabled = False
                    self.audio_enable_check.setChecked(False)
                    self.audio_status_label.setText('Audio: Failed to start')
                    self.audio_status_label.setStyleSheet("color: red;")
                    self.statusBar().showMessage('Failed to start audio output')
            else:
                self.audio_player.stop()
                self.audio_status_label.setText('Audio: Disabled')
                self.audio_status_label.setStyleSheet("color: gray;")
                self.statusBar().showMessage('Audio output disabled')
        
        def on_modulation_changed(self, value):
            """Handle modulation mode change"""
            self.modulation_mode = value
            
            # Create appropriate demodulator
            if value == 'FM':
                self.demodulator = FMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
            elif value == 'AM':
                self.demodulator = AMDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate)
            elif value == 'USB':
                self.demodulator = SSBDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate, mode='USB')
            elif value == 'LSB':
                self.demodulator = SSBDemodulator(sample_rate=self.sample_rate, audio_rate=self.audio_rate, mode='LSB')
            
            # Restore squelch setting
            self.demodulator.set_squelch(self.squelch_slider.value())
            
            self.statusBar().showMessage(f'Modulation mode: {value}')
            if self.audio_enabled:
                self.audio_status_label.setText(f'Audio: Ready ({self.modulation_mode})')
        
        def on_squelch_changed(self, value):
            """Handle squelch threshold change"""
            self.squelch_value_label.setText(str(value))
            self.demodulator.set_squelch(value)
            self.statusBar().showMessage(f'Squelch: {value} dB')
        
        def on_rf_gain_changed(self, value):
            """Handle RF gain change"""
            self.rf_gain_value_label.setText(str(value))
            
            # Apply to SDR device if connected
            if self.use_real_sdr and self.sdr_device.is_connected:
                # For RTL-SDR, gain is in tenths of dB
                self.sdr_device.set_gain(value / 10.0)
                self.statusBar().showMessage(f'RF Gain: {value} dB')
        
        def on_colormap_changed(self, value):
            """Handle colormap change"""
            self.waterfall_settings.set_colormap(value)
            self.waterfall.set_colormap(self.waterfall_settings.colormap)
            self.statusBar().showMessage(f'Colormap: {value}')
        
        def on_range_changed(self):
            """Handle waterfall range change"""
            min_db = self.min_db_spinbox.value()
            max_db = self.max_db_spinbox.value()
            self.waterfall_settings.set_range(min_db, max_db)
            self.waterfall.set_range(min_db, max_db)
            self.statusBar().showMessage(f'Waterfall range: {min_db} to {max_db} dB')
        
        def on_peak_hold_changed(self, state):
            """Handle peak hold enable/disable"""
            self.waterfall_settings.peak_hold = (state == Qt.Checked)
            if self.waterfall_settings.peak_hold:
                self.statusBar().showMessage('Peak hold enabled')
            else:
                self.waterfall_settings.peak_buffer = None  # Reset peak buffer
                self.statusBar().showMessage('Peak hold disabled')
            
        def toggle_acquisition(self):
            """Toggle signal acquisition on/off"""
            if self.is_running:
                # Stop acquisition
                self.timer.stop()
                self.is_running = False
                self.start_stop_btn.setText('Start')
                
                # Stop audio if enabled
                if self.audio_enabled:
                    self.audio_player.stop()
                    self.audio_enabled = False
                    self.audio_enable_check.setChecked(False)
                    self.audio_status_label.setText('Audio: Disabled')
                    self.audio_status_label.setStyleSheet("color: gray;")
                
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
