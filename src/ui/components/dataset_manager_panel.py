"""
Dataset manager dialog for managing datasets within a workspace.
Two-tier model: originals (left column) and working copies (right column).
Files live in data/originals/ and data/copies/ respectively.
"""

import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QScrollArea,
    QInputDialog, QLabel, QMenu, QWidget, QSizePolicy,
    QGraphicsDropShadowEffect
)
from . import modal
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, QEvent
from PyQt5.QtGui import QFont, QColor, QCursor


# ── Helpers ────────────────────────────────────────────────────────────────

def _format_size(size):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def _accent():
    return "#6366f1"


def _accent_hover():
    return "#7577f5"


# ── Original Card (left column) ───────────────────────────────────────────

class OriginalCard(QWidget):
    """Card widget for an imported original dataset."""

    new_copy_clicked = pyqtSignal(str)   # original filename
    menu_requested = pyqtSignal(str)     # original filename

    def __init__(self, filename, file_path, imported_at=None, missing=False):
        super().__init__()
        self.filename = filename
        self.file_path = file_path
        self.missing = missing
        self.setCursor(QCursor(Qt.PointingHandCursor))

        border_color = "rgba(245,158,11,0.5)" if missing else "rgba(255,255,255,0.08)"
        self.setStyleSheet(f"""
            OriginalCard {{
                background: #1e2433;
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
            OriginalCard:hover {{
                border-color: rgba(255,255,255,0.18);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 6, 10)
        layout.setSpacing(6)

        # Warning icon for missing files
        if missing:
            warn = QLabel("\u26a0")
            warn.setToolTip("File not found on disk")
            warn.setStyleSheet("color: #f59e0b; font-size: 14px; background: transparent; border: none;")
            warn.setFixedWidth(18)
            layout.addWidget(warn, 0, Qt.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        name_color = "#8b8fa3" if missing else "#e2e4ed"
        name_without_ext = os.path.splitext(filename)[0]
        name_label = QLabel(name_without_ext)
        name_label.setStyleSheet(f"color: {name_color}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        name_label.setToolTip(filename if not missing else f"{filename} (missing)")
        name_label.setWordWrap(False)
        info.addWidget(name_label)

        details_parts = []
        if not missing and os.path.exists(file_path):
            details_parts.append(_format_size(os.path.getsize(file_path)))
        if imported_at:
            details_parts.append(imported_at)
        elif not missing and os.path.exists(file_path):
            mod = datetime.fromtimestamp(os.path.getmtime(file_path))
            details_parts.append(mod.strftime("%Y-%m-%d %H:%M"))
        if missing:
            details_parts.append("File missing")

        details_label = QLabel("  \u00b7  ".join(details_parts))
        details_label.setStyleSheet("color: #8b8fa3; font-size: 9px; background: transparent; border: none;")
        info.addWidget(details_label)

        layout.addLayout(info, 1)

        # + New Copy button
        self.new_copy_btn = QPushButton("+")
        self.new_copy_btn.setFixedSize(28, 28)
        self.new_copy_btn.setToolTip("New Copy")
        self.new_copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.new_copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #8b8fa3;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                padding: 0px;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background: {_accent()};
                color: #ffffff;
                border-color: {_accent()};
            }}
        """)
        if missing:
            self.new_copy_btn.setEnabled(False)
            self.new_copy_btn.setToolTip("Cannot copy — original missing")
        self.new_copy_btn.clicked.connect(lambda: self.new_copy_clicked.emit(self.filename))
        layout.addWidget(self.new_copy_btn, 0, Qt.AlignVCenter)

        # Context menu button
        self.ctx_btn = QPushButton("\u22ee")
        self.ctx_btn.setFixedSize(28, 28)
        self.ctx_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ctx_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8b8fa3;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                padding: 0px;
                min-height: 0px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.06);
                color: #e2e4ed;
            }
        """)
        self.ctx_btn.clicked.connect(lambda: self.menu_requested.emit(self.filename))
        layout.addWidget(self.ctx_btn, 0, Qt.AlignVCenter)


# ── Working Copy Card (right column) ──────────────────────────────────────

class CopyCard(QWidget):
    """Card widget for a working copy dataset."""

    load_clicked = pyqtSignal(str)    # copy relative path
    rename_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, copy_rel_path, file_path, is_active=False, missing=False):
        super().__init__()
        self.copy_rel_path = copy_rel_path
        self.file_path = file_path
        self.is_active = is_active
        self.missing = missing
        self.display_name = os.path.basename(copy_rel_path)

        bg = "#232a3a" if is_active else "#1e2433"
        left_border = f"border-left: 3px solid {_accent()};" if is_active else ""
        border_color = "rgba(245,158,11,0.5)" if missing else "rgba(255,255,255,0.08)"

        self.setStyleSheet(f"""
            CopyCard {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                {left_border}
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 6, 10)
        layout.setSpacing(6)

        if missing:
            warn = QLabel("\u26a0")
            warn.setToolTip("File not found on disk")
            warn.setStyleSheet("color: #f59e0b; font-size: 14px; background: transparent; border: none;")
            warn.setFixedWidth(18)
            layout.addWidget(warn, 0, Qt.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        # Top row: name + ACTIVE badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.setContentsMargins(0, 0, 0, 0)

        name_color = "#8b8fa3" if missing else "#e2e4ed"
        name_without_ext = os.path.splitext(self.display_name)[0]
        name_label = QLabel(name_without_ext)
        name_label.setStyleSheet(f"color: {name_color}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        name_label.setToolTip(self.display_name if not missing else f"{self.display_name} (missing)")
        name_label.setWordWrap(False)
        top_row.addWidget(name_label, 1)

        if is_active:
            badge = QLabel("ACTIVE")
            badge.setStyleSheet(f"""
                QLabel {{
                    color: {_accent()};
                    font-size: 9px;
                    font-weight: 700;
                    letter-spacing: 1px;
                    background: transparent;
                    border: none;
                    padding: 0px 2px;
                }}
            """)
            top_row.addWidget(badge, 0, Qt.AlignRight | Qt.AlignVCenter)

        info.addLayout(top_row)

        # Details line
        details_parts = []
        if not missing and os.path.exists(file_path):
            details_parts.append(_format_size(os.path.getsize(file_path)))
            mod = datetime.fromtimestamp(os.path.getmtime(file_path))
            details_parts.append(mod.strftime("%Y-%m-%d %H:%M"))
        if missing:
            details_parts.append("File missing")
        details_label = QLabel("  \u00b7  ".join(details_parts))
        details_label.setStyleSheet("color: #8b8fa3; font-size: 9px; background: transparent; border: none;")
        info.addWidget(details_label)

        layout.addLayout(info, 1)

        # Load button
        self.load_btn = QPushButton("Load")
        self.load_btn.setFixedHeight(28)
        self.load_btn.setCursor(QCursor(Qt.PointingHandCursor))
        if is_active or missing:
            self.load_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #4b5063;
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 6px;
                    padding: 4px 14px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 0px;
                }
            """)
            self.load_btn.setEnabled(False)
        else:
            self.load_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {_accent()};
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 4px 14px;
                    font-size: 11px;
                    font-weight: 600;
                    min-height: 0px;
                }}
                QPushButton:hover {{
                    background: {_accent_hover()};
                }}
            """)
        self.load_btn.clicked.connect(lambda: self.load_clicked.emit(self.copy_rel_path))
        layout.addWidget(self.load_btn, 0, Qt.AlignVCenter)

        # Context menu button
        self.menu_btn = QPushButton("\u22ee")
        self.menu_btn.setFixedSize(28, 28)
        self.menu_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8b8fa3;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                padding: 0px;
                min-height: 0px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.06);
                color: #e2e4ed;
            }
        """)
        self.menu_btn.clicked.connect(self._show_menu)
        layout.addWidget(self.menu_btn, 0, Qt.AlignVCenter)

    def _show_menu(self):
        menu = QMenu(self)
        load_action = menu.addAction("Load")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete Copy")

        if self.is_active or self.missing:
            load_action.setEnabled(False)
        if self.is_active:
            rename_action.setEnabled(False)

        action = menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        if action == load_action:
            self.load_clicked.emit(self.copy_rel_path)
        elif action == rename_action:
            self.rename_clicked.emit(self.copy_rel_path)
        elif action == delete_action:
            self.delete_clicked.emit(self.copy_rel_path)


# ── Custom Title Bar ──────────────────────────────────────────────────────

class _TitleBar(QWidget):
    """Custom draggable title bar for the frameless dialog."""

    close_clicked = pyqtSignal()
    scan_clicked = pyqtSignal()

    def __init__(self, parent_dialog):
        super().__init__()
        self._dialog = parent_dialog
        self._drag_pos = None
        self.setFixedHeight(36)
        self.setStyleSheet("background: #0f1117; border: none; border-top-left-radius: 10px; border-top-right-radius: 10px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(8)

        icon_label = QLabel("\u26c1")
        icon_label.setStyleSheet("color: #6366f1; font-size: 14px; background: transparent; border: none;")
        layout.addWidget(icon_label)

        title = QLabel("Dataset Manager")
        title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(title)

        layout.addStretch()

        # Scan / refresh button
        scan_btn = QPushButton("\u21bb")
        scan_btn.setFixedSize(28, 28)
        scan_btn.setCursor(QCursor(Qt.PointingHandCursor))
        scan_btn.setToolTip("Scan files — re-validate disk state")
        scan_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8b8fa3;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                padding: 0px;
                min-height: 0px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                color: #e2e4ed;
            }
        """)
        scan_btn.clicked.connect(self.scan_clicked.emit)
        layout.addWidget(scan_btn)

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8b8fa3;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0px;
                min-height: 0px;
            }
            QPushButton:hover {
                background: #ef4444;
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self._dialog.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self._dialog.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ── Main Dialog ───────────────────────────────────────────────────────────

class DatasetManagerDialog(QDialog):
    """Two-column dataset manager with originals and working copies."""

    dataset_selected = pyqtSignal(str)   # full file path
    dataset_deleted = pyqtSignal(str)    # relative path
    dataset_renamed = pyqtSignal(str, str)
    workspace_reset = pyqtSignal()       # emitted after full reset

    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.workspace_path = None
        self.workspace_name = ""
        self.current_dataset = None
        self.data_manager = None
        self._selected_original = None
        self.setFixedSize(760, 520)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            DatasetManagerDialog {
                background: #13161e;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        self.title_bar = _TitleBar(self)
        self.title_bar.close_clicked.connect(self.accept)
        self.title_bar.scan_clicked.connect(self.refresh)
        root.addWidget(self.title_bar)

        # Body
        body = QHBoxLayout()
        body.setContentsMargins(16, 8, 16, 12)
        body.setSpacing(14)

        # ── LEFT COLUMN (originals) ───────────────────────────────────
        left_col = QVBoxLayout()
        left_col.setSpacing(8)

        left_header = QLabel("IMPORTED DATASETS")
        left_header.setStyleSheet(f"color: {_accent()}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; background: transparent;")
        left_col.addWidget(left_header)

        # Scroll area for original cards
        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.left_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.left_scroll.setFixedWidth(260)

        self.left_container = QWidget()
        self.left_container.setStyleSheet("background: transparent;")
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(0, 0, 4, 0)
        self.left_layout.setSpacing(6)
        self.left_layout.addStretch()

        self.left_scroll.setWidget(self.left_container)
        left_col.addWidget(self.left_scroll, 1)

        # Empty state (shown when no originals)
        self.left_empty = QWidget()
        self.left_empty.setStyleSheet("background: transparent;")
        empty_l = QVBoxLayout(self.left_empty)
        empty_l.setAlignment(Qt.AlignCenter)
        empty_icon = QLabel("\U0001F4C2")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        empty_l.addWidget(empty_icon)
        empty_text = QLabel("No datasets imported yet")
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setStyleSheet("color: #4b5063; font-size: 11px; background: transparent; border: none;")
        empty_l.addWidget(empty_text)
        self.left_empty_btn = QPushButton("+ Import Dataset")
        self.left_empty_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.left_empty_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_accent()};
                border: 1px solid {_accent()};
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 11px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background: rgba(99,102,241,0.12);
            }}
        """)
        self.left_empty_btn.clicked.connect(self.import_dataset)
        empty_l.addWidget(self.left_empty_btn, 0, Qt.AlignCenter)
        self.left_empty.setFixedWidth(260)
        left_col.addWidget(self.left_empty)
        self.left_empty.hide()

        # Import button at bottom of left column
        self.import_btn = QPushButton("+ Import Dataset")
        self.import_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.import_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_accent()};
                border: 1px dashed {_accent()};
                border-radius: 6px;
                padding: 9px 0px;
                font-size: 11px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background: rgba(99,102,241,0.10);
            }}
        """)
        self.import_btn.clicked.connect(self.import_dataset)
        left_col.addWidget(self.import_btn)

        body.addLayout(left_col)

        # Vertical separator
        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.08);")
        body.addWidget(sep)

        # ── RIGHT COLUMN (working copies) ─────────────────────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        right_header = QLabel("WORKING COPIES")
        right_header.setStyleSheet(f"color: {_accent()}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; background: transparent;")
        right_col.addWidget(right_header)

        self.right_sub_header = QLabel("")
        self.right_sub_header.setStyleSheet("color: #8b8fa3; font-size: 10px; background: transparent;")
        right_col.addWidget(self.right_sub_header)

        # Pipeline guidance banner
        self.guidance_banner = QWidget()
        self.guidance_banner.setStyleSheet("""
            QWidget {
                background: rgba(99,102,241,0.08);
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 6px;
            }
        """)
        banner_layout = QHBoxLayout(self.guidance_banner)
        banner_layout.setContentsMargins(12, 8, 12, 8)
        banner_layout.setSpacing(10)
        banner_text = QLabel("\U0001F4CB Ready to work? Create a working copy to keep your original data safe.")
        banner_text.setWordWrap(True)
        banner_text.setStyleSheet("color: #a5b4fc; font-size: 11px; background: transparent; border: none;")
        banner_layout.addWidget(banner_text, 1)
        self.banner_create_btn = QPushButton("+ Create Working Copy")
        self.banner_create_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.banner_create_btn.setFixedHeight(28)
        self.banner_create_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_accent()};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background: {_accent_hover()};
            }}
        """)
        self.banner_create_btn.clicked.connect(self._on_banner_create)
        banner_layout.addWidget(self.banner_create_btn, 0, Qt.AlignVCenter)
        right_col.addWidget(self.guidance_banner)
        self.guidance_banner.hide()

        # Scroll area for copy cards
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.right_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.right_container = QWidget()
        self.right_container.setStyleSheet("background: transparent;")
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 4, 0)
        self.right_layout.setSpacing(6)
        self.right_layout.addStretch()

        self.right_scroll.setWidget(self.right_container)
        right_col.addWidget(self.right_scroll, 1)

        # Empty state for right column
        self.right_empty = QWidget()
        self.right_empty.setStyleSheet("background: transparent;")
        rempty = QVBoxLayout(self.right_empty)
        rempty.setAlignment(Qt.AlignCenter)
        rempty_text = QLabel("No working copies yet.\nClick + New Copy to create one.")
        rempty_text.setAlignment(Qt.AlignCenter)
        rempty_text.setStyleSheet("color: #4b5063; font-size: 11px; background: transparent; border: none;")
        rempty.addWidget(rempty_text)
        self.right_empty_btn = QPushButton("+ Create Working Copy")
        self.right_empty_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.right_empty_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_accent()};
                border: 1px solid {_accent()};
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 11px;
                font-weight: 600;
                min-height: 0px;
            }}
            QPushButton:hover {{
                background: rgba(99,102,241,0.12);
            }}
        """)
        self.right_empty_btn.clicked.connect(self._on_empty_create)
        rempty.addWidget(self.right_empty_btn, 0, Qt.AlignCenter)
        right_col.addWidget(self.right_empty)
        self.right_empty.hide()

        # "Load Original Directly" button at bottom of right column
        self.load_original_btn = QPushButton("Load Original Directly \u2192")
        self.load_original_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.load_original_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8b8fa3;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 7px 0px;
                font-size: 11px;
                font-weight: 500;
                min-height: 0px;
            }
            QPushButton:hover {
                color: #e2e4ed;
                border-color: rgba(255,255,255,0.2);
                background: rgba(255,255,255,0.03);
            }
        """)
        self.load_original_btn.clicked.connect(self._on_load_original)
        right_col.addWidget(self.load_original_btn)
        self.load_original_btn.hide()

        body.addLayout(right_col, 1)
        root.addLayout(body, 1)

        # ── BOTTOM BAR ────────────────────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setContentsMargins(16, 4, 16, 12)

        # Reset Workspace (left, de-emphasized, red-tinted)
        self.reset_btn = QPushButton("Reset Workspace")
        self.reset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 10px;
                font-weight: 600;
                min-height: 0px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.08);
            }
        """)
        self.reset_btn.clicked.connect(self._on_reset_workspace)
        bottom.addWidget(self.reset_btn)

        bottom.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e2e4ed;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 6px;
                padding: 7px 24px;
                font-size: 11px;
                font-weight: 600;
                min-height: 0px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.06);
            }
        """)
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        root.addLayout(bottom)

    # ── Public API ─────────────────────────────────────────────────────────

    def set_workspace(self, workspace_path, workspace_name=""):
        """Configure workspace path and refresh."""
        self.workspace_path = workspace_path
        self.workspace_name = workspace_name
        self.refresh()

    def set_data_manager(self, dm):
        """Provide a reference to the DataManager for two-tier operations."""
        self.data_manager = dm
        self.current_dataset = dm.active_working_copy
        self.refresh()

    def set_current_dataset(self, relative_path):
        """Update which dataset is active and refresh the view."""
        self.current_dataset = relative_path
        self.refresh()

    # ── Refresh ────────────────────────────────────────────────────────────

    def refresh(self):
        """Rebuild both columns from data_manager state."""
        self._refresh_left()
        self._refresh_right()

    def _refresh_left(self):
        """Rebuild the originals column."""
        while self.left_layout.count() > 1:
            item = self.left_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.data_manager or not self.workspace_path:
            self._show_left_empty(True)
            return

        originals = self.data_manager.get_originals()

        if not originals:
            self._show_left_empty(True)
            return

        self._show_left_empty(False)

        first_original = None
        for filename, info in originals.items():
            orig_rel = info.get('path', f"originals/{filename}")
            file_path = self.data_manager._resolve_data_path(orig_rel)
            imported_at = info.get('imported_at')
            missing = not os.path.isfile(file_path)
            card = OriginalCard(filename, file_path, imported_at, missing)
            card.new_copy_clicked.connect(self._on_new_copy)
            card.menu_requested.connect(self._on_original_menu)
            card.mousePressEvent = lambda e, fn=filename: self._select_original(fn)
            self.left_layout.insertWidget(self.left_layout.count() - 1, card)
            if first_original is None:
                first_original = filename

        if self._selected_original and self._selected_original in originals:
            pass
        elif first_original:
            self._selected_original = first_original

        self._highlight_selected_original()

    def _refresh_right(self):
        """Rebuild the working copies column for the selected original."""
        while self.right_layout.count() > 1:
            item = self.right_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._selected_original or not self.data_manager:
            self.right_sub_header.setText("")
            self._show_right_empty(False)
            self.guidance_banner.hide()
            self.load_original_btn.hide()
            return

        orig_base = os.path.splitext(self._selected_original)[0]
        self.right_sub_header.setText(f"Copies of: {orig_base}")

        copies = self.data_manager.get_copies_for_original(self._selected_original)

        if not copies:
            self._show_right_empty(True)
            self.guidance_banner.show()
            self.load_original_btn.show()
            return

        self._show_right_empty(False)
        self.guidance_banner.hide()
        self.load_original_btn.show()

        for copy_rel in copies:
            file_path = self.data_manager._resolve_data_path(copy_rel)
            missing = not os.path.isfile(file_path)
            is_active = (copy_rel == self.current_dataset)
            card = CopyCard(copy_rel, file_path, is_active, missing)
            card.load_clicked.connect(self._on_load_copy)
            card.rename_clicked.connect(self._on_rename_copy)
            card.delete_clicked.connect(self._on_delete_copy)
            self.right_layout.insertWidget(self.right_layout.count() - 1, card)

    def _show_left_empty(self, show):
        self.left_empty.setVisible(show)
        self.left_scroll.setVisible(not show)
        self.import_btn.setVisible(not show)

    def _show_right_empty(self, show):
        self.right_empty.setVisible(show)
        self.right_scroll.setVisible(not show)

    def _select_original(self, filename):
        self._selected_original = filename
        self._highlight_selected_original()
        self._refresh_right()

    def _highlight_selected_original(self):
        for i in range(self.left_layout.count()):
            item = self.left_layout.itemAt(i)
            w = item.widget()
            if isinstance(w, OriginalCard):
                if w.filename == self._selected_original:
                    w.setStyleSheet(f"""
                        OriginalCard {{
                            background: #252b3b;
                            border: 1px solid {_accent()};
                            border-radius: 6px;
                        }}
                    """)
                else:
                    border = "rgba(245,158,11,0.5)" if w.missing else "rgba(255,255,255,0.08)"
                    w.setStyleSheet(f"""
                        OriginalCard {{
                            background: #1e2433;
                            border: 1px solid {border};
                            border-radius: 6px;
                        }}
                        OriginalCard:hover {{
                            border-color: rgba(255,255,255,0.18);
                        }}
                    """)

    # ── Actions ────────────────────────────────────────────────────────────

    def import_dataset(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Dataset", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path or not self.data_manager:
            return

        filename = os.path.basename(file_path)
        originals = self.data_manager.get_originals()

        if filename in originals:
            result = modal.show_import_duplicate(self, filename)
            if result == "cancel":
                return
            elif result == "create_copy":
                copy_rel = self.data_manager.create_working_copy(filename)
                if copy_rel:
                    self._selected_original = filename
                    self.refresh()
                return

        try:
            orig_name, copy_rel = self.data_manager.import_original(file_path)
            if orig_name:
                self._selected_original = orig_name
                self.refresh()
        except Exception as e:
            modal.show_error(self, "Error", f"Error importing dataset: {str(e)}")

    def _on_new_copy(self, original_filename):
        if not self.data_manager:
            return
        copy_rel = self.data_manager.create_working_copy(original_filename)
        if copy_rel:
            self._selected_original = original_filename
            self.refresh()

    def _on_banner_create(self):
        if self._selected_original:
            self._on_new_copy(self._selected_original)

    def _on_empty_create(self):
        if self._selected_original:
            self._on_new_copy(self._selected_original)

    def _on_load_copy(self, copy_rel_path):
        if not self.data_manager or not self.workspace_path:
            return
        file_path = self.data_manager._resolve_data_path(copy_rel_path)
        self.dataset_selected.emit(file_path)
        self.current_dataset = copy_rel_path
        self.refresh()

    def _on_load_original(self):
        if not self._selected_original:
            return
        result = modal.show_load_original_warning(self)
        if result == "cancel":
            return
        elif result == "create_copy":
            self._on_new_copy(self._selected_original)
            return

        orig_rel = f"originals/{self._selected_original}"
        file_path = self.data_manager._resolve_data_path(orig_rel)
        self.dataset_selected.emit(file_path)
        self.current_dataset = orig_rel
        self.refresh()

    def _on_original_menu(self, original_filename):
        """Show context menu for an original card."""
        menu = QMenu(self)
        load_action = menu.addAction("Load Original Directly")
        delete_action = menu.addAction("Delete Original")

        # Find the card's context button for positioning
        sender = self.sender()
        pos = sender.ctx_btn.mapToGlobal(sender.ctx_btn.rect().bottomLeft()) if hasattr(sender, 'ctx_btn') else QCursor.pos()

        action = menu.exec(pos)
        if action == load_action:
            self._on_load_original_for(original_filename)
        elif action == delete_action:
            self._on_delete_original(original_filename)

    def _on_load_original_for(self, original_filename):
        """Load a specific original directly (with warning)."""
        result = modal.show_load_original_warning(self)
        if result == "cancel":
            return
        elif result == "create_copy":
            self._on_new_copy(original_filename)
            return

        orig_rel = f"originals/{original_filename}"
        file_path = self.data_manager._resolve_data_path(orig_rel)
        self.dataset_selected.emit(file_path)
        self.current_dataset = orig_rel
        self.refresh()

    def _on_delete_original(self, original_filename):
        """Delete an original and all its copies."""
        if not self.data_manager:
            return
        copies = self.data_manager.get_copies_for_original(original_filename)
        if not modal.show_delete_original_confirm(self, original_filename, len(copies)):
            return

        deleted = self.data_manager.delete_original_with_copies(original_filename)

        # If active dataset was deleted, emit signal
        if self.data_manager.active_working_copy is None and self.current_dataset is not None:
            self.current_dataset = None
            self.dataset_deleted.emit("")

        if self._selected_original == original_filename:
            self._selected_original = None

        self.refresh()

    def _on_rename_copy(self, copy_rel_path):
        if copy_rel_path == self.current_dataset:
            modal.show_warning(self, "Cannot Rename", "The currently active dataset cannot be renamed.")
            return

        old_basename = os.path.basename(copy_rel_path)
        name_without_ext = os.path.splitext(old_basename)[0]
        new_name, ok = QInputDialog.getText(
            self, "Rename Dataset", "Enter new name:", text=name_without_ext
        )
        if not ok or not new_name:
            return
        if not new_name.endswith('.csv'):
            new_name += '.csv'

        copies_dir = self.data_manager._copies_folder()
        if os.path.exists(os.path.join(copies_dir, new_name)):
            modal.show_warning(self, "Error", f"A dataset named '{new_name}' already exists.")
            return

        if self.data_manager.rename_copy(copy_rel_path, new_name):
            self.dataset_renamed.emit(copy_rel_path, f"copies/{new_name}")
            self.refresh()

    def _on_delete_copy(self, copy_rel_path):
        display_name = os.path.basename(copy_rel_path)
        if not modal.show_question(self, "Delete Working Copy",
                                   f"Delete '{display_name}'?\nThis cannot be undone."):
            return

        was_active = (copy_rel_path == self.current_dataset)
        self.data_manager.delete_copy(copy_rel_path)
        self.dataset_deleted.emit(copy_rel_path)

        if was_active:
            self.current_dataset = None

        self.refresh()

    def _on_reset_workspace(self):
        """Handle Reset Workspace button."""
        if not modal.show_reset_workspace(self):
            return
        if self.data_manager:
            self.data_manager.reset_workspace_data()
        self.current_dataset = None
        self._selected_original = None
        self.workspace_reset.emit()
        self.accept()
