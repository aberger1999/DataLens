"""
Main window for the DataLens application.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QApplication, QLabel, QToolButton
)
from PyQt5.QtCore import Qt, QSettings, QEvent, QPoint, QRect
from PyQt5.QtGui import QIcon, QPixmap, QFont
from .components.home_screen import HomeScreen
from .components.workspace_view import WorkspaceView
from .components import modal
from .theme import apply_theme
from .dwm_helper import apply_modern_window_style, update_dwm_theme
from .resource_utils import resource_path
import ctypes
import ctypes.wintypes
import json
import os
import sys


# ---------------------------------------------------------------------------
# Win32 constants used by the custom title bar (WM_NCCALCSIZE path)
# ---------------------------------------------------------------------------
WM_NCCALCSIZE = 0x0083
WM_NCHITTEST = 0x0084
WM_NCACTIVATE = 0x0086

HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

SM_CXFRAME = 32
SM_CYFRAME = 33
SM_CXPADDEDBORDER = 92


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class _NCCALCSIZE_PARAMS(ctypes.Structure):
    _fields_ = [
        ("rgrc", _RECT * 3),
        ("lppos", ctypes.c_void_p),
    ]


class NativeTitleBar(QWidget):
    """
    Custom title bar that is drawn inside the client area of a native
    window. The window is NOT marked frameless — WM_NCCALCSIZE collapses
    the non-client area in MainWindow.nativeEvent, and WM_NCHITTEST marks
    this widget's background as HTCAPTION so Windows still handles drag,
    double-click-to-maximize, Aero Snap, and window animations.
    """

    HEIGHT = 48

    def __init__(self, main_window, theme="dark"):
        super().__init__(main_window)
        self._window = main_window
        self._theme = theme
        self.setFixedHeight(self.HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(10)

        # Logo — large and prominent
        self.logo_label = QLabel()
        logo_path = resource_path("assets", "DataLens_Logo_cropped.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaledToHeight(30, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled)
        self.logo_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.logo_label)

        # "DataLens" title — prominent, 12pt DemiBold
        self.title_label = QLabel("DataLens")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.DemiBold)
        self.title_label.setFont(title_font)
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Window-control buttons — narrow (40px) and native-looking
        self.min_btn = QToolButton()
        self.min_btn.setText("\u2013")      # en dash
        self.max_btn = QToolButton()
        self.max_btn.setText("\u25A1")      # □
        self.close_btn = QToolButton()
        self.close_btn.setText("\u2715")    # ✕

        for btn in (self.min_btn, self.max_btn, self.close_btn):
            btn.setFixedSize(40, self.HEIGHT)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.ArrowCursor)
            layout.addWidget(btn)

        self.min_btn.clicked.connect(main_window.showMinimized)
        self.max_btn.clicked.connect(self._toggle_max)
        self.close_btn.clicked.connect(main_window.close)

        self.apply_theme(theme)

    def _toggle_max(self):
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def update_max_icon(self):
        if self._window.isMaximized():
            self.max_btn.setText("\u2752")  # restore glyph
        else:
            self.max_btn.setText("\u25A1")

    def button_rects(self):
        """Return the button rects in this widget's local coordinate
        system, used by WM_NCHITTEST to avoid marking button pixels as
        HTCAPTION."""
        return (
            self.min_btn.geometry(),
            self.max_btn.geometry(),
            self.close_btn.geometry(),
        )

    def apply_theme(self, theme):
        self._theme = theme
        if theme == "dark":
            bg = "#0f1117"
            text = "#ffffff"
            btn_hover = "rgba(255,255,255,0.10)"
        else:
            bg = "#e8eaf0"
            text = "#0f172a"
            btn_hover = "rgba(0,0,0,0.08)"

        self.setStyleSheet(
            f"NativeTitleBar {{ background-color: {bg}; }}"
        )
        self.title_label.setStyleSheet(
            f"color: {text}; background: transparent;"
        )
        self.logo_label.setStyleSheet("background: transparent;")

        btn_style = f"""
            QToolButton {{
                border: none;
                color: {text};
                background: transparent;
                font-size: 11pt;
            }}
            QToolButton:hover {{
                background-color: {btn_hover};
            }}
        """
        close_style = f"""
            QToolButton {{
                border: none;
                color: {text};
                background: transparent;
                font-size: 11pt;
            }}
            QToolButton:hover {{
                background-color: #e81123;
                color: white;
            }}
        """
        self.min_btn.setStyleSheet(btn_style)
        self.max_btn.setStyleSheet(btn_style)
        self.close_btn.setStyleSheet(close_style)


class MainWindow(QMainWindow):
    """Main window of the application."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self._settings = QSettings()
        self.current_theme = self._load_theme()
        self.init_ui()
        self.setup_connections()

    def _load_theme(self):
        """Load persisted theme; defaults to 'dark'."""
        value = self._settings.value("theme", "dark")
        return value if value in ("dark", "light") else "dark"

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("DataLens")
        self.setMinimumSize(1200, 800)

        # Set icon explicitly on this window (supplements QApplication icon)
        icon_path = resource_path("assets", "DataLens_Logo.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom native title bar (inside the client area — window is
        # NOT marked frameless; WM_NCCALCSIZE collapses the non-client
        # area and WM_NCHITTEST marks this widget as HTCAPTION).
        self.title_bar = NativeTitleBar(self, theme=self.current_theme)
        layout.addWidget(self.title_bar)

        self.stacked_widget = QStackedWidget()

        self.home_screen = HomeScreen(initial_theme=self.current_theme)
        self.stacked_widget.addWidget(self.home_screen)

        self.workspace_view = WorkspaceView()
        self.stacked_widget.addWidget(self.workspace_view)

        layout.addWidget(self.stacked_widget)

        # Apply the centralized theme
        apply_theme(self.current_theme)
        self.workspace_view.update_theme(self.current_theme)

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
        self.title_bar.apply_theme(theme)
        hwnd = int(self.winId())
        update_dwm_theme(hwnd, theme)
        self._settings.setValue("theme", theme)

    def showEvent(self, event):
        """Apply Windows 11 DWM styling once the window handle is valid."""
        super().showEvent(event)
        if not getattr(self, '_dwm_applied', False):
            self._dwm_applied = True
            hwnd = int(self.winId())
            apply_modern_window_style(hwnd, self.current_theme)

    def changeEvent(self, event):
        """Keep the max/restore button glyph in sync with window state."""
        if event.type() == QEvent.WindowStateChange:
            if hasattr(self, 'title_bar'):
                self.title_bar.update_max_icon()
        super().changeEvent(event)

    # ------------------------------------------------------------------
    # Native Windows message handling for the custom title bar
    # ------------------------------------------------------------------
    def nativeEvent(self, eventType, message):
        if eventType != "windows_generic_MSG" or sys.platform != "win32":
            return False, 0

        try:
            msg = ctypes.wintypes.MSG.from_address(int(message))
        except Exception:
            return False, 0

        # --- WM_NCCALCSIZE: collapse the non-client area -------------
        if msg.message == WM_NCCALCSIZE and msg.wParam:
            params = _NCCALCSIZE_PARAMS.from_address(msg.lParam)
            if self.isMaximized():
                # When maximized, Windows sizes the window ~8px beyond
                # the work area on every side. Inset so the title bar
                # contents are not clipped off-screen.
                user32 = ctypes.windll.user32
                cx_frame = user32.GetSystemMetrics(SM_CXFRAME)
                cy_frame = user32.GetSystemMetrics(SM_CYFRAME)
                padded = user32.GetSystemMetrics(SM_CXPADDEDBORDER)
                params.rgrc[0].left += cx_frame + padded
                params.rgrc[0].right -= cx_frame + padded
                params.rgrc[0].top += cy_frame + padded
                params.rgrc[0].bottom -= cy_frame + padded
            # Returning 0 (with the rect unchanged, apart from the
            # maximized inset above) tells Windows the entire proposed
            # window rect is the client rect — i.e. no non-client area.
            return True, 0

        # --- WM_NCHITTEST: classify the point under the cursor -------
        if msg.message == WM_NCHITTEST:
            x = ctypes.c_short(msg.lParam & 0xFFFF).value
            y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
            local = self.mapFromGlobal(QPoint(x, y))
            lx, ly = local.x(), local.y()
            w, h = self.width(), self.height()
            border = 6

            if not self.isMaximized():
                on_left = 0 <= lx < border
                on_right = w - border <= lx < w
                on_top = 0 <= ly < border
                on_bottom = h - border <= ly < h

                if on_top and on_left:
                    return True, HTTOPLEFT
                if on_top and on_right:
                    return True, HTTOPRIGHT
                if on_bottom and on_left:
                    return True, HTBOTTOMLEFT
                if on_bottom and on_right:
                    return True, HTBOTTOMRIGHT
                if on_top:
                    return True, HTTOP
                if on_bottom:
                    return True, HTBOTTOM
                if on_left:
                    return True, HTLEFT
                if on_right:
                    return True, HTRIGHT

            # Title bar region
            if hasattr(self, 'title_bar') and 0 <= ly < self.title_bar.height():
                tb_local = self.title_bar.mapFromGlobal(QPoint(x, y))
                for rect in self.title_bar.button_rects():
                    if rect.contains(tb_local):
                        # Let Qt route clicks to the QToolButton.
                        return True, HTCLIENT
                return True, HTCAPTION

            # Anywhere else — regular client area (Qt handles it).
            return True, HTCLIENT

        # Let Qt handle everything else
        return False, 0

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
