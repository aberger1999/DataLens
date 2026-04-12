"""
Workspace manager panel for organizing data files, graphs, and reports.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QGridLayout,
    QFrame, QScrollArea, QFileDialog, QLineEdit
)
from . import modal
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import os
import sys
import json
import shutil
from datetime import datetime

class WorkspaceCard(QFrame):
    """Card widget for displaying workspace information."""
    
    activated = pyqtSignal(int)
    deleted = pyqtSignal(int)
    
    def __init__(self, workspace_id, workspace_data, is_active=False):
        super().__init__()
        self.workspace_id = workspace_id
        self.workspace_data = workspace_data
        self.is_active = is_active
        self.init_ui()
        
    def init_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        if self.is_active:
            self.setStyleSheet("""
                WorkspaceCard {
                    background-color: #2a82da;
                    border: 2px solid #4a9eff;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                WorkspaceCard {
                    background-color: #2d2d2d;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    padding: 10px;
                }
                WorkspaceCard:hover {
                    background-color: #3d3d3d;
                    border: 1px solid #2a82da;
                }
            """)
        
        layout = QVBoxLayout(self)
        
        title_layout = QHBoxLayout()
        title_label = QLabel(f"Workspace {self.workspace_id}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        if self.is_active:
            active_badge = QLabel("● ACTIVE")
            active_badge.setStyleSheet("color: #4ade80; font-weight: bold;")
            title_layout.addWidget(active_badge)
        
        layout.addLayout(title_layout)
        
        if self.workspace_data.get('name'):
            name_label = QLabel(f"Name: {self.workspace_data['name']}")
            layout.addWidget(name_label)
        
        info_label = QLabel(
            f"Files: {self.workspace_data.get('file_count', 0)} | "
            f"Graphs: {self.workspace_data.get('graph_count', 0)} | "
            f"Reports: {self.workspace_data.get('report_count', 0)}"
        )
        info_label.setStyleSheet("color: #aaaaaa; font-size: 9pt;")
        layout.addWidget(info_label)
        
        if self.workspace_data.get('last_modified'):
            date_label = QLabel(f"Modified: {self.workspace_data['last_modified']}")
            date_label.setStyleSheet("color: #888888; font-size: 8pt;")
            layout.addWidget(date_label)
        
        button_layout = QHBoxLayout()
        
        if not self.is_active:
            activate_btn = QPushButton("Activate")
            activate_btn.clicked.connect(lambda: self.activated.emit(self.workspace_id))
            button_layout.addWidget(activate_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #dc2626;")
        delete_btn.clicked.connect(lambda: self.deleted.emit(self.workspace_id))
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)

class WorkspaceManagerPanel(QWidget):
    """Panel for managing workspaces."""
    
    workspace_changed = pyqtSignal(str)
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.active_workspace = None
        self.workspaces_dir = self._get_workspaces_dir()
        self.max_workspaces = 5
        self.init_workspace_structure()
        self.init_ui()
        self.load_workspaces()
        
    @staticmethod
    def _get_workspaces_dir():
        """Return a user-writable workspaces directory."""
        if getattr(sys, 'frozen', False):
            base = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'DataLens')
        else:
            base = '.'
        return os.path.join(base, 'workspaces')

    def init_workspace_structure(self):
        """Initialize workspace directory structure."""
        if not os.path.exists(self.workspaces_dir):
            os.makedirs(self.workspaces_dir)
        
        for i in range(1, self.max_workspaces + 1):
            workspace_path = os.path.join(self.workspaces_dir, f"workspace_{i}")
            if not os.path.exists(workspace_path):
                os.makedirs(workspace_path)
                os.makedirs(os.path.join(workspace_path, "data"))
                os.makedirs(os.path.join(workspace_path, "graphs"))
                os.makedirs(os.path.join(workspace_path, "reports"))
                
                metadata = {
                    "id": i,
                    "name": f"Workspace {i}",
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "file_count": 0,
                    "graph_count": 0,
                    "report_count": 0
                }
                
                with open(os.path.join(workspace_path, "metadata.json"), 'w') as f:
                    json.dump(metadata, f, indent=4)
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Workspace Manager")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_workspaces)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        info_label = QLabel(
            "Organize your data analysis projects into workspaces. "
            "Each workspace can store data files, graphs, and reports. "
            f"Maximum {self.max_workspaces} workspaces."
        )
        info_label.setWordWrap(True)
        # info_label.setStyleSheet("color: #aaaaaa; padding: 10px; background-color: #1e1e1e; border-radius: 5px;")
        layout.addWidget(info_label)
        
        active_workspace_group = QGroupBox("Active Workspace")
        active_layout = QVBoxLayout(active_workspace_group)
        
        self.active_workspace_label = QLabel("No workspace active")
        self.active_workspace_label.setStyleSheet("font-size: 11pt; color: #4ade80;")
        active_layout.addWidget(self.active_workspace_label)
        
        self.workspace_path_label = QLabel("")
        self.workspace_path_label.setStyleSheet("color: #888888; font-size: 9pt;")
        active_layout.addWidget(self.workspace_path_label)
        
        quick_actions_layout = QHBoxLayout()
        
        open_data_btn = QPushButton("Open Data Folder")
        open_data_btn.clicked.connect(self.open_data_folder)
        quick_actions_layout.addWidget(open_data_btn)
        
        open_graphs_btn = QPushButton("Open Graphs Folder")
        open_graphs_btn.clicked.connect(self.open_graphs_folder)
        quick_actions_layout.addWidget(open_graphs_btn)
        
        open_reports_btn = QPushButton("Open Reports Folder")
        open_reports_btn.clicked.connect(self.open_reports_folder)
        quick_actions_layout.addWidget(open_reports_btn)
        
        active_layout.addLayout(quick_actions_layout)
        layout.addWidget(active_workspace_group)
        
        workspaces_group = QGroupBox("Available Workspaces")
        workspaces_layout = QVBoxLayout(workspaces_group)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)
        
        self.workspaces_container = QWidget()
        self.workspaces_grid = QGridLayout(self.workspaces_container)
        self.workspaces_grid.setSpacing(15)
        
        scroll_area.setWidget(self.workspaces_container)
        workspaces_layout.addWidget(scroll_area)
        
        layout.addWidget(workspaces_group)
        
    def load_workspaces(self):
        """Load and display all workspaces."""
        for i in reversed(range(self.workspaces_grid.count())):
            self.workspaces_grid.itemAt(i).widget().setParent(None)
        
        row, col = 0, 0
        for i in range(1, self.max_workspaces + 1):
            workspace_path = os.path.join(self.workspaces_dir, f"workspace_{i}")
            metadata_path = os.path.join(workspace_path, "metadata.json")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                metadata['file_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "data")) if os.path.isfile(os.path.join(workspace_path, "data", f))])
                metadata['graph_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "graphs")) if f.endswith('.png')])
                metadata['report_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "reports")) if f.endswith(('.html', '.pdf'))])
                
                is_active = self.active_workspace == i
                card = WorkspaceCard(i, metadata, is_active)
                card.activated.connect(self.activate_workspace)
                card.deleted.connect(self.delete_workspace)
                
                self.workspaces_grid.addWidget(card, row, col)
                
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
    
    def activate_workspace(self, workspace_id):
        """Activate a workspace."""
        self.active_workspace = workspace_id
        workspace_path = os.path.join(self.workspaces_dir, f"workspace_{workspace_id}")
        
        metadata_path = os.path.join(workspace_path, "metadata.json")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.active_workspace_label.setText(f"Workspace {workspace_id}: {metadata['name']}")
        self.workspace_path_label.setText(f"Path: {os.path.abspath(workspace_path)}")
        
        self.workspace_changed.emit(workspace_path)
        self.load_workspaces()
        
        modal.show_info(
            self,
            "Workspace Activated",
            f"Workspace {workspace_id} is now active.\n\n"
            f"All data files, graphs, and reports will be saved to:\n{workspace_path}"
        )
    
    def delete_workspace(self, workspace_id):
        """Delete workspace contents."""
        confirmed = modal.show_question(
            self,
            "Delete Workspace",
            f"Are you sure you want to delete all contents of Workspace {workspace_id}?\n\n"
            "This will remove all data files, graphs, and reports in this workspace."
        )

        if confirmed:
            workspace_path = os.path.join(self.workspaces_dir, f"workspace_{workspace_id}")

            for folder in ["data", "graphs", "reports"]:
                folder_path = os.path.join(workspace_path, folder)
                if os.path.exists(folder_path):
                    for file in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
            
            metadata = {
                "id": workspace_id,
                "name": f"Workspace {workspace_id}",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file_count": 0,
                "graph_count": 0,
                "report_count": 0
            }
            
            with open(os.path.join(workspace_path, "metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=4)
            
            if self.active_workspace == workspace_id:
                self.active_workspace = None
                self.active_workspace_label.setText("No workspace active")
                self.workspace_path_label.setText("")
            
            self.load_workspaces()
            
            modal.show_info(
                self,
                "Workspace Deleted",
                f"Workspace {workspace_id} has been cleared."
            )
    
    def open_data_folder(self):
        """Open the data folder of active workspace."""
        if self.active_workspace:
            path = os.path.join(self.workspaces_dir, f"workspace_{self.active_workspace}", "data")
            os.startfile(os.path.abspath(path))
        else:
            modal.show_warning(self, "No Active Workspace", "Please activate a workspace first.")
    
    def open_graphs_folder(self):
        """Open the graphs folder of active workspace."""
        if self.active_workspace:
            path = os.path.join(self.workspaces_dir, f"workspace_{self.active_workspace}", "graphs")
            os.startfile(os.path.abspath(path))
        else:
            modal.show_warning(self, "No Active Workspace", "Please activate a workspace first.")
    
    def open_reports_folder(self):
        """Open the reports folder of active workspace."""
        if self.active_workspace:
            path = os.path.join(self.workspaces_dir, f"workspace_{self.active_workspace}", "reports")
            os.startfile(os.path.abspath(path))
        else:
            modal.show_warning(self, "No Active Workspace", "Please activate a workspace first.")
    
    def get_active_workspace_path(self):
        """Get the path of the active workspace."""
        if self.active_workspace:
            return os.path.join(self.workspaces_dir, f"workspace_{self.active_workspace}")
        return None
    
    def update_workspace_metadata(self):
        """Update metadata for active workspace."""
        if self.active_workspace:
            workspace_path = os.path.join(self.workspaces_dir, f"workspace_{self.active_workspace}")
            metadata_path = os.path.join(workspace_path, "metadata.json")
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata['file_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "data")) if os.path.isfile(os.path.join(workspace_path, "data", f))])
            metadata['graph_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "graphs")) if f.endswith('.png')])
            metadata['report_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "reports")) if f.endswith(('.html', '.pdf'))])
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            self.load_workspaces()
