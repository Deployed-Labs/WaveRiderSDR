"""
Workspace Dialog for WaveRiderSDR

Dialog for managing workspaces.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QListWidget, QListWidgetItem, QLineEdit,
                            QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt


class WorkspaceDialog(QDialog):
    """Dialog for workspace management"""
    
    def __init__(self, workspace_manager, parent=None):
        super().__init__(parent)
        self.workspace_manager = workspace_manager
        self.init_ui()
        self.refresh_workspace_list()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Manage Workspaces")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel("Select a workspace to load or manage your workspaces:")
        layout.addWidget(info_label)
        
        # Workspace list
        self.workspace_list = QListWidget()
        self.workspace_list.itemDoubleClicked.connect(self.load_selected_workspace)
        layout.addWidget(self.workspace_list)
        
        # Current workspace label
        self.current_label = QLabel()
        self.update_current_label()
        layout.addWidget(self.current_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.load_selected_workspace)
        button_layout.addWidget(self.load_button)
        
        self.save_button = QPushButton("Save As...")
        self.save_button.clicked.connect(self.save_new_workspace)
        button_layout.addWidget(self.save_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_selected_workspace)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def refresh_workspace_list(self):
        """Refresh the workspace list"""
        self.workspace_list.clear()
        workspaces = self.workspace_manager.list_workspaces()
        
        current = self.workspace_manager.get_current_workspace_name()
        
        for workspace in workspaces:
            item = QListWidgetItem(workspace)
            if workspace == current:
                item.setText(f"{workspace} (current)")
            self.workspace_list.addItem(item)
    
    def update_current_label(self):
        """Update current workspace label"""
        current = self.workspace_manager.get_current_workspace_name()
        self.current_label.setText(f"Current Workspace: {current or 'None'}")
    
    def load_selected_workspace(self):
        """Load the selected workspace"""
        current_item = self.workspace_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a workspace to load")
            return
        
        workspace_name = current_item.text().replace(" (current)", "")
        
        try:
            self.workspace_manager.load_workspace(workspace_name)
            self.refresh_workspace_list()
            self.update_current_label()
            QMessageBox.information(self, "Success", f"Loaded workspace: {workspace_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load workspace: {e}")
    
    def save_new_workspace(self):
        """Save current configuration as a new workspace"""
        name, ok = QInputDialog.getText(
            self,
            "Save Workspace",
            "Enter workspace name:"
        )
        
        if ok and name:
            try:
                self.workspace_manager.save_workspace(name)
                self.refresh_workspace_list()
                self.update_current_label()
                QMessageBox.information(self, "Success", f"Saved workspace: {name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save workspace: {e}")
    
    def delete_selected_workspace(self):
        """Delete the selected workspace"""
        current_item = self.workspace_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a workspace to delete")
            return
        
        workspace_name = current_item.text().replace(" (current)", "")
        
        if workspace_name == "default":
            QMessageBox.warning(self, "Warning", "Cannot delete the default workspace")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete workspace '{workspace_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.workspace_manager.delete_workspace(workspace_name)
                self.refresh_workspace_list()
                self.update_current_label()
                QMessageBox.information(self, "Success", f"Deleted workspace: {workspace_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete workspace: {e}")
