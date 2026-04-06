"""
Main window for the DataLens application.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QApplication, QPushButton, QLabel, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont, QCursor
from .components.home_screen import HomeScreen
from .components.workspace_view import WorkspaceView
from .components import modal
from .theme import apply_theme, get_colors
import json
import os
import sys


class _TitleBar(QWidget):
    """Custom title bar that matches the dark theme."""

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self._window = parent_window
        self._drag_pos = None
        self._is_maximized = False
        self.setFixedHeight(40)
        self.setObjectName("customTitleBar")

        c = get_colors("dark")

        self.setStyleSheet(f"""
            QWidget#customTitleBar {{
                background-color: {c['bg_base']};
                border-bottom: 1px solid {c['border']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(8)

        # App icon
        icon_path = parent_window._resource_path('icon.png')
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(QSize(18, 18)))
            icon_label.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(icon_label)

        # Title text
        title_label = QLabel("DataLens")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title_label)

        layout.addStretch()

        # Window control buttons
        btn_style_base = f"""
            QPushButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: none;
                border-radius: 0px;
                font-size: 13px;
                padding: 0px;
                min-height: 0px;
                min-width: 46px;
                max-width: 46px;
                max-height: 40px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.1);
                color: {c['text_primary']};
            }}
        """
        close_btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: none;
                border-radius: 0px;
                font-size: 13px;
                padding: 0px;
                min-height: 0px;
                min-width: 46px;
                max-width: 46px;
                max-height: 40px;
            }}
            QPushButton:hover {{
                background-color: #ef4444;
                color: #ffffff;
            }}
        """

        self.min_btn = QPushButton("─")
        self.min_btn.setStyleSheet(btn_style_base)
        self.min_btn.setFixedSize(46, 40)
        self.min_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.min_btn.clicked.connect(self._window.showMinimized)
        layout.addWidget(self.min_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setStyleSheet(btn_style_base)
        self.max_btn.setFixedSize(46, 40)
        self.max_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet(close_btn_style)
        self.close_btn.setFixedSize(46, 40)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.clicked.connect(self._window.close)
        layout.addWidget(self.close_btn)

    def _toggle_maximize(self):
        if self._window.isMaximized():
            self._window.showNormal()
            self.max_btn.setText("□")
        else:
            self._window.showMaximized()
            self.max_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self._window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            if self._window.isMaximized():
                # Un-maximize and reposition so the cursor stays proportional
                old_width = self._window.width()
                self._window.showNormal()
                new_width = self._window.width()
                ratio = event.globalPos().x() / old_width
                self._drag_pos = QPoint(int(new_width * ratio), event.pos().y())
                self.max_btn.setText("□")
            self._window.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()


class MainWindow(QMainWindow):
    """Main window of the application."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.current_theme = "dark"
        self.setWindowFlags(Qt.FramelessWindowHint)
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
        self.setWindowTitle("DataLens")
        self.setMinimumSize(1200, 800)

        icon_path = self._resource_path('icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom title bar
        self.title_bar = _TitleBar(self)
        layout.addWidget(self.title_bar)

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
        # Update title bar colors
        c = get_colors(theme)
        self.title_bar.setStyleSheet(f"""
            QWidget#customTitleBar {{
                background-color: {c['bg_base']};
                border-bottom: 1px solid {c['border']};
            }}
        """)

    def show_error(self, message):
        """Show error message dialog."""
        modal.show_error(self, "Error", message)

    def closeEvent(self, event):
        """Handle window close event with unsaved changes check."""
        if self.stacked_widget.currentWidget() == self.workspace_view:
            if self.workspace_view.has_unsaved_changes:
                result = modal.show_question_3way(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save before exiting?"
                )

                if result == "cancel":
                    event.ignore()
                    return
                elif result == "yes":
                    self.workspace_view.save_workspace()

        event.accept()
