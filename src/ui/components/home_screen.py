"""
Modern home screen for workspace selection.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QDialog, QLineEdit, QGroupBox,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ..theme import get_colors, current_theme, RADIUS_LG, RADIUS_MD, RADIUS_SM
from . import modal
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
        self.setMinimumHeight(140)
        self.setMaximumHeight(160)
        self.setMaximumWidth(320)
        self.update_theme()

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 12, 14, 12)

        # Top row: icon + action buttons
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(icon_label)

        top_layout.addStretch()

        rename_btn = QPushButton("✏️")
        rename_btn.setFixedSize(22, 22)
        rename_btn.setToolTip("Rename workspace")
        rename_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                border: none;
                border-radius: 11px;
                font-size: 11px;
                padding: 0px;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
        """)
        rename_btn.clicked.connect(lambda: self.renamed.emit(self.workspace_id))
        top_layout.addWidget(rename_btn)

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(22, 22)
        delete_btn.setToolTip("Delete workspace")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['danger']};
                border: none;
                border-radius: 11px;
                font-size: 11px;
                padding: 0px;
                min-height: 0px;
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
        name_font.setPointSize(10)
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
        stats_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px; background: transparent;")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stats_label)

        if self.workspace_data.get('last_modified'):
            date_label = QLabel(f"Modified: {self.workspace_data['last_modified']}")
            date_label.setStyleSheet(f"color: {c['text_disabled']}; font-size: 11px; background: transparent;")
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(date_label)

        layout.addStretch()

    def update_theme(self):
        c = get_colors(self.current_theme)
        self.setStyleSheet(f"""
            WorkspaceCard {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: {RADIUS_LG};
                padding: 14px;
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
        self.setMinimumHeight(140)
        self.setMaximumHeight(160)
        self.setMaximumWidth(320)
        self.update_theme()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(14, 12, 14, 12)

        icon_label = QLabel("➕")
        icon_label.setStyleSheet("font-size: 36px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("Create New Workspace")
        text_font = QFont()
        text_font.setPointSize(10)
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
                border: 2px dashed {c['border_medium']};
                border-radius: {RADIUS_LG};
                padding: 14px;
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

class NewProjectCard(QFrame):
    """Ghost placeholder tile that triggers new workspace creation."""

    clicked = pyqtSignal()

    def __init__(self, theme="dark"):
        super().__init__()
        self.current_theme = theme
        self._hovered = False
        self.init_ui()

    def init_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(140)
        self.setMaximumHeight(160)
        self.setMaximumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # "+" box
        self.plus_box = QLabel("+")
        self.plus_box.setFixedSize(36, 36)
        self.plus_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus_row = QHBoxLayout()
        plus_row.setContentsMargins(0, 0, 0, 0)
        plus_row.addStretch()
        plus_row.addWidget(self.plus_box)
        plus_row.addStretch()
        layout.addLayout(plus_row)

        # Label
        self.caption = QLabel("New Project")
        self.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.caption)

        layout.addStretch()

        self._apply_styles()

    def _apply_styles(self):
        dark = self.current_theme == "dark"

        if self._hovered:
            border_color = "#6366f1"
            plus_border = "#6366f1"
            plus_color = "#6366f1"
            text_color = "#6366f1"
        else:
            border_color = "rgba(255,255,255,0.2)" if dark else "rgba(0,0,0,0.15)"
            plus_border = "rgba(255,255,255,0.25)" if dark else "rgba(0,0,0,0.2)"
            plus_color = "rgba(255,255,255,0.4)" if dark else "rgba(0,0,0,0.3)"
            text_color = "rgba(255,255,255,0.4)" if dark else "rgba(0,0,0,0.35)"

        self.setStyleSheet(f"""
            NewProjectCard {{
                background-color: transparent;
                border: 2px dashed {border_color};
                border-radius: 10px;
            }}
        """)

        self.plus_box.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border: 2px solid {plus_border};
                border-radius: 8px;
                color: {plus_color};
                font-size: 22px;
                font-weight: 500;
            }}
        """)

        self.caption.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border: none;
                color: {text_color};
                font-size: 12px;
                font-weight: 500;
            }}
        """)

    def update_theme(self):
        self._apply_styles()

    def enterEvent(self, event):
        self._hovered = True
        self._apply_styles()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_styles()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CreateWorkspaceDialog(QDialog):
    """Dialog for creating a new workspace."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.workspace_name = ""
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        theme = current_theme()
        c = get_colors(theme)
        is_dark = theme == "dark"
        input_border = "rgba(255,255,255,0.12)" if is_dark else "rgba(0,0,0,0.14)"

        # Overlay
        self._overlay = QWidget(self)
        self._overlay.setStyleSheet("background: rgba(0, 0, 0, 0.6);")

        # Box
        self._box = QWidget(self._overlay)
        self._box.setStyleSheet(f"""
            QWidget {{
                background-color: {c['bg_primary']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
        """)
        box_layout = QVBoxLayout(self._box)
        box_layout.setContentsMargins(24, 24, 24, 24)
        box_layout.setSpacing(16)

        title_label = QLabel("Create New Workspace")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_primary']};
                font-size: 15px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        box_layout.addWidget(title_label)

        desc_label = QLabel("Enter a name for your new workspace:")
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_secondary']};
                font-size: 13px;
                background: transparent;
                border: none;
            }}
        """)
        box_layout.addWidget(desc_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Sales Analysis, Customer Data, etc.")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {c['accent']};
            }}
        """)
        box_layout.addWidget(self.name_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Create Workspace")
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
        """)
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)

        box_layout.addLayout(btn_layout)

        self.name_input.returnPressed.connect(self.accept)

    def _layout_children(self):
        if self.parent():
            self.resize(self.parent().size())
            self.move(self.parent().mapToGlobal(self.parent().rect().topLeft()))
        self._overlay.setGeometry(0, 0, self.width(), self.height())
        box_w = min(440, self.width() - 60)
        self._box.setFixedWidth(box_w)
        self._box.adjustSize()
        bx = (self.width() - box_w) // 2
        by = (self.height() - self._box.height()) // 2
        self._box.move(bx, by)

    def showEvent(self, event):
        super().showEvent(event)
        self._layout_children()
        self.name_input.setFocus()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_children()

    def get_workspace_name(self):
        return self.name_input.text().strip()


class RenameWorkspaceDialog(QDialog):
    """Dialog for renaming a workspace."""

    def __init__(self, parent=None, current_name=""):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.current_name = current_name
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        c = get_colors("dark")

        self._overlay = QWidget(self)
        self._overlay.setStyleSheet("background: rgba(0, 0, 0, 0.6);")

        self._box = QWidget(self._overlay)
        self._box.setStyleSheet(f"""
            QWidget {{
                background-color: #1e2433;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 10px;
            }}
        """)
        box_layout = QVBoxLayout(self._box)
        box_layout.setContentsMargins(24, 24, 24, 24)
        box_layout.setSpacing(16)

        title_label = QLabel("Rename Workspace")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_primary']};
                font-size: 15px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        box_layout.addWidget(title_label)

        desc_label = QLabel("Enter a new name for your workspace:")
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: #9ca3af;
                font-size: 13px;
                background: transparent;
                border: none;
            }}
        """)
        box_layout.addWidget(desc_label)

        self.name_input = QLineEdit()
        self.name_input.setText(self.current_name)
        self.name_input.setPlaceholderText("e.g., Sales Analysis, Customer Data, etc.")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {c['accent']};
            }}
        """)
        box_layout.addWidget(self.name_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        rename_btn = QPushButton("Rename")
        rename_btn.setCursor(Qt.PointingHandCursor)
        rename_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
        """)
        rename_btn.clicked.connect(self.accept)
        btn_layout.addWidget(rename_btn)

        box_layout.addLayout(btn_layout)

        self.name_input.returnPressed.connect(self.accept)

    def _layout_children(self):
        if self.parent():
            self.resize(self.parent().size())
            self.move(self.parent().mapToGlobal(self.parent().rect().topLeft()))
        self._overlay.setGeometry(0, 0, self.width(), self.height())
        box_w = min(440, self.width() - 60)
        self._box.setFixedWidth(box_w)
        self._box.adjustSize()
        bx = (self.width() - box_w) // 2
        by = (self.height() - self._box.height()) // 2
        self._box.move(bx, by)

    def showEvent(self, event):
        super().showEvent(event)
        self._layout_children()
        self.name_input.setFocus()
        self.name_input.selectAll()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_children()

    def get_workspace_name(self):
        return self.name_input.text().strip()


