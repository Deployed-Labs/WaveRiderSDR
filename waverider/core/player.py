"""
IQ Stream Playback for WaveRiderSDR

Provides functionality to play back previously recorded IQ streams.
"""

import h5py
import numpy as np
from typing import Optional, Callable


class IQPlayer:
    """Plays back recorded IQ streams"""
    
    def __init__(self):
        """Initialize IQ Player"""
        self.current_file = None
        self.dataset = None
        self.metadata = {}
        self.position = 0
        self.is_playing = False
        self.is_looping = False
    
    def load_recording(self, filepath: str) -> dict:
        """
        Load a recording file
        
        Args:
            filepath: Path to the HDF5 recording file
            
        Returns:
            Dictionary with recording metadata
        """
        self.close()
        
        try:
            self.current_file = h5py.File(filepath, 'r')
            self.dataset = self.current_file['iq_data']
            
            # Load metadata
            self.metadata = dict(self.current_file.attrs)
            self.position = 0
            
            return self.metadata
        except Exception as e:
            self.close()
            raise RuntimeError(f"Failed to load recording: {e}")
    
    def close(self):
        """Close the current recording file"""
        if self.current_file:
            self.current_file.close()
            self.current_file = None
            self.dataset = None
            self.metadata = {}
            self.position = 0
            self.is_playing = False
    
    def start_playback(self, loop: bool = False):
        """
        Start playback
        
        Args:
            loop: Whether to loop the playback
        """
        if not self.dataset:
            raise RuntimeError("No recording loaded")
        
        self.is_playing = True
        self.is_looping = loop
    
    def stop_playback(self):
        """Stop playback"""
        self.is_playing = False
    
    def pause_playback(self):
        """Pause playback"""
        self.is_playing = False
    
    def read_samples(self, num_samples: int) -> Optional[np.ndarray]:
        """
        Read samples from the recording
        
        Args:
            num_samples: Number of samples to read
            
        Returns:
            Complex IQ data array, or None if end reached
        """
        if not self.dataset:
            return None
        
        total_samples = self.dataset.shape[0]
        
        if self.position >= total_samples:
            if self.is_looping:
                self.position = 0
            else:
                self.is_playing = False
                return None
        
        # Read samples
        end_pos = min(self.position + num_samples, total_samples)
        samples = self.dataset[self.position:end_pos]
        self.position = end_pos
        
        return samples
    
    def seek(self, position: int):
        """
        Seek to a specific position
        
        Args:
            position: Sample position to seek to
        """
        if not self.dataset:
            return
        
        total_samples = self.dataset.shape[0]
        self.position = max(0, min(position, total_samples))
    
    def seek_time(self, time_seconds: float):
        """
        Seek to a specific time
        
        Args:
            time_seconds: Time in seconds to seek to
        """
        if not self.dataset or 'sample_rate' not in self.metadata:
            return
        
        sample_rate = self.metadata['sample_rate']
        position = int(time_seconds * sample_rate)
        self.seek(position)
    
    def get_playback_info(self) -> dict:
        """
        Get information about current playback
        
        Returns:
            Dictionary with playback information
        """
        if not self.dataset:
            return {}
        
        total_samples = self.dataset.shape[0]
        sample_rate = self.metadata.get('sample_rate', 1)
        
        return {
            'position': self.position,
            'total_samples': total_samples,
            'current_time': self.position / sample_rate,
            'total_time': total_samples / sample_rate,
            'is_playing': self.is_playing,
            'is_looping': self.is_looping,
            'progress': (self.position / total_samples * 100) if total_samples > 0 else 0
        }
    
    def get_metadata(self) -> dict:
        """Get recording metadata"""
        return self.metadata.copy()
