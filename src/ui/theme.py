"""
Centralized theme system for the Data Analysis Application.
Provides modern, consistent styling across all components.
"""

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication


# ── Design Tokens ──────────────────────────────────────────────────────────

DARK = {
    # Surfaces
    "bg_primary":      "#1a1b2e",   # Main background - deep navy
    "bg_secondary":    "#222340",   # Cards, panels
    "bg_tertiary":     "#2a2b4a",   # Elevated surfaces
    "bg_input":        "#161728",   # Input fields
    "bg_hover":        "#32335a",   # Hover state

    # Borders
    "border":          "#3a3b5c",   # Default border
    "border_subtle":   "#2e2f50",   # Subtle dividers
    "border_focus":    "#6c63ff",   # Focus ring

    # Text
    "text_primary":    "#e8e9f0",   # Primary text
    "text_secondary":  "#9496b0",   # Secondary / muted
    "text_disabled":   "#5a5c7a",   # Disabled
    "text_inverse":    "#ffffff",   # On accent backgrounds

    # Accent
    "accent":          "#6c63ff",   # Primary accent - vibrant purple
    "accent_hover":    "#7d75ff",   # Accent hover
    "accent_pressed":  "#5b52e0",   # Accent pressed
    "accent_subtle":   "#6c63ff22", # Accent with transparency

    # Semantic
    "success":         "#10b981",
    "warning":         "#f59e0b",
    "danger":          "#ef4444",
    "danger_hover":    "#dc2626",
    "info":            "#3b82f6",

    # Specific
    "tab_active":      "#6c63ff",
    "scrollbar_bg":    "#1a1b2e",
    "scrollbar_handle": "#3a3b5c",
    "scrollbar_hover": "#6c63ff",
    "table_alt":       "#1f2038",
    "table_grid":      "#2e2f50",
    "selection":       "#6c63ff",
    "header_bg":       "#222340",
}

LIGHT = {
    # Surfaces
    "bg_primary":      "#f5f6fa",
    "bg_secondary":    "#ffffff",
    "bg_tertiary":     "#ecedf5",
    "bg_input":        "#ffffff",
    "bg_hover":        "#e8e9f5",

    # Borders
    "border":          "#d1d3e0",
    "border_subtle":   "#e5e7f0",
    "border_focus":    "#6c63ff",

    # Text
    "text_primary":    "#1a1b2e",
    "text_secondary":  "#6b6d85",
    "text_disabled":   "#a0a2b5",
    "text_inverse":    "#ffffff",

    # Accent
    "accent":          "#6c63ff",
    "accent_hover":    "#5b52e0",
    "accent_pressed":  "#4a42c8",
    "accent_subtle":   "#6c63ff18",

    # Semantic
    "success":         "#059669",
    "warning":         "#d97706",
    "danger":          "#dc2626",
    "danger_hover":    "#b91c1c",
    "info":            "#2563eb",

    # Specific
    "tab_active":      "#6c63ff",
    "scrollbar_bg":    "#f5f6fa",
    "scrollbar_handle": "#c0c2d0",
    "scrollbar_hover": "#6c63ff",
    "table_alt":       "#f8f9fc",
    "table_grid":      "#e5e7f0",
    "selection":       "#6c63ff",
    "header_bg":       "#ffffff",
}

PALETTES = {"dark": DARK, "light": LIGHT}


# ── Font ───────────────────────────────────────────────────────────────────

FONT_FAMILY = "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
FONT_SIZE = "10pt"
FONT_SIZE_SMALL = "9pt"
FONT_SIZE_LARGE = "11pt"


# ── Radius & Spacing ──────────────────────────────────────────────────────

RADIUS_SM = "4px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
RADIUS_XL = "16px"


# ── Stylesheet Builder ────────────────────────────────────────────────────

