"""
Main window for the Data Analysis Application.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon
from .components.home_screen import HomeScreen
from .components.workspace_view import WorkspaceView
from .theme import apply_theme, get_colors
import json
import os
import sys

class MainWindow(QMainWindow):
    """Main window of the application."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.current_theme = "dark"
        self.init_ui()
        self.setup_connections()

    def _resource_path(self, relative_path):
        """
        Get absolute path to resource, works for dev and PyInstaller.
        """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        return os.path.join(base_path, relative_path)

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Data Analysis Application")
        self.setMinimumSize(1200, 800)

        icon_path = self._resource_path('icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()

        self.current_theme = "dark"

        self.home_screen = HomeScreen(initial_theme="dark")
        self.stacked_widget.addWidget(self.home_screen)

        self.workspace_view = WorkspaceView()
        self.stacked_widget.addWidget(self.workspace_view)

        layout.addWidget(self.stacked_widget)

        # Apply the centralized theme
        apply_theme("dark")
        self.workspace_view.update_theme("dark")

    def setup_connections(self):
        """Setup signal connections."""
        self.home_screen.workspace_selected.connect(self.open_workspace)
        self.home_screen.theme_changed.connect(self.change_theme)
        self.workspace_view.back_to_home.connect(self.show_home_screen)

    def open_workspace(self, workspace_id, workspace_path):
        """Open a workspace."""
        metadata_path = os.path.join(workspace_path, "metadata.json")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        workspace_name = metadata.get('name', f'Workspace {workspace_id}')

        self.workspace_view.set_workspace(workspace_id, workspace_path, workspace_name)
        self.stacked_widget.setCurrentWidget(self.workspace_view)

    def show_home_screen(self):
        """Return to home screen."""
        self.home_screen.load_workspaces()
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def change_theme(self, theme):
        """Change application theme."""
        self.current_theme = theme
        apply_theme(theme)
        self.workspace_view.update_theme(theme)

    def show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """Handle window close event with unsaved changes check."""
        if self.stacked_widget.currentWidget() == self.workspace_view:
            if self.workspace_view.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save before exiting?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    self.workspace_view.save_workspace()

        event.accept() 