class ThemeToggle(QWidget):
    """Compact segmented Dark/Light theme toggle for the home screen."""

    theme_changed = pyqtSignal(str)

    def __init__(self, current_theme="dark", parent=None):
        super().__init__(parent)
        self.current_theme = current_theme

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.dark_btn = QPushButton("🌙 Dark")
        self.light_btn = QPushButton("☀ Light")
        for btn in (self.dark_btn, self.light_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setMinimumWidth(92)

        self.dark_btn.clicked.connect(lambda: self._select("dark"))
        self.light_btn.clicked.connect(lambda: self._select("light"))

        layout.addWidget(self.dark_btn)
        layout.addWidget(self.light_btn)

        self.setFixedWidth(192)
        self._refresh_styles()

    def _select(self, theme):
        if theme == self.current_theme:
            return
        self.current_theme = theme
        self._refresh_styles()
        self.theme_changed.emit(theme)

    def set_theme(self, theme):
        """Update the active theme without emitting a change signal."""
        self.current_theme = theme
        self._refresh_styles()

    def _chip_style(self, selected):
        c = get_colors(self.current_theme)
        if selected:
            return f"""
                QPushButton {{
                    background-color: {c['accent']};
                    color: {c['text_inverse']};
                    border: 1px solid {c['accent']};
                    border-radius: 18px;
                    padding: 6px 16px;
                    font-size: 14px;
                    font-weight: 600;
                    min-height: 36px;
                    max-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {c['accent_hover']};
                }}
            """
        return f"""
            QPushButton {{
                background-color: {c['bg_tertiary']};
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 18px;
                padding: 6px 16px;
                font-size: 14px;
                font-weight: 600;
                min-height: 36px;
                max-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
                border-color: {c['accent']};
            }}
        """

    def _refresh_styles(self):
        self.dark_btn.setStyleSheet(self._chip_style(self.current_theme == "dark"))
        self.light_btn.setStyleSheet(self._chip_style(self.current_theme == "light"))


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
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Content area with padding
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(48, 20, 48, 0)
        layout.setSpacing(24)

        # Header
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        # Title row: logo + "DataLens" inline
        title_row_widget = QWidget()
        title_row_widget.setMinimumHeight(80)
        title_row = QHBoxLayout(title_row_widget)
        title_row.setSpacing(0)
        title_row.setContentsMargins(0, 0, 0, 0)

        # Logo inline with title
        import sys
        try:
            logo_base = sys._MEIPASS
        except Exception:
            logo_base = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))
        logo_path = os.path.join(logo_base, 'assets', 'DataLens_Logo_cropped.png')
        if os.path.exists(logo_path):
            from PyQt5.QtGui import QPixmap
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaledToHeight(64, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)
            logo_label.setStyleSheet("background: transparent; border: none; margin-right: 8px;")
            title_row.addWidget(logo_label)

        self.title_label = QLabel("DataLens")
        _title_color = "#ffffff" if self.current_theme == "dark" else "#0f172a"
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {_title_color};
                font-size: 28pt;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: transparent;
                border: none;
            }}
        """)
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        title_layout.addWidget(title_row_widget)

        self.subtitle_label = QLabel("Your data. Clearer than ever.")
        sub_color = "#94a3b8" if self.current_theme == "dark" else "#475569"
        self.subtitle_label.setStyleSheet(f"color: {sub_color}; font-size: 13pt; font-weight: 400; background: transparent;")
        title_layout.addWidget(self.subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.theme_toggle = ThemeToggle(self.current_theme)
        self.theme_toggle.theme_changed.connect(self.on_theme_changed)
        header_layout.addWidget(self.theme_toggle, 0, Qt.AlignVCenter)

        layout.addLayout(header_layout)

        # Separator
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFixedHeight(1)
        layout.addWidget(self.separator)

        # Scrollable workspace grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.workspaces_container = QWidget()
        self.workspaces_layout = QGridLayout(self.workspaces_container)
        self.workspaces_layout.setSpacing(20)
        self.workspaces_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll_area.setWidget(self.workspaces_container)
        layout.addWidget(scroll_area)

        outer_layout.addWidget(content_widget, 1)

        # ── Footer ──
        c = get_colors(self.current_theme)
        self.footer_frame = QFrame()
        self.footer_frame.setFixedHeight(36)
        self.footer_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.footer_frame.setContentsMargins(0, 0, 0, 0)
        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(16, 0, 16, 0)
        footer_layout.setSpacing(0)

        left_label = QLabel("DataLens")
        left_label.setStyleSheet(f"color: #6b7280; font-size: 11px; background: transparent;")
        footer_layout.addWidget(left_label)

        footer_layout.addStretch()

        center_label = QLabel("\u00a9 2026 DataLens. All rights reserved.")
        center_label.setStyleSheet(f"color: #6b7280; font-size: 11px; background: transparent;")
        center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(center_label)

        footer_layout.addStretch()

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(f"color: #6b7280; font-size: 11px; background: transparent;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer_layout.addWidget(version_label)

        outer_layout.addWidget(self.footer_frame)

        self.update_home_theme()

    def update_home_theme(self):
        """Update theme for home screen elements."""
        c = get_colors(self.current_theme)

        # Title text color follows theme
        title_color = "#ffffff" if self.current_theme == "dark" else "#0f172a"
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {title_color};
                font-size: 28pt;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: transparent;
                border: none;
            }}
        """)
        sub_color = "#94a3b8" if self.current_theme == "dark" else "#475569"
        self.subtitle_label.setStyleSheet(f"color: {sub_color}; font-size: 13pt; font-weight: 400; background: transparent;")
        self.separator.setStyleSheet(f"background-color: {c['border']};")

        self.footer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_secondary']};
                border-top: 1px solid {c['border']};
            }}
        """)

        # Theme toggle restyles itself for the active theme
        self.theme_toggle.set_theme(self.current_theme)

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

        # Ghost "New Project" tile always appears as the last item
        ghost_tile = NewProjectCard(self.current_theme)
        ghost_tile.clicked.connect(self.create_new_workspace)
        self.workspaces_layout.addWidget(ghost_tile, row, col)

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

            modal.show_success(
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

                    modal.show_success(
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

            confirmed = modal.show_question(
                self,
                "Delete Workspace",
                f"Are you sure you want to delete '{workspace_name}'?\n\n"
                "This will permanently remove all data, graphs, and reports in this workspace."
            )

            if confirmed:
                import shutil
                try:
                    shutil.rmtree(workspace_path, onerror=self._handle_remove_readonly)
                    self.load_workspaces()

                    modal.show_success(
                        self,
                        "Workspace Deleted",
                        f"Workspace '{workspace_name}' has been deleted."
                    )
                except Exception as e:
                    modal.show_error(
                        self,
                        "Delete Failed",
                        f"Failed to delete workspace: {str(e)}"
                    )

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
