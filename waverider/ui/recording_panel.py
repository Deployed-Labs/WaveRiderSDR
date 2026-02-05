"""
Recording Panel for WaveRiderSDR

UI panel for controlling recording and playback.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QProgressBar, QGroupBox, QFileDialog,
                            QMessageBox)
from PyQt5.QtCore import QTimer, Qt
import numpy as np


class RecordingPanel(QWidget):
    """Panel for recording and playback controls"""
    
    def __init__(self, recorder, player):
        super().__init__()
        self.recorder = recorder
        self.player = player
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # Update every 100ms
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Recording section
        record_group = QGroupBox("Recording")
        record_layout = QVBoxLayout()
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        record_layout.addWidget(self.record_button)
        
        self.record_status = QLabel("Status: Idle")
        record_layout.addWidget(self.record_status)
        
        self.record_info = QLabel("Duration: 0s | Samples: 0")
        record_layout.addWidget(self.record_info)
        
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        
        # Playback section
        playback_group = QGroupBox("Playback")
        playback_layout = QVBoxLayout()
        
        # Playback controls
        control_layout = QHBoxLayout()
        
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.load_recording)
        control_layout.addWidget(self.load_button)
        
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setEnabled(False)
        control_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        playback_layout.addLayout(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        playback_layout.addWidget(self.progress_bar)
        
        # Playback info
        self.playback_info = QLabel("No recording loaded")
        playback_layout.addWidget(self.playback_info)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        layout.addStretch()
    
    def toggle_recording(self):
        """Toggle recording on/off"""
        if self.recorder.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start recording"""
        try:
            # Use sample values for demonstration
            sample_rate = 2.048e6  # 2.048 MHz
            center_freq = 100e6  # 100 MHz
            
            filepath = self.recorder.start_recording(sample_rate, center_freq)
            self.record_button.setText("Stop Recording")
            self.record_status.setText(f"Status: Recording")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop recording"""
        self.recorder.stop_recording()
        self.record_button.setText("Start Recording")
        self.record_status.setText("Status: Idle")
        self.record_info.setText("Duration: 0s | Samples: 0")
    
    def load_recording(self):
        """Load a recording file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Recording",
            self.recorder.output_dir,
            "HDF5 Files (*.h5);;All Files (*)"
        )
        
        if filename:
            try:
                metadata = self.player.load_recording(filename)
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(True)
                self.update_player_info()
                
                # Show metadata
                sample_rate = metadata.get('sample_rate', 0) / 1e6
                center_freq = metadata.get('center_frequency', 0) / 1e6
                QMessageBox.information(
                    self,
                    "Recording Loaded",
                    f"Sample Rate: {sample_rate:.3f} MHz\n"
                    f"Center Frequency: {center_freq:.3f} MHz"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load recording: {e}")
    
    def toggle_playback(self):
        """Toggle playback on/off"""
        if self.player.is_playing:
            self.player.pause_playback()
            self.play_button.setText("Play")
        else:
            self.player.start_playback(loop=False)
            self.play_button.setText("Pause")
    
    def stop_playback(self):
        """Stop playback"""
        self.player.stop_playback()
        self.player.seek(0)
        self.play_button.setText("Play")
        self.progress_bar.setValue(0)
    
    def update_display(self):
        """Update display with current status"""
        # Update recording info
        if self.recorder.is_recording:
            info = self.recorder.get_recording_info()
            duration = info.get('duration', 0)
            samples = info.get('sample_count', 0)
            self.record_info.setText(f"Duration: {duration:.1f}s | Samples: {samples}")
            
            # Simulate recording by writing dummy samples
            # In a real application, this would come from the SDR device
            if samples % 10000 == 0:  # Write samples periodically
                dummy_samples = np.random.randn(1000) + 1j * np.random.randn(1000)
                self.recorder.write_samples(dummy_samples.astype(np.complex64))
        
        # Update playback info
        if self.player.dataset:
            self.update_player_info()
    
    def update_player_info(self):
        """Update playback information"""
        info = self.player.get_playback_info()
        
        if info:
            current_time = info.get('current_time', 0)
            total_time = info.get('total_time', 0)
            progress = info.get('progress', 0)
            
            self.playback_info.setText(
                f"Time: {current_time:.1f}s / {total_time:.1f}s"
            )
            self.progress_bar.setValue(int(progress))
            
            # Simulate playback by reading samples
            if self.player.is_playing:
                samples = self.player.read_samples(1000)
                # In a real application, these samples would be sent to the SDR for output
