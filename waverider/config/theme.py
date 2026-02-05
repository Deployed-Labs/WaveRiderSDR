"""
UI Theme Manager for WaveRiderSDR

Provides customizable theming, accessibility features, and UI customization.
"""

import os
import yaml
from typing import Dict, Any


class ThemeManager:
    """Manages UI themes and customization"""
    
    # Predefined themes
    THEMES = {
        'dark': {
            'name': 'Dark',
            'colors': {
                'background': '#2b2b2b',
                'foreground': '#ffffff',
                'accent': '#3daee9',
                'highlight': '#4a4a4a',
                'text': '#ffffff',
                'text_secondary': '#b0b0b0',
                'border': '#555555',
                'warning': '#f67400',
                'error': '#da4453',
                'success': '#27ae60'
            },
            'fonts': {
                'family': 'Arial',
                'size': 10,
                'size_title': 12,
                'size_heading': 14
            }
        },
        'light': {
            'name': 'Light',
            'colors': {
                'background': '#ffffff',
                'foreground': '#000000',
                'accent': '#0078d7',
                'highlight': '#e5e5e5',
                'text': '#000000',
                'text_secondary': '#666666',
                'border': '#cccccc',
                'warning': '#ff8c00',
                'error': '#c42b1c',
                'success': '#107c10'
            },
            'fonts': {
                'family': 'Arial',
                'size': 10,
                'size_title': 12,
                'size_heading': 14
            }
        },
        'high_contrast': {
            'name': 'High Contrast',
            'colors': {
                'background': '#000000',
                'foreground': '#ffffff',
                'accent': '#ffff00',
                'highlight': '#333333',
                'text': '#ffffff',
                'text_secondary': '#ffff00',
                'border': '#ffffff',
                'warning': '#ffff00',
                'error': '#ff0000',
                'success': '#00ff00'
            },
            'fonts': {
                'family': 'Arial',
                'size': 12,
                'size_title': 14,
                'size_heading': 16
            }
        }
    }
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize Theme Manager
        
        Args:
            config_dir: Directory to store UI configuration
        """
        self.config_dir = config_dir
        self.current_theme = 'dark'
        self.font_scale = 1.0
        self.custom_settings = {}
        
        os.makedirs(config_dir, exist_ok=True)
        self.load_settings()
    
    def load_settings(self):
        """Load UI settings from file"""
        settings_path = os.path.join(self.config_dir, "ui_settings.yaml")
        
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = yaml.safe_load(f)
                self.current_theme = settings.get('theme', 'dark')
                self.font_scale = settings.get('font_scale', 1.0)
                self.custom_settings = settings.get('custom', {})
        else:
            self.save_settings()
    
    def save_settings(self):
        """Save UI settings to file"""
        settings_path = os.path.join(self.config_dir, "ui_settings.yaml")
        
        settings = {
            'theme': self.current_theme,
            'font_scale': self.font_scale,
            'custom': self.custom_settings
        }
        
        with open(settings_path, 'w') as f:
            yaml.dump(settings, f, default_flow_style=False)
    
    def set_theme(self, theme_name: str):
        """
        Set the current theme
        
        Args:
            theme_name: Name of the theme to apply
        """
        if theme_name not in self.THEMES:
            raise ValueError(f"Unknown theme: {theme_name}")
        
        self.current_theme = theme_name
        self.save_settings()
    
    def get_theme(self, theme_name: str = None) -> Dict[str, Any]:
        """
        Get theme configuration
        
        Args:
            theme_name: Name of theme (uses current if None)
            
        Returns:
            Theme configuration dictionary
        """
        if theme_name is None:
            theme_name = self.current_theme
        
        if theme_name not in self.THEMES:
            theme_name = 'dark'
        
        theme = self.THEMES[theme_name].copy()
        
        # Apply font scaling
        theme['fonts'] = theme['fonts'].copy()
        for key, value in theme['fonts'].items():
            if key.startswith('size'):
                theme['fonts'][key] = int(value * self.font_scale)
        
        return theme
    
    def set_font_scale(self, scale: float):
        """
        Set font scaling factor
        
        Args:
            scale: Font scale factor (0.5 to 2.0)
        """
        self.font_scale = max(0.5, min(2.0, scale))
        self.save_settings()
    
    def get_stylesheet(self) -> str:
        """
        Generate Qt stylesheet from current theme
        
        Returns:
            Qt stylesheet string
        """
        theme = self.get_theme()
        colors = theme['colors']
        fonts = theme['fonts']
        
        stylesheet = f"""
            QMainWindow, QDialog, QWidget {{
                background-color: {colors['background']};
                color: {colors['text']};
                font-family: {fonts['family']};
                font-size: {fonts['size']}pt;
            }}
            
            QPushButton {{
                background-color: {colors['accent']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px 15px;
                border-radius: 3px;
                font-size: {fonts['size']}pt;
            }}
            
            QPushButton:hover {{
                background-color: {colors['highlight']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['border']};
            }}
            
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
                background-color: {colors['highlight']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 3px;
                font-size: {fonts['size']}pt;
            }}
            
            QLabel {{
                color: {colors['text']};
                font-size: {fonts['size']}pt;
            }}
            
            QGroupBox {{
                border: 1px solid {colors['border']};
                border-radius: 5px;
                margin-top: 10px;
                font-size: {fonts['size_title']}pt;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                color: {colors['text']};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            
            QMenuBar {{
                background-color: {colors['background']};
                color: {colors['text']};
                border-bottom: 1px solid {colors['border']};
            }}
            
            QMenuBar::item:selected {{
                background-color: {colors['highlight']};
            }}
            
            QMenu {{
                background-color: {colors['background']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
            
            QMenu::item:selected {{
                background-color: {colors['highlight']};
            }}
            
            QStatusBar {{
                background-color: {colors['background']};
                color: {colors['text_secondary']};
                border-top: 1px solid {colors['border']};
            }}
            
            QToolBar {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                spacing: 3px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
            }}
            
            QTabBar::tab {{
                background-color: {colors['highlight']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px 10px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['accent']};
            }}
            
            QSlider::groove:horizontal {{
                border: 1px solid {colors['border']};
                height: 8px;
                background: {colors['highlight']};
            }}
            
            QSlider::handle:horizontal {{
                background: {colors['accent']};
                border: 1px solid {colors['border']};
                width: 18px;
                margin: -5px 0;
                border-radius: 3px;
            }}
        """
        
        return stylesheet
    
    def list_themes(self) -> list:
        """
        Get list of available themes
        
        Returns:
            List of theme names
        """
        return list(self.THEMES.keys())
    
    def get_font_scale(self) -> float:
        """Get current font scale"""
        return self.font_scale
