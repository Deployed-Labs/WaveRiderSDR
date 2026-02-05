"""
Main Window for WaveRiderSDR

Primary application window with all UI components.
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QMenuBar, QMenu, QAction, QStatusBar, QToolBar,
                            QMessageBox, QFileDialog, QDockWidget, QLabel,
                            QPushButton, QGroupBox, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from waverider.core.recorder import IQRecorder
from waverider.core.player import IQPlayer
from waverider.core.workspace import WorkspaceManager
from waverider.config.theme import ThemeManager
from waverider.database.devices import DeviceDatabase
from waverider.ui.recording_panel import RecordingPanel
from waverider.ui.device_panel import DevicePanel
from waverider.ui.workspace_dialog import WorkspaceDialog
from waverider.ui.theme_dialog import ThemeDialog


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.recorder = IQRecorder()
        self.player = IQPlayer()
        self.workspace_manager = WorkspaceManager()
        self.theme_manager = ThemeManager()
        self.device_db = DeviceDatabase()
        
        self.init_ui()
        self.apply_theme()
        self.load_default_workspace()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("WaveRiderSDR")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create spectrum/waterfall placeholder
        spectrum_group = QGroupBox("Spectrum Display")
        spectrum_layout = QVBoxLayout()
        spectrum_label = QLabel("Spectrum analyzer view would be displayed here")
        spectrum_label.setAlignment(Qt.AlignCenter)
        spectrum_label.setMinimumHeight(200)
        spectrum_layout.addWidget(spectrum_label)
        spectrum_group.setLayout(spectrum_layout)
        
        # Create controls placeholder
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout()
        controls_label = QLabel("SDR controls (frequency, gain, etc.) would be displayed here")
        controls_label.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(controls_label)
        controls_group.setLayout(controls_layout)
        
        # Add to main layout
        main_layout.addWidget(spectrum_group, stretch=3)
        main_layout.addWidget(controls_group, stretch=1)
        
        # Create dock widgets
        self.create_dock_widgets()
        
        # Create menus
        self.create_menus()
        
        # Create toolbars
        self.create_toolbars()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
    
    def create_dock_widgets(self):
        """Create dockable panels"""
        # Recording panel
        self.recording_dock = QDockWidget("Recording", self)
        self.recording_panel = RecordingPanel(self.recorder, self.player)
        self.recording_dock.setWidget(self.recording_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.recording_dock)
        
        # Device panel
        self.device_dock = QDockWidget("Devices", self)
        self.device_panel = DevicePanel(self.device_db)
        self.device_dock.setWidget(self.device_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.device_dock)
    
    def create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Recording...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_recording)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        view_menu.addAction(self.recording_dock.toggleViewAction())
        view_menu.addAction(self.device_dock.toggleViewAction())
        
        view_menu.addSeparator()
        
        theme_action = QAction("&Theme Settings...", self)
        theme_action.triggered.connect(self.show_theme_dialog)
        view_menu.addAction(theme_action)
        
        # Workspace menu
        workspace_menu = menubar.addMenu("&Workspace")
        
        save_workspace_action = QAction("&Save Workspace...", self)
        save_workspace_action.setShortcut("Ctrl+S")
        save_workspace_action.triggered.connect(self.save_workspace)
        workspace_menu.addAction(save_workspace_action)
        
        load_workspace_action = QAction("&Load Workspace...", self)
        load_workspace_action.setShortcut("Ctrl+L")
        load_workspace_action.triggered.connect(self.load_workspace)
        workspace_menu.addAction(load_workspace_action)
        
        manage_workspace_action = QAction("&Manage Workspaces...", self)
        manage_workspace_action.triggered.connect(self.show_workspace_dialog)
        workspace_menu.addAction(manage_workspace_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbars(self):
        """Create toolbars"""
        # Main toolbar
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        record_action = QAction("Record", self)
        record_action.triggered.connect(self.recording_panel.toggle_recording)
        toolbar.addAction(record_action)
        
        play_action = QAction("Play", self)
        play_action.triggered.connect(self.recording_panel.toggle_playback)
        toolbar.addAction(play_action)
        
        toolbar.addSeparator()
        
        device_action = QAction("Devices", self)
        device_action.triggered.connect(lambda: self.device_dock.setVisible(True))
        toolbar.addAction(device_action)
    
    def apply_theme(self):
        """Apply current theme to the application"""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def load_default_workspace(self):
        """Load default workspace configuration"""
        try:
            config = self.workspace_manager.load_workspace('default')
            self.apply_workspace_config(config)
        except Exception as e:
            print(f"Error loading default workspace: {e}")
    
    def apply_workspace_config(self, config: dict):
        """Apply workspace configuration to UI"""
        layout = config.get('layout', {})
        
        # Apply main window settings
        main_window = layout.get('main_window', {})
        if main_window:
            self.resize(main_window.get('width', 1200), 
                       main_window.get('height', 800))
            self.move(main_window.get('x', 100), 
                     main_window.get('y', 100))
        
        # Apply panel visibility
        panels = layout.get('panels', {})
        if 'recording' in panels:
            self.recording_dock.setVisible(panels['recording'].get('visible', True))
        
        self.statusBar().showMessage(f"Loaded workspace: {config.get('name', 'default')}")
    
    def save_workspace(self):
        """Save current workspace"""
        # Get current layout configuration
        config = self.workspace_manager.get_current_config()
        
        # Update with current window state
        config['layout']['main_window'] = {
            'width': self.width(),
            'height': self.height(),
            'x': self.x(),
            'y': self.y()
        }
        
        config['layout']['panels']['recording'] = {
            'visible': self.recording_dock.isVisible(),
            'position': 'right',
            'width': self.recording_dock.width()
        }
        
        # Save workspace
        name = self.workspace_manager.get_current_workspace_name() or 'default'
        self.workspace_manager.save_workspace(name, config)
        self.statusBar().showMessage(f"Workspace '{name}' saved")
    
    def load_workspace(self):
        """Show workspace load dialog"""
        self.show_workspace_dialog()
    
    def show_workspace_dialog(self):
        """Show workspace management dialog"""
        dialog = WorkspaceDialog(self.workspace_manager, self)
        if dialog.exec_():
            # Reload workspace if changed
            config = self.workspace_manager.get_current_config()
            self.apply_workspace_config(config)
    
    def show_theme_dialog(self):
        """Show theme settings dialog"""
        dialog = ThemeDialog(self.theme_manager, self)
        if dialog.exec_():
            self.apply_theme()
    
    def open_recording(self):
        """Open a recording file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Recording",
            "",
            "HDF5 Files (*.h5);;All Files (*)"
        )
        
        if filename:
            try:
                self.player.load_recording(filename)
                self.recording_panel.update_player_info()
                self.statusBar().showMessage(f"Loaded recording: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load recording: {e}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About WaveRiderSDR",
            "WaveRiderSDR v0.1.0\n\n"
            "The only SDR with full features and rolling updates.\n\n"
            "Features:\n"
            "• Recording and Playback\n"
            "• Configurable Workspaces\n"
            "• Customizable UI with Themes\n"
            "• Device Compatibility Database"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Auto-save workspace if enabled
        if self.workspace_manager.current_config.get('settings', {}).get('auto_save', True):
            self.save_workspace()
        
        # Stop recording if active
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        
        # Close player
        self.player.close()
        
        event.accept()
