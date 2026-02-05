"""
Theme Dialog for WaveRiderSDR

Dialog for customizing UI theme and appearance.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QComboBox, QSlider, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt


class ThemeDialog(QDialog):
    """Dialog for theme customization"""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Theme Settings")
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        theme_select_layout = QHBoxLayout()
        theme_label = QLabel("Select Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.list_themes())
        self.theme_combo.setCurrentText(self.theme_manager.current_theme)
        theme_select_layout.addWidget(theme_label)
        theme_select_layout.addWidget(self.theme_combo)
        theme_layout.addLayout(theme_select_layout)
        
        # Theme description
        self.theme_description = QLabel()
        self.update_theme_description()
        self.theme_combo.currentTextChanged.connect(self.update_theme_description)
        theme_layout.addWidget(self.theme_description)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Font scaling
        font_group = QGroupBox("Accessibility")
        font_layout = QVBoxLayout()
        
        font_label = QLabel("Font Scale:")
        font_layout.addWidget(font_label)
        
        scale_layout = QHBoxLayout()
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(50, 200)  # 0.5x to 2.0x
        self.font_slider.setValue(int(self.theme_manager.get_font_scale() * 100))
        self.font_slider.setTickPosition(QSlider.TicksBelow)
        self.font_slider.setTickInterval(25)
        self.font_slider.valueChanged.connect(self.update_font_label)
        
        self.font_value_label = QLabel(f"{self.theme_manager.get_font_scale():.1f}x")
        
        scale_layout.addWidget(self.font_slider)
        scale_layout.addWidget(self.font_value_label)
        font_layout.addLayout(scale_layout)
        
        font_info = QLabel("Adjust font size for better readability")
        font_info.setWordWrap(True)
        font_layout.addWidget(font_info)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_and_apply)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def update_theme_description(self):
        """Update theme description label"""
        theme_name = self.theme_combo.currentText()
        descriptions = {
            'dark': 'Dark theme with blue accents, easy on the eyes',
            'light': 'Light theme with professional appearance',
            'high_contrast': 'High contrast theme for better accessibility'
        }
        self.theme_description.setText(descriptions.get(theme_name, ''))
    
    def update_font_label(self, value):
        """Update font scale label"""
        scale = value / 100.0
        self.font_value_label.setText(f"{scale:.1f}x")
    
    def apply_settings(self):
        """Apply theme settings"""
        theme_name = self.theme_combo.currentText()
        font_scale = self.font_slider.value() / 100.0
        
        self.theme_manager.set_theme(theme_name)
        self.theme_manager.set_font_scale(font_scale)
        
        QMessageBox.information(
            self,
            "Applied",
            "Theme settings applied. Some changes may require restarting the application."
        )
    
    def accept_and_apply(self):
        """Apply settings and close dialog"""
        self.apply_settings()
        self.accept()
