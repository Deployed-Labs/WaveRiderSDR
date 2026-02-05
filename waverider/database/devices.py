"""
Device Compatibility Database for WaveRiderSDR

Manages a database of known SDR devices with pre-configured settings.
"""

import json
import os
from typing import Dict, List, Optional, Any


class DeviceDatabase:
    """Manages SDR device compatibility database"""
    
    # Pre-configured device definitions
    DEFAULT_DEVICES = [
        {
            'id': 'rtlsdr_generic',
            'name': 'RTL-SDR Generic',
            'manufacturer': 'Various',
            'type': 'RTL-SDR',
            'frequency_range': {
                'min': 24e6,
                'max': 1766e6,
                'unit': 'Hz'
            },
            'sample_rates': [250000, 1024000, 1536000, 1792000, 1920000, 2048000, 2400000, 2560000, 2800000, 3200000],
            'default_sample_rate': 2048000,
            'gain_range': {
                'min': 0,
                'max': 49.6,
                'step': 0.1,
                'unit': 'dB'
            },
            'features': ['tuner_agc', 'rtl_agc', 'direct_sampling'],
            'connection': 'USB',
            'notes': 'Generic RTL-SDR dongle based on RTL2832U chip'
        },
        {
            'id': 'hackrf_one',
            'name': 'HackRF One',
            'manufacturer': 'Great Scott Gadgets',
            'type': 'HackRF',
            'frequency_range': {
                'min': 1e6,
                'max': 6000e6,
                'unit': 'Hz'
            },
            'sample_rates': [2000000, 4000000, 8000000, 10000000, 12500000, 16000000, 20000000],
            'default_sample_rate': 10000000,
            'gain_range': {
                'min': 0,
                'max': 62,
                'step': 2,
                'unit': 'dB'
            },
            'features': ['tx_capable', 'wideband', 'bias_tee'],
            'connection': 'USB',
            'notes': 'Half-duplex transceiver with 20 MHz bandwidth'
        },
        {
            'id': 'airspy_mini',
            'name': 'Airspy Mini',
            'manufacturer': 'Airspy',
            'type': 'Airspy',
            'frequency_range': {
                'min': 24e6,
                'max': 1800e6,
                'unit': 'Hz'
            },
            'sample_rates': [3000000, 6000000],
            'default_sample_rate': 6000000,
            'gain_range': {
                'min': 0,
                'max': 21,
                'step': 1,
                'unit': 'dB'
            },
            'features': ['high_dynamic_range', 'low_noise'],
            'connection': 'USB',
            'notes': 'High-performance SDR with excellent sensitivity'
        },
        {
            'id': 'airspy_r2',
            'name': 'Airspy R2',
            'manufacturer': 'Airspy',
            'type': 'Airspy',
            'frequency_range': {
                'min': 24e6,
                'max': 1800e6,
                'unit': 'Hz'
            },
            'sample_rates': [2500000, 10000000],
            'default_sample_rate': 10000000,
            'gain_range': {
                'min': 0,
                'max': 21,
                'step': 1,
                'unit': 'dB'
            },
            'features': ['high_dynamic_range', 'low_noise', 'wideband'],
            'connection': 'USB',
            'notes': 'High-performance SDR with 10 MHz bandwidth'
        },
        {
            'id': 'sdrplay_rsp1a',
            'name': 'SDRplay RSP1A',
            'manufacturer': 'SDRplay',
            'type': 'SDRplay',
            'frequency_range': {
                'min': 1000,
                'max': 2000e6,
                'unit': 'Hz'
            },
            'sample_rates': [2000000, 5000000, 6000000, 7000000, 8000000, 9000000, 10000000],
            'default_sample_rate': 8000000,
            'gain_range': {
                'min': 0,
                'max': 47,
                'step': 1,
                'unit': 'dB'
            },
            'features': ['wideband', 'bias_tee', 'notch_filters'],
            'connection': 'USB',
            'notes': 'Wide-band SDR with 1 kHz to 2 GHz coverage'
        },
        {
            'id': 'bladerf_x40',
            'name': 'bladeRF x40',
            'manufacturer': 'Nuand',
            'type': 'bladeRF',
            'frequency_range': {
                'min': 300e6,
                'max': 3800e6,
                'unit': 'Hz'
            },
            'sample_rates': [1000000, 2000000, 4000000, 8000000, 16000000, 20000000, 40000000],
            'default_sample_rate': 10000000,
            'gain_range': {
                'min': -15,
                'max': 60,
                'step': 1,
                'unit': 'dB'
            },
            'features': ['tx_capable', 'full_duplex', 'fpga'],
            'connection': 'USB',
            'notes': 'Full-duplex transceiver with FPGA'
        }
    ]
    
    def __init__(self, db_path: str = "devices.json"):
        """
        Initialize Device Database
        
        Args:
            db_path: Path to the device database file
        """
        self.db_path = db_path
        self.devices = {}
        
        # Load or create database
        if os.path.exists(db_path):
            self.load_database()
        else:
            self.initialize_database()
    
    def initialize_database(self):
        """Initialize database with default devices"""
        self.devices = {device['id']: device for device in self.DEFAULT_DEVICES}
        self.save_database()
    
    def load_database(self):
        """Load database from file"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.devices = data.get('devices', {})
        except Exception as e:
            print(f"Error loading database: {e}")
            self.initialize_database()
    
    def save_database(self):
        """Save database to file"""
        data = {
            'version': '1.0',
            'devices': self.devices
        }
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_device(self, device: Dict[str, Any]) -> str:
        """
        Add a new device to the database
        
        Args:
            device: Device configuration dictionary
            
        Returns:
            Device ID
        """
        if 'id' not in device:
            raise ValueError("Device must have an 'id' field")
        
        device_id = device['id']
        self.devices[device_id] = device
        self.save_database()
        
        return device_id
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device configuration by ID
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device configuration dictionary or None
        """
        return self.devices.get(device_id)
    
    def update_device(self, device_id: str, updates: Dict[str, Any]):
        """
        Update device configuration
        
        Args:
            device_id: Device identifier
            updates: Dictionary with updates
        """
        if device_id not in self.devices:
            raise KeyError(f"Device '{device_id}' not found")
        
        self.devices[device_id].update(updates)
        self.save_database()
    
    def delete_device(self, device_id: str):
        """
        Delete device from database
        
        Args:
            device_id: Device identifier
        """
        if device_id in self.devices:
            del self.devices[device_id]
            self.save_database()
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """
        List all devices
        
        Returns:
            List of device configurations
        """
        return list(self.devices.values())
    
    def search_devices(self, query: str) -> List[Dict[str, Any]]:
        """
        Search devices by name, manufacturer, or type
        
        Args:
            query: Search query string
            
        Returns:
            List of matching devices
        """
        query = query.lower()
        results = []
        
        for device in self.devices.values():
            if (query in device.get('name', '').lower() or
                query in device.get('manufacturer', '').lower() or
                query in device.get('type', '').lower()):
                results.append(device)
        
        return results
    
    def get_devices_by_type(self, device_type: str) -> List[Dict[str, Any]]:
        """
        Get all devices of a specific type
        
        Args:
            device_type: Device type (e.g., 'RTL-SDR', 'HackRF')
            
        Returns:
            List of devices of the specified type
        """
        return [device for device in self.devices.values()
                if device.get('type') == device_type]
    
    def get_device_types(self) -> List[str]:
        """
        Get list of all device types in database
        
        Returns:
            List of unique device types
        """
        types = set()
        for device in self.devices.values():
            if 'type' in device:
                types.add(device['type'])
        return sorted(list(types))
