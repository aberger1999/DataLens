"""
Modern home screen for workspace selection and settings.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QDialog, QLineEdit, QMessageBox, QGroupBox,
    QComboBox, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from ..theme import get_colors, RADIUS_LG, RADIUS_MD
import os
import json
from datetime import datetime

class WorkspaceCard(QFrame):
    """Modern card widget for workspace selection."""

    clicked = pyqtSignal(int)
    deleted = pyqtSignal(int)
    renamed = pyqtSignal(int)

    def __init__(self, workspace_id, workspace_data, theme="dark"):
        super().__init__()
        self.workspace_id = workspace_id
        self.workspace_data = workspace_data
        self.current_theme = theme
        self.init_ui()

    def init_ui(self):
        c = get_colors(self.current_theme)

        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(200)
        self.setMaximumWidth(320)
        self.update_theme()

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Top row: icon + action buttons
        top_layout = QHBoxLayout()

        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 36px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(icon_label)

        top_layout.addStretch()

        rename_btn = QPushButton("✏️")
        rename_btn.setFixedSize(34, 34)
        rename_btn.setToolTip("Rename workspace")
        rename_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                border: none;
                border-radius: 17px;
                font-size: 16px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
        """)
        rename_btn.clicked.connect(lambda: self.renamed.emit(self.workspace_id))
        top_layout.addWidget(rename_btn)

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(34, 34)
        delete_btn.setToolTip("Delete workspace")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['danger']};
                border: none;
                border-radius: 17px;
                font-size: 16px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['danger_hover']};
            }}
        """)
        delete_btn.clicked.connect(lambda: self.deleted.emit(self.workspace_id))
        top_layout.addWidget(delete_btn)

        layout.addLayout(top_layout)

        # Workspace name
        name_label = QLabel(self.workspace_data.get('name', f'Workspace {self.workspace_id}'))
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("background: transparent;")
        layout.addWidget(name_label)

        # Stats
        stats_text = (
            f"{self.workspace_data.get('file_count', 0)} files  ·  "
            f"{self.workspace_data.get('graph_count', 0)} graphs  ·  "
            f"{self.workspace_data.get('report_count', 0)} reports"
        )
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 9pt; background: transparent;")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stats_label)

        if self.workspace_data.get('last_modified'):
            date_label = QLabel(f"Modified: {self.workspace_data['last_modified']}")
            date_label.setStyleSheet(f"color: {c['text_disabled']}; font-size: 8pt; background: transparent;")
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(date_label)

        layout.addStretch()

    def update_theme(self):
        c = get_colors(self.current_theme)
        self.setStyleSheet(f"""
            WorkspaceCard {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border_subtle']};
                border-radius: {RADIUS_LG};
                padding: 20px;
            }}
            WorkspaceCard:hover {{
                background-color: {c['bg_tertiary']};
                border: 1px solid {c['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.workspace_id)
        super().mousePressEvent(event)

class CreateWorkspaceCard(QFrame):
    """Card for creating a new workspace."""

    clicked = pyqtSignal()

    def __init__(self, theme="dark"):
        super().__init__()
        self.current_theme = theme
        self.init_ui()
        
    def init_ui(self):
        c = get_colors(self.current_theme)

        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(200)
        self.setMaximumWidth(320)
        self.update_theme()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        icon_label = QLabel("➕")
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("Create New Workspace")
        text_font = QFont()
        text_font.setPointSize(11)
        text_font.setBold(True)
        text_label.setFont(text_font)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("background: transparent;")
        layout.addWidget(text_label)

    def update_theme(self):
        c = get_colors(self.current_theme)
        self.setStyleSheet(f"""
            CreateWorkspaceCard {{
                background-color: {c['bg_primary']};
                border: 2px dashed {c['border']};
                border-radius: {RADIUS_LG};
                padding: 20px;
            }}
            CreateWorkspaceCard:hover {{
                background-color: {c['bg_secondary']};
                border: 2px dashed {c['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class CreateWorkspaceDialog(QDialog):
    """Dialog for creating a new workspace."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workspace_name = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Create New Workspace")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title_label = QLabel("Create New Workspace")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        desc_label = QLabel("Enter a name for your new workspace:")
        layout.addWidget(desc_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Sales Analysis, Customer Data, etc.")
        self.name_input.setMinimumHeight(36)
        layout.addWidget(self.name_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setAutoDefault(False)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Create Workspace")
        create_btn.setProperty("cssClass", "primary")
        create_btn.clicked.connect(self.accept)
        create_btn.setDefault(True)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

        # Enter key in the input creates the workspace
        self.name_input.returnPressed.connect(self.accept)

    def get_workspace_name(self):
        return self.name_input.text().strip()


class RenameWorkspaceDialog(QDialog):
    """Dialog for renaming a workspace."""

    def __init__(self, parent=None, current_name=""):
        super().__init__(parent)
        self.current_name = current_name
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Rename Workspace")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title_label = QLabel("Rename Workspace")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        desc_label = QLabel("Enter a new name for your workspace:")
        layout.addWidget(desc_label)

        self.name_input = QLineEdit()
        self.name_input.setText(self.current_name)
        self.name_input.setPlaceholderText("e.g., Sales Analysis, Customer Data, etc.")
        self.name_input.setMinimumHeight(36)
        self.name_input.selectAll()
        layout.addWidget(self.name_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setAutoDefault(False)
        button_layout.addWidget(cancel_btn)

        rename_btn = QPushButton("Rename")
        rename_btn.setProperty("cssClass", "primary")
        rename_btn.clicked.connect(self.accept)
        rename_btn.setDefault(True)
        button_layout.addWidget(rename_btn)

        layout.addLayout(button_layout)

        self.name_input.returnPressed.connect(self.accept)

    def get_workspace_name(self):
        return self.name_input.text().strip()


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None, current_theme="dark"):
        super().__init__(parent)
        self.current_theme = current_theme
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self.setMinimumHeight(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title_label = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout(appearance_group)

        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.current_theme.capitalize())
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()

        appearance_layout.addLayout(theme_layout)
        layout.addWidget(appearance_group)

        data_group = QGroupBox("Data Settings")
        data_layout = QVBoxLayout(data_group)

        auto_save_layout = QHBoxLayout()
        self.auto_save_check = QCheckBox("Auto-save data on changes")
        self.auto_save_check.setChecked(True)
        auto_save_layout.addWidget(self.auto_save_check)
        data_layout.addLayout(auto_save_layout)

        decimal_layout = QHBoxLayout()
        decimal_label = QLabel("Decimal places:")
        decimal_layout.addWidget(decimal_label)

        self.decimal_spin = QSpinBox()
        self.decimal_spin.setRange(0, 10)
        self.decimal_spin.setValue(2)
        decimal_layout.addWidget(self.decimal_spin)
        decimal_layout.addStretch()

        data_layout.addLayout(decimal_layout)
        layout.addWidget(data_group)

        visualization_group = QGroupBox("Visualization Settings")
        viz_layout = QVBoxLayout(visualization_group)

        dpi_layout = QHBoxLayout()
        dpi_label = QLabel("Export DPI:")
        dpi_layout.addWidget(dpi_label)

        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["150", "300", "600"])
        self.dpi_combo.setCurrentText("300")
        dpi_layout.addWidget(self.dpi_combo)
        dpi_layout.addStretch()

        viz_layout.addLayout(dpi_layout)
        layout.addWidget(visualization_group)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setProperty("cssClass", "primary")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def on_theme_changed(self, theme):
        self.theme_changed.emit(theme.lower())

class HomeScreen(QWidget):
    """Modern home screen with workspace selection."""

    workspace_selected = pyqtSignal(int, str)
    theme_changed = pyqtSignal(str)

    def __init__(self, initial_theme="light"):
        super().__init__()
        self.workspaces_dir = "workspaces"
        self.workspaces = []
        self.current_theme = initial_theme
        self.init_workspace_structure()
        self.init_ui()
        self.load_workspaces()

    def init_workspace_structure(self):
        """Initialize workspace directory structure."""
        if not os.path.exists(self.workspaces_dir):
            os.makedirs(self.workspaces_dir)

        workspace_1_path = os.path.join(self.workspaces_dir, "workspace_1")
        if not os.path.exists(workspace_1_path):
            self.create_workspace_structure(1, "My Workspace")

    def create_workspace_structure(self, workspace_id, name):
        """Create a new workspace structure."""
        workspace_path = os.path.join(self.workspaces_dir, f"workspace_{workspace_id}")

        if not os.path.exists(workspace_path):
            os.makedirs(workspace_path)
            os.makedirs(os.path.join(workspace_path, "data"))
            os.makedirs(os.path.join(workspace_path, "graphs"))
            os.makedirs(os.path.join(workspace_path, "reports"))

            metadata = {
                "id": workspace_id,
                "name": name,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file_count": 0,
                "graph_count": 0,
                "report_count": 0
            }

            with open(os.path.join(workspace_path, "metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=4)

    def _handle_remove_readonly(self, func, path, exc_info):
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(24)

        # Header
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)
        title_label = QLabel("Data Analysis Application")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)

        self.subtitle_label = QLabel("Select a workspace to begin your analysis")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        self.subtitle_label.setFont(subtitle_font)
        title_layout.addWidget(self.subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        header_layout.addWidget(self.settings_btn)

        layout.addLayout(header_layout)

        # Separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFixedHeight(1)
        layout.addWidget(self.separator)

        # Workspaces section header
        workspaces_header_layout = QHBoxLayout()

        workspaces_label = QLabel("Your Workspaces")
        workspaces_font = QFont()
        workspaces_font.setPointSize(13)
        workspaces_font.setBold(True)
        workspaces_label.setFont(workspaces_font)
        workspaces_header_layout.addWidget(workspaces_label)

        workspaces_header_layout.addStretch()

        self.create_workspace_btn = QPushButton("+ New Workspace")
        self.create_workspace_btn.setProperty("cssClass", "primary")
        self.create_workspace_btn.clicked.connect(self.create_new_workspace)
        workspaces_header_layout.addWidget(self.create_workspace_btn)

        layout.addLayout(workspaces_header_layout)

        # Scrollable workspace grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.workspaces_container = QWidget()
        self.workspaces_layout = QGridLayout(self.workspaces_container)
        self.workspaces_layout.setSpacing(20)
        self.workspaces_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll_area.setWidget(self.workspaces_container)
        layout.addWidget(scroll_area)

        self.update_home_theme()

    def update_home_theme(self):
        """Update theme for home screen elements."""
        c = get_colors(self.current_theme)

        self.subtitle_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11pt;")
        self.separator.setStyleSheet(f"background-color: {c['border_subtle']};")

        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_tertiary']};
                border: 1px solid {c['border']};
                border-radius: {RADIUS_MD};
                padding: 10px 20px;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                border-color: {c['accent']};
            }}
        """)

        self.create_workspace_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border: none;
                border-radius: {RADIUS_MD};
                padding: 10px 24px;
                font-size: 10pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
        """)

    def load_workspaces(self):
        """Load and display all workspaces."""
        for i in reversed(range(self.workspaces_layout.count())):
            widget = self.workspaces_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.workspaces = []
        row, col = 0, 0

        if not os.path.exists(self.workspaces_dir):
            return

        workspace_dirs = [d for d in os.listdir(self.workspaces_dir)
                         if os.path.isdir(os.path.join(self.workspaces_dir, d))
                         and d.startswith("workspace_")]

        workspace_ids = []
        for d in workspace_dirs:
            try:
                workspace_id = int(d.split("_")[1])
                workspace_ids.append(workspace_id)
            except (ValueError, IndexError):
                continue

        workspace_ids.sort()

        for workspace_id in workspace_ids:
            workspace_path = os.path.join(self.workspaces_dir, f"workspace_{workspace_id}")
            metadata_path = os.path.join(workspace_path, "metadata.json")

            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

                metadata['file_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "data")) if os.path.isfile(os.path.join(workspace_path, "data", f))])
                metadata['graph_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "graphs")) if f.endswith('.png')])
                metadata['report_count'] = len([f for f in os.listdir(os.path.join(workspace_path, "reports")) if f.endswith(('.html', '.pdf'))])

                self.workspaces.append(metadata)

                card = WorkspaceCard(workspace_id, metadata, self.current_theme)
                card.clicked.connect(self.on_workspace_clicked)
                card.deleted.connect(self.delete_workspace)
                card.renamed.connect(self.rename_workspace)

                self.workspaces_layout.addWidget(card, row, col)

                col += 1
                if col >= 3:
                    col = 0
                    row += 1

        if len(self.workspaces) == 0:
            c = get_colors(self.current_theme)
            empty_label = QLabel("No workspaces yet. Click '+ New Workspace' to get started!")
            empty_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11pt; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.workspaces_layout.addWidget(empty_label, 0, 0, 1, 3)

    def on_workspace_clicked(self, workspace_id):
        """Handle workspace selection."""
        workspace_path = os.path.join(self.workspaces_dir, f"workspace_{workspace_id}")
        metadata_path = os.path.join(workspace_path, "metadata.json")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        metadata['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)

        self.workspace_selected.emit(workspace_id, workspace_path)

    def create_new_workspace(self):
        """Create a new workspace."""
        dialog = CreateWorkspaceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_workspace_name()
            if not name:
                name = f"Workspace {len(self.workspaces) + 1}"

            existing_ids = [w['id'] for w in self.workspaces]
            next_id = 1
            while next_id in existing_ids:
                next_id += 1

            self.create_workspace_structure(next_id, name)
            self.load_workspaces()

            QMessageBox.information(
                self,
                "Workspace Created",
                f"Workspace '{name}' has been created successfully!"
            )

    def rename_workspace(self, workspace_id):
        """Rename a workspace."""
        workspace_path = os.path.join(self.workspaces_dir, f"workspace_{workspace_id}")
        metadata_path = os.path.join(workspace_path, "metadata.json")

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            current_name = metadata.get('name', f'Workspace {workspace_id}')

            dialog = RenameWorkspaceDialog(self, current_name)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_name = dialog.get_workspace_name()
                if new_name and new_name != current_name:
                    metadata['name'] = new_name
                    metadata['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=4)

                    self.load_workspaces()

                    QMessageBox.information(
                        self,
                        "Workspace Renamed",
                        f"Workspace renamed to '{new_name}'."
                    )

    def delete_workspace(self, workspace_id):
        """Delete a workspace."""
        workspace_path = os.path.join(self.workspaces_dir, f"workspace_{workspace_id}")
        metadata_path = os.path.join(workspace_path, "metadata.json")

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            workspace_name = metadata.get('name', f'Workspace {workspace_id}')

            reply = QMessageBox.question(
                self,
                "Delete Workspace",
                f"Are you sure you want to delete '{workspace_name}'?\n\n"
                "This will permanently remove all data, graphs, and reports in this workspace.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                import shutil
                try:
                    shutil.rmtree(workspace_path, onerror=self._handle_remove_readonly)
                    self.load_workspaces()

                    QMessageBox.information(
                        self,
                        "Workspace Deleted",
                        f"Workspace '{workspace_name}' has been deleted."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Delete Failed",
                        f"Failed to delete workspace: {str(e)}"
                    )
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self, self.current_theme)
        dialog.theme_changed.connect(self.on_theme_changed)
        dialog.exec()

    def on_theme_changed(self, theme):
        """Handle theme change."""
        self.current_theme = theme.lower()
        self.theme_changed.emit(theme.lower())
        self.update_home_theme()
        self.update_all_themes()

    def update_all_themes(self):
        """Update theme for all workspace cards."""
        for i in range(self.workspaces_layout.count()):
            widget = self.workspaces_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'update_theme'):
                if hasattr(widget, 'current_theme'):
                    widget.current_theme = self.current_theme
                widget.update_theme()
