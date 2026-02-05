"""
Workspace Configuration Manager for WaveRiderSDR

Enables users to save and load custom workspace layouts.
"""

import os
import yaml
from typing import Dict, Any, Optional


class WorkspaceManager:
    """Manages workspace configurations"""
    
    def __init__(self, workspace_dir: str = "workspaces"):
        """
        Initialize Workspace Manager
        
        Args:
            workspace_dir: Directory to store workspace configurations
        """
        self.workspace_dir = workspace_dir
        self.current_workspace = None
        self.current_config = {}
        
        # Create workspace directory if it doesn't exist
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Create default workspace if it doesn't exist
        default_path = os.path.join(workspace_dir, "default.yaml")
        if not os.path.exists(default_path):
            self.save_workspace("default", self._get_default_config())
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default workspace configuration"""
        return {
            'name': 'default',
            'version': '1.0',
            'layout': {
                'main_window': {
                    'width': 1200,
                    'height': 800,
                    'x': 100,
                    'y': 100
                },
                'panels': {
                    'spectrum': {
                        'visible': True,
                        'position': 'top',
                        'height': 300
                    },
                    'waterfall': {
                        'visible': True,
                        'position': 'middle',
                        'height': 200
                    },
                    'controls': {
                        'visible': True,
                        'position': 'bottom',
                        'height': 150
                    },
                    'recording': {
                        'visible': True,
                        'position': 'right',
                        'width': 250
                    }
                },
                'toolbars': {
                    'main': {'visible': True},
                    'frequency': {'visible': True},
                    'recording': {'visible': True}
                }
            },
            'settings': {
                'auto_save': True,
                'remember_position': True
            }
        }
    
    def save_workspace(self, name: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Save current workspace configuration
        
        Args:
            name: Name of the workspace
            config: Configuration dictionary (uses current if None)
            
        Returns:
            Path to saved workspace file
        """
        if config is None:
            config = self.current_config
        
        if not config:
            config = self._get_default_config()
        
        # Ensure name is in config
        config['name'] = name
        
        # Generate filename
        filename = f"{name}.yaml"
        filepath = os.path.join(self.workspace_dir, filename)
        
        # Save to YAML file
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        self.current_workspace = name
        self.current_config = config
        
        return filepath
    
    def load_workspace(self, name: str) -> Dict[str, Any]:
        """
        Load a workspace configuration
        
        Args:
            name: Name of the workspace to load
            
        Returns:
            Configuration dictionary
        """
        filename = f"{name}.yaml"
        filepath = os.path.join(self.workspace_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Workspace '{name}' not found")
        
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        
        self.current_workspace = name
        self.current_config = config
        
        return config
    
    def list_workspaces(self) -> list:
        """
        List available workspaces
        
        Returns:
            List of workspace names
        """
        workspaces = []
        
        for filename in os.listdir(self.workspace_dir):
            if filename.endswith('.yaml'):
                name = filename[:-5]  # Remove .yaml extension
                workspaces.append(name)
        
        return sorted(workspaces)
    
    def delete_workspace(self, name: str):
        """
        Delete a workspace
        
        Args:
            name: Name of the workspace to delete
        """
        if name == 'default':
            raise ValueError("Cannot delete default workspace")
        
        filename = f"{name}.yaml"
        filepath = os.path.join(self.workspace_dir, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if self.current_workspace == name:
            self.load_workspace('default')
    
    def update_layout(self, layout_updates: Dict[str, Any]):
        """
        Update current workspace layout
        
        Args:
            layout_updates: Dictionary with layout updates
        """
        if not self.current_config:
            self.current_config = self._get_default_config()
        
        # Deep update the layout
        if 'layout' not in self.current_config:
            self.current_config['layout'] = {}
        
        self._deep_update(self.current_config['layout'], layout_updates)
    
    def _deep_update(self, base_dict: dict, update_dict: dict):
        """Recursively update nested dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current workspace configuration"""
        return self.current_config.copy()
    
    def get_current_workspace_name(self) -> Optional[str]:
        """Get current workspace name"""
        return self.current_workspace