def build_stylesheet(theme: str = "dark") -> str:
    """Build the full application stylesheet for the given theme."""
    c = PALETTES.get(theme, DARK)

    return f"""
    /* ── Global ──────────────────────────────────────────────── */
    QWidget {{
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE};
        color: {c["text_primary"]};
    }}

    QMainWindow {{
        background-color: {c["bg_primary"]};
    }}

    QDialog {{
        background-color: {c["bg_primary"]};
        color: {c["text_primary"]};
    }}

    /* ── Buttons ─────────────────────────────────────────────── */
    QPushButton {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: 7px 16px;
        border-radius: {RADIUS_MD};
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c["bg_hover"]};
        border-color: {c["accent"]};
    }}
    QPushButton:pressed {{
        background-color: {c["accent_pressed"]};
        color: {c["text_inverse"]};
        border-color: {c["accent_pressed"]};
    }}
    QPushButton:disabled {{
        background-color: {c["bg_primary"]};
        color: {c["text_disabled"]};
        border-color: {c["border_subtle"]};
    }}

    /* Primary button via property */
    QPushButton[cssClass="primary"] {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
        border: none;
        font-weight: 600;
    }}
    QPushButton[cssClass="primary"]:hover {{
        background-color: {c["accent_hover"]};
    }}
    QPushButton[cssClass="primary"]:pressed {{
        background-color: {c["accent_pressed"]};
    }}

    QPushButton[cssClass="danger"] {{
        background-color: {c["danger"]};
        color: {c["text_inverse"]};
        border: none;
        font-weight: 600;
    }}
    QPushButton[cssClass="danger"]:hover {{
        background-color: {c["danger_hover"]};
    }}

    QPushButton[cssClass="success"] {{
        background-color: {c["success"]};
        color: {c["text_inverse"]};
        border: none;
        font-weight: 600;
    }}
    QPushButton[cssClass="success"]:hover {{
        background-color: {"#059669" if theme == "dark" else "#047857"};
    }}

    /* ── Inputs ──────────────────────────────────────────────── */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: 6px 10px;
        border-radius: {RADIUS_SM};
        selection-background-color: {c["accent"]};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c["accent"]};
    }}

    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background-color: {c["bg_tertiary"]};
        border: none;
        width: 20px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover,
    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {c["bg_hover"]};
    }}

    /* ── ComboBox ─────────────────────────────────────────────── */
    QComboBox {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: 6px 10px;
        border-radius: {RADIUS_SM};
        min-height: 18px;
    }}
    QComboBox:hover {{
        border-color: {c["accent"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["accent"]};
        selection-color: {c["text_inverse"]};
        outline: none;
    }}

    /* ── CheckBox & RadioButton ──────────────────────────────── */
    QCheckBox {{
        spacing: 8px;
        color: {c["text_primary"]};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {c["border"]};
        border-radius: {RADIUS_SM};
        background-color: {c["bg_input"]};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c["accent"]};
        border-color: {c["accent"]};
    }}
    QCheckBox::indicator:hover {{
        border-color: {c["accent"]};
    }}

    QRadioButton {{
        spacing: 8px;
        color: {c["text_primary"]};
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {c["border"]};
        border-radius: 9px;
        background-color: {c["bg_input"]};
    }}
    QRadioButton::indicator:checked {{
        background-color: {c["accent"]};
        border-color: {c["accent"]};
    }}

    /* ── Table ────────────────────────────────────────────────── */
    QTableWidget, QTableView {{
        background-color: {c["bg_secondary"]};
        alternate-background-color: {c["table_alt"]};
        gridline-color: {c["table_grid"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: {RADIUS_SM};
        selection-background-color: {c["selection"]};
        selection-color: {c["text_inverse"]};
    }}
    QTableWidget::item, QTableView::item {{
        padding: 4px 8px;
    }}
    QHeaderView::section {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        padding: 6px 10px;
        border: none;
        border-right: 1px solid {c["border_subtle"]};
        border-bottom: 1px solid {c["border_subtle"]};
        font-weight: 600;
    }}

    /* ── Tabs ────────────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {c["border_subtle"]};
        border-radius: {RADIUS_SM};
        background-color: {c["bg_primary"]};
        top: -1px;
    }}
    QTabBar {{
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_secondary"]};
        padding: 10px 18px;
        min-width: 140px;
        border: 1px solid {c["border_subtle"]};
        border-bottom: none;
        border-top-left-radius: {RADIUS_MD};
        border-top-right-radius: {RADIUS_MD};
        margin-right: 2px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
        font-weight: 600;
    }}
    QTabBar::tab:!selected {{
        margin-top: 2px;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {c["bg_hover"]};
        color: {c["text_primary"]};
    }}

    /* ── GroupBox ─────────────────────────────────────────────── */
    QGroupBox {{
        background-color: {c["bg_secondary"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: {RADIUS_MD};
        margin-top: 14px;
        padding: 16px 12px 12px 12px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 12px;
        color: {c["accent"]};
        font-size: {FONT_SIZE};
        font-weight: 600;
    }}

    /* ── Splitter ─────────────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {c["border_subtle"]};
        border-radius: 2px;
    }}
    QSplitter::handle:horizontal {{
        width: 6px;
        margin: 6px 0px;
    }}
    QSplitter::handle:vertical {{
        height: 6px;
        margin: 0px 6px;
    }}
    QSplitter::handle:hover {{
        background-color: {c["accent"]};
    }}

    /* ── ScrollBar ────────────────────────────────────────────── */
    QScrollBar:vertical {{
        border: none;
        background-color: {c["scrollbar_bg"]};
        width: 10px;
        margin: 0px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c["scrollbar_handle"]};
        min-height: 30px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c["scrollbar_hover"]};
    }}
    QScrollBar:horizontal {{
        border: none;
        background-color: {c["scrollbar_bg"]};
        height: 10px;
        margin: 0px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c["scrollbar_handle"]};
        min-width: 30px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {c["scrollbar_hover"]};
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        border: none;
        background: none;
        height: 0px;
        width: 0px;
    }}
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: none;
    }}

    /* ── ScrollArea ───────────────────────────────────────────── */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    /* ── ToolTip ──────────────────────────────────────────────── */
    QToolTip {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: 6px 10px;
        border-radius: {RADIUS_SM};
        font-size: {FONT_SIZE_SMALL};
    }}

    /* ── Label ────────────────────────────────────────────────── */
    QLabel {{
        color: {c["text_primary"]};
        background-color: transparent;
    }}

    /* ── Menu ─────────────────────────────────────────────────── */
    QMenuBar {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border-bottom: 1px solid {c["border_subtle"]};
    }}
    QMenuBar::item:selected {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
    }}
    QMenu {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
        border-radius: {RADIUS_SM};
    }}

    /* ── ProgressBar ──────────────────────────────────────────── */
    QProgressBar {{
        border: none;
        background-color: {c["bg_tertiary"]};
        border-radius: {RADIUS_SM};
        text-align: center;
        color: {c["text_primary"]};
        height: 8px;
    }}
    QProgressBar::chunk {{
        background-color: {c["accent"]};
        border-radius: {RADIUS_SM};
    }}

    /* ── Frame ────────────────────────────────────────────────── */
    QFrame[frameShape="4"] {{
        color: {c["border_subtle"]};
        max-height: 1px;
    }}
    QFrame[frameShape="5"] {{
        color: {c["border_subtle"]};
        max-width: 1px;
    }}
    """


def build_palette(theme: str = "dark") -> QPalette:
    """Build a QPalette for the given theme."""
    c = PALETTES.get(theme, DARK)
    palette = QPalette()

    palette.setColor(QPalette.ColorRole.Window, QColor(c["bg_primary"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(c["text_primary"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(c["bg_input"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(c["bg_secondary"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["bg_tertiary"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(c["text_primary"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(c["text_primary"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(c["text_disabled"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(c["bg_tertiary"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(c["text_primary"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(c["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(c["text_inverse"]))
    palette.setColor(QPalette.ColorRole.Link, QColor(c["accent"]))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(c["accent_hover"]))

    return palette


def apply_theme(theme: str = "dark"):
    """Apply the given theme to the entire application."""
    app = QApplication.instance()
    if app is None:
        return

    app.setStyle("Fusion")
    app.setPalette(build_palette(theme))
    app.setStyleSheet(build_stylesheet(theme))


def get_colors(theme: str = "dark") -> dict:
    """Get the color dictionary for the given theme."""
    return PALETTES.get(theme, DARK)
