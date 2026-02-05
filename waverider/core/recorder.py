"""
IQ Stream Recorder for WaveRiderSDR

Provides functionality to record incoming IQ streams to files for offline analysis.
"""

import os
import time
import h5py
import numpy as np
from datetime import datetime
from typing import Optional


class IQRecorder:
    """Records IQ streams to HDF5 files"""
    
    def __init__(self, output_dir: str = "recordings"):
        """
        Initialize IQ Recorder
        
        Args:
            output_dir: Directory to store recordings
        """
        self.output_dir = output_dir
        self.is_recording = False
        self.current_file = None
        self.dataset = None
        self.sample_count = 0
        self.metadata = {}
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def start_recording(self, sample_rate: float, center_freq: float, 
                       metadata: Optional[dict] = None) -> str:
        """
        Start recording IQ data
        
        Args:
            sample_rate: Sample rate in Hz
            center_freq: Center frequency in Hz
            metadata: Additional metadata to store
            
        Returns:
            Path to the recording file
        """
        if self.is_recording:
            raise RuntimeError("Already recording")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iq_recording_{timestamp}.h5"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create HDF5 file
        self.current_file = h5py.File(filepath, 'w')
        
        # Create dataset for IQ data (complex64)
        self.dataset = self.current_file.create_dataset(
            'iq_data',
            shape=(0,),
            maxshape=(None,),
            dtype=np.complex64,
            chunks=(10000,)
        )
        
        # Store metadata
        self.metadata = {
            'sample_rate': sample_rate,
            'center_frequency': center_freq,
            'start_time': time.time(),
            'version': '1.0'
        }
        
        if metadata:
            self.metadata.update(metadata)
        
        for key, value in self.metadata.items():
            self.current_file.attrs[key] = value
        
        self.is_recording = True
        self.sample_count = 0
        
        return filepath
    
    def write_samples(self, iq_data: np.ndarray):
        """
        Write IQ samples to the recording
        
        Args:
            iq_data: Complex IQ data array
        """
        if not self.is_recording:
            raise RuntimeError("Not currently recording")
        
        # Resize dataset and append data
        current_size = self.dataset.shape[0]
        new_size = current_size + len(iq_data)
        self.dataset.resize((new_size,))
        self.dataset[current_size:new_size] = iq_data
        
        self.sample_count += len(iq_data)
    
    def stop_recording(self):
        """Stop recording and close the file"""
        if not self.is_recording:
            return
        
        # Update metadata with final information
        self.current_file.attrs['end_time'] = time.time()
        self.current_file.attrs['total_samples'] = self.sample_count
        
        # Close file
        self.current_file.close()
        self.current_file = None
        self.dataset = None
        self.is_recording = False
        self.sample_count = 0
        self.metadata = {}
    
    def get_recording_info(self) -> dict:
        """
        Get information about current recording
        
        Returns:
            Dictionary with recording information
        """
        if not self.is_recording:
            return {}
        
        return {
            'sample_count': self.sample_count,
            'duration': time.time() - self.metadata.get('start_time', 0),
            'sample_rate': self.metadata.get('sample_rate', 0),
            'center_frequency': self.metadata.get('center_frequency', 0)
        }
