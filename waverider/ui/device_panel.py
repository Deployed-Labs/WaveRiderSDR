"""
Device Panel for WaveRiderSDR

UI panel for managing and browsing SDR devices.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QListWidget, QListWidgetItem, QGroupBox,
                            QLineEdit, QTextEdit, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt


class DevicePanel(QWidget):
    """Panel for device database management"""
    
    def __init__(self, device_db):
        super().__init__()
        self.device_db = device_db
        self.init_ui()
        self.refresh_device_list()
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search devices...")
        self.search_input.textChanged.connect(self.search_devices)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Filter by type
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Type:")
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.addItems(self.device_db.get_device_types())
        self.type_filter.currentTextChanged.connect(self.filter_by_type)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.type_filter)
        layout.addLayout(filter_layout)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self.show_device_details)
        layout.addWidget(self.device_list)
        
        # Device details
        details_group = QGroupBox("Device Details")
        details_layout = QVBoxLayout()
        
        self.device_details = QTextEdit()
        self.device_details.setReadOnly(True)
        self.device_details.setMaximumHeight(200)
        details_layout.addWidget(self.device_details)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_device_list)
        button_layout.addWidget(self.refresh_button)
        
        layout.addLayout(button_layout)
    
    def refresh_device_list(self):
        """Refresh the device list"""
        self.device_list.clear()
        devices = self.device_db.list_devices()
        
        for device in devices:
            item = QListWidgetItem(f"{device['name']} ({device['manufacturer']})")
            item.setData(Qt.UserRole, device['id'])
            self.device_list.addItem(item)
    
    def search_devices(self, query: str):
        """Search devices by query"""
        self.device_list.clear()
        
        if not query:
            self.refresh_device_list()
            return
        
        devices = self.device_db.search_devices(query)
        
        for device in devices:
            item = QListWidgetItem(f"{device['name']} ({device['manufacturer']})")
            item.setData(Qt.UserRole, device['id'])
            self.device_list.addItem(item)
    
    def filter_by_type(self, device_type: str):
        """Filter devices by type"""
        self.device_list.clear()
        
        if device_type == "All Types":
            self.refresh_device_list()
            return
        
        devices = self.device_db.get_devices_by_type(device_type)
        
        for device in devices:
            item = QListWidgetItem(f"{device['name']} ({device['manufacturer']})")
            item.setData(Qt.UserRole, device['id'])
            self.device_list.addItem(item)
    
    def show_device_details(self, item):
        """Show details for selected device"""
        device_id = item.data(Qt.UserRole)
        device = self.device_db.get_device(device_id)
        
        if device:
            details = self.format_device_details(device)
            self.device_details.setPlainText(details)
    
    def format_device_details(self, device: dict) -> str:
        """Format device details for display"""
        freq_range = device.get('frequency_range', {})
        gain_range = device.get('gain_range', {})
        
        details = f"Name: {device.get('name', 'N/A')}\n"
        details += f"Manufacturer: {device.get('manufacturer', 'N/A')}\n"
        details += f"Type: {device.get('type', 'N/A')}\n"
        details += f"\nFrequency Range:\n"
        details += f"  {freq_range.get('min', 0)/1e6:.1f} MHz - {freq_range.get('max', 0)/1e6:.1f} MHz\n"
        
        sample_rates = device.get('sample_rates', [])
        if sample_rates:
            details += f"\nSample Rates:\n"
            for sr in sample_rates:
                details += f"  {sr/1e6:.3f} MHz\n"
        
        details += f"\nGain Range:\n"
        details += f"  {gain_range.get('min', 0)} - {gain_range.get('max', 0)} {gain_range.get('unit', 'dB')}\n"
        
        features = device.get('features', [])
        if features:
            details += f"\nFeatures:\n"
            for feature in features:
                details += f"  • {feature.replace('_', ' ').title()}\n"
        
        notes = device.get('notes', '')
        if notes:
            details += f"\nNotes:\n{notes}\n"
        
        return details
