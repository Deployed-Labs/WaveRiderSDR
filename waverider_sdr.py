#!/usr/bin/env python3
"""
WaveRiderSDR - Software Defined Radio with Waterfall Visualization
Main application entry point
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, 
                             QComboBox, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy import signal as sp_signal
import matplotlib.pyplot as plt


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


class SignalGenerator:
    """Generate simulated SDR signals for demonstration"""
    
    def __init__(self, sample_rate=2.4e6, center_freq=100e6):
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.time = 0
        
    def generate_samples(self, num_samples):
        """Generate simulated RF samples
        
        Args:
            num_samples: Number of samples to generate
            
        Returns:
            Complex IQ samples
        """
        # Generate time array
        t = np.arange(num_samples) / self.sample_rate + self.time
        self.time += num_samples / self.sample_rate
        
        # Create a complex signal with multiple components
        # 1. Carrier wave
        signal = np.exp(2j * np.pi * 0 * t)
        
        # 2. Add some modulated signals at different frequencies
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


class WaveRiderSDR(QMainWindow):
    """Main application window for WaveRiderSDR"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('WaveRiderSDR - Waterfall Visualization')
        self.setGeometry(100, 100, 1000, 700)
        
        # Initialize signal source (using simulated data for now)
        self.sample_rate = 2.4e6  # 2.4 MHz
        self.center_freq = 100e6  # 100 MHz
        self.signal_source = SignalGenerator(self.sample_rate, self.center_freq)
        
        # FFT parameters
        self.fft_size = 1024
        self.update_interval = 50  # ms
        
        # Setup UI
        self.setup_ui()
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(self.update_interval)
        
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
        self.start_stop_btn = QPushButton('Stop')
        self.start_stop_btn.clicked.connect(self.toggle_acquisition)
        controls_layout.addWidget(self.start_stop_btn)
        
        main_layout.addLayout(controls_layout)
        
        # Status bar
        self.statusBar().showMessage('Running with simulated signal source')
        
    def update_display(self):
        """Update the waterfall display with new data"""
        # Get samples from signal source
        samples = self.signal_source.generate_samples(self.fft_size)
        
        # Apply window function
        window = np.hamming(len(samples))
        samples_windowed = samples * window
        
        # Compute FFT
        fft = np.fft.fftshift(np.fft.fft(samples_windowed))
        
        # Convert to dB
        fft_mag = np.abs(fft)
        fft_db = 20 * np.log10(fft_mag + 1e-10)  # Add small value to avoid log(0)
        
        # Update waterfall
        self.waterfall.update_waterfall(fft_db)
        
    def on_frequency_changed(self, value):
        """Handle center frequency change"""
        self.center_freq = value * 1e6
        self.signal_source.center_freq = self.center_freq
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
        if self.timer.isActive():
            self.timer.stop()
            self.start_stop_btn.setText('Start')
            self.statusBar().showMessage('Stopped')
        else:
            self.timer.start(self.update_interval)
            self.start_stop_btn.setText('Stop')
            self.statusBar().showMessage('Running')


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = WaveRiderSDR()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
