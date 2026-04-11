"""
Centralized theme system for the DataLens application.
Deep navy/slate dark theme with indigo accent. Every color, radius,
and spacing token lives here so the look can be tuned in one place.
"""

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication


# ── Design Tokens ──────────────────────────────────────────────────────────

DARK = {
    # Surfaces  (deep navy / slate)
    "bg_base":         "#0f1117",   # Deepest background (window chrome)
    "bg_primary":      "#131620",   # Main content background
    "bg_secondary":    "#1a1f2e",   # Panels, sidebars
    "bg_tertiary":     "#252b3b",   # Cards, elevated surfaces
    "bg_input":        "#1e2433",   # Input fields, wells
    "bg_hover":        "#2d3548",   # Hover state on surfaces
    "bg_active":       "#343d52",   # Pressed / active state

    # Borders
    "border":          "rgba(255,255,255,0.10)",   # Default border
    "border_subtle":   "rgba(255,255,255,0.06)",   # Very faint dividers
    "border_medium":   "rgba(255,255,255,0.15)",   # Input borders
    "border_focus":    "#6366f1",                    # Focus ring

    # Text
    "text_primary":    "#e2e4ed",   # Primary text
    "text_secondary":  "#8b8fa3",   # Secondary / muted
    "text_disabled":   "#4b5063",   # Disabled
    "text_inverse":    "#ffffff",   # On accent backgrounds
    "text_label":      "#6b7280",   # Small labels, captions

    # Accent  (indigo)
    "accent":          "#6366f1",   # Primary accent
    "accent_hover":    "#7577f5",   # Accent hover
    "accent_pressed":  "#5254cc",   # Accent pressed
    "accent_subtle":   "rgba(99,102,241,0.12)",  # Accent tint for backgrounds
    "accent_glow":     "rgba(99,102,241,0.35)",  # Focus glow

    # Semantic
    "success":         "#10b981",
    "success_hover":   "#059669",
    "warning":         "#f59e0b",
    "warning_hover":   "#d97706",
    "danger":          "#ef4444",
    "danger_hover":    "#dc2626",
    "info":            "#3b82f6",

    # Table
    "table_alt":       "#161b27",   # Alternating row
    "table_grid":      "rgba(255,255,255,0.05)",
    "table_header":    "#1e2536",

    # Scrollbar
    "scrollbar_bg":    "#0f1117",
    "scrollbar_handle": "#2d3548",
    "scrollbar_hover": "#6366f1",

    # Selection
    "selection":       "#6366f1",
    "header_bg":       "#1a1f2e",
}

LIGHT = {
    # Surfaces
    "bg_base":         "#f0f2f5",
    "bg_primary":      "#f5f6fa",
    "bg_secondary":    "#ffffff",
    "bg_tertiary":     "#ecedf5",
    "bg_input":        "#ffffff",
    "bg_hover":        "#e8e9f5",
    "bg_active":       "#dddff0",

    # Borders
    "border":          "rgba(0,0,0,0.10)",
    "border_subtle":   "rgba(0,0,0,0.06)",
    "border_medium":   "rgba(0,0,0,0.15)",
    "border_focus":    "#6366f1",

    # Text
    "text_primary":    "#1a1b2e",
    "text_secondary":  "#6b6d85",
    "text_disabled":   "#a0a2b5",
    "text_inverse":    "#ffffff",
    "text_label":      "#6b7280",

    # Accent
    "accent":          "#6366f1",
    "accent_hover":    "#5254cc",
    "accent_pressed":  "#4345b0",
    "accent_subtle":   "rgba(99,102,241,0.10)",
    "accent_glow":     "rgba(99,102,241,0.25)",

    # Semantic
    "success":         "#059669",
    "success_hover":   "#047857",
    "warning":         "#d97706",
    "warning_hover":   "#b45309",
    "danger":          "#dc2626",
    "danger_hover":    "#b91c1c",
    "info":            "#2563eb",

    # Table
    "table_alt":       "#f8f9fc",
    "table_grid":      "rgba(0,0,0,0.06)",
    "table_header":    "#f0f1f8",

    # Scrollbar
    "scrollbar_bg":    "#f5f6fa",
    "scrollbar_handle": "#c0c2d0",
    "scrollbar_hover": "#6366f1",

    # Selection
    "selection":       "#6366f1",
    "header_bg":       "#ffffff",
}

PALETTES = {"dark": DARK, "light": LIGHT}

# Currently active theme (updated by apply_theme)
_current_theme = "dark"


def current_theme() -> str:
    """Return the name of the currently active theme."""
    return _current_theme


# ── Font ───────────────────────────────────────────────────────────────────

FONT_FAMILY = "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
FONT_SIZE   = "10pt"
FONT_SIZE_SMALL = "9pt"
FONT_SIZE_LARGE = "11pt"
FONT_SIZE_XS = "8pt"


# ── Radius & Spacing ────────────────────────────────────────────────────

RADIUS_SM = "4px"
RADIUS_MD = "6px"
RADIUS_LG = "10px"
RADIUS_XL = "14px"

BTN_HEIGHT   = "34px"
BTN_PADDING  = "7px 16px"
INPUT_PADDING = "6px 10px"
CARD_PADDING = "16px"


# ── Stylesheet Builder ────────────────────────────────────────────────────

def build_stylesheet(theme: str = "dark") -> str:
    """Build the full application stylesheet for the given theme."""
    c = PALETTES.get(theme, DARK)

    return f"""
    /* ================================================================
       GLOBAL
       ================================================================ */
    QWidget {{
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE};
        color: {c["text_primary"]};
        outline: none;
    }}
    QMainWindow {{
        background-color: {c["bg_base"]};
    }}
    QDialog {{
        background-color: {c["bg_primary"]};
        color: {c["text_primary"]};
    }}

    /* ================================================================
       BUTTONS
       ================================================================ */

    /* -- Default (outlined / ghost) --------------------------------- */
    QPushButton {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: {BTN_PADDING};
        border-radius: {RADIUS_MD};
        min-height: 20px;
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
    QPushButton:checked {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
        border-color: {c["accent"]};
        font-weight: 600;
    }}

    /* -- Primary (accent filled) ----------------------------------- */
    QPushButton[cssClass="primary"] {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
        border: 1px solid {c["accent"]};
        font-weight: 600;
    }}
    QPushButton[cssClass="primary"]:hover {{
        background-color: {c["accent_hover"]};
        border-color: {c["accent_hover"]};
    }}
    QPushButton[cssClass="primary"]:pressed {{
        background-color: {c["accent_pressed"]};
    }}
    QPushButton[cssClass="primary"]:disabled {{
        background-color: {c["bg_primary"]};
        color: {c["text_disabled"]};
        border-color: {c["border_subtle"]};
    }}

    /* -- Success (green filled) ------------------------------------ */
    QPushButton[cssClass="success"] {{
        background-color: {c["success"]};
        color: {c["text_inverse"]};
        border: 1px solid {c["success"]};
        font-weight: 600;
    }}
    QPushButton[cssClass="success"]:hover {{
        background-color: {c["success_hover"]};
        border-color: {c["success_hover"]};
    }}
    QPushButton[cssClass="success"]:disabled {{
        background-color: {c["bg_primary"]};
        color: {c["text_disabled"]};
        border-color: {c["border_subtle"]};
    }}

    /* -- Danger (red filled) --------------------------------------- */
    QPushButton[cssClass="danger"] {{
        background-color: {c["danger"]};
        color: {c["text_inverse"]};
        border: 1px solid {c["danger"]};
        font-weight: 600;
    }}
    QPushButton[cssClass="danger"]:hover {{
        background-color: {c["danger_hover"]};
        border-color: {c["danger_hover"]};
    }}

    /* -- Outline (subtle, secondary actions) ----------------------- */
    QPushButton[cssClass="outline"] {{
        background-color: transparent;
        color: {c["text_primary"]};
        border: 1px solid {c["border_medium"]};
    }}
    QPushButton[cssClass="outline"]:hover {{
        background-color: {c["bg_hover"]};
        border-color: {c["accent"]};
        color: {c["accent"]};
    }}

    /* -- Ghost (no background, compact) ----------------------------- */
    QPushButton[cssClass="ghost"] {{
        background-color: transparent;
        color: {c["text_primary"]};
        border: none;
        padding: 2px;
        min-height: 0px;
    }}
    QPushButton[cssClass="ghost"]:hover {{
        background-color: {c["bg_hover"]};
        color: {c["text_primary"]};
    }}

    /* -- Warning (amber filled) ------------------------------------ */
    QPushButton[cssClass="warning"] {{
        background-color: {c["warning"]};
        color: {c["text_inverse"]};
        border: 1px solid {c["warning"]};
        font-weight: 600;
    }}
    QPushButton[cssClass="warning"]:hover {{
        background-color: {c["warning_hover"]};
        border-color: {c["warning_hover"]};
    }}

    /* ================================================================
       INPUTS  (text, spin, double-spin)
       ================================================================ */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_medium"]};
        padding: {INPUT_PADDING};
        border-radius: {RADIUS_MD};
        selection-background-color: {c["accent"]};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c["accent"]};
    }}
    QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: {c["bg_primary"]};
        color: {c["text_disabled"]};
        border-color: {c["border_subtle"]};
    }}

    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background-color: {c["bg_tertiary"]};
        border: none;
        width: 20px;
        border-radius: 2px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover,
    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {c["bg_hover"]};
    }}

    /* ================================================================
       COMBOBOX
       ================================================================ */
    QComboBox {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_medium"]};
        padding: {INPUT_PADDING};
        border-radius: {RADIUS_MD};
        min-height: 18px;
    }}
    QComboBox:hover {{
        border-color: {c["accent"]};
    }}
    QComboBox:focus {{
        border-color: {c["accent"]};
    }}
    QComboBox:disabled {{
        background-color: {c["bg_primary"]};
        color: {c["text_disabled"]};
        border-color: {c["border_subtle"]};
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
        padding: 4px;
        border-radius: {RADIUS_MD};
    }}

    /* ================================================================
       CHECKBOX  &  RADIOBUTTON
       ================================================================ */
    QCheckBox {{
        spacing: 8px;
        color: {c["text_primary"]};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {c["border_medium"]};
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
    QCheckBox:disabled {{
        color: {c["text_disabled"]};
    }}

    QRadioButton {{
        spacing: 8px;
        color: {c["text_primary"]};
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {c["border_medium"]};
        border-radius: 9px;
        background-color: {c["bg_input"]};
    }}
    QRadioButton::indicator:checked {{
        background-color: {c["accent"]};
        border-color: {c["accent"]};
    }}

    /* ================================================================
       TABLE
       ================================================================ */
    QTableWidget, QTableView {{
        background-color: {c["bg_secondary"]};
        alternate-background-color: {c["table_alt"]};
        gridline-color: {c["table_grid"]};
        border: 1px solid {c["border"]};
        border-radius: {RADIUS_MD};
        selection-background-color: {c["selection"]};
        selection-color: {c["text_inverse"]};
    }}
    QTableWidget::item, QTableView::item {{
        padding: 5px 10px;
        border-bottom: 1px solid {c["table_grid"]};
    }}
    QTableWidget::item:hover, QTableView::item:hover {{
        background-color: {c["bg_hover"]};
    }}
    QHeaderView::section {{
        background-color: {c["table_header"]};
        color: {c["text_secondary"]};
        padding: 8px 10px;
        border: none;
        border-right: 1px solid {c["table_grid"]};
        border-bottom: 2px solid {c["border"]};
        font-weight: 600;
        font-size: {FONT_SIZE_SMALL};
        text-transform: uppercase;
    }}

    /* ================================================================
       TABS
       ================================================================ */
    QTabWidget::pane {{
        border: 1px solid {c["border"]};
        border-radius: {RADIUS_MD};
        background-color: {c["bg_primary"]};
        top: -1px;
    }}
    QTabBar {{
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {c["text_secondary"]};
        padding: 10px 20px;
        min-width: 138px;
        border: none;
        border-bottom: 3px solid transparent;
        margin-right: 2px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        color: {c["accent"]};
        border-bottom: 3px solid {c["accent"]};
        font-weight: 600;
    }}
    QTabBar::tab:hover:!selected {{
        color: {c["text_primary"]};
        background-color: {c["accent_subtle"]};
        border-bottom: 3px solid {c["accent_subtle"]};
    }}

    /* ================================================================
       GROUPBOX  (section containers)
       ================================================================ */
    QGroupBox {{
        background-color: {c["bg_secondary"]};
        border: 1px solid {c["border"]};
        border-radius: {RADIUS_LG};
        margin-top: 16px;
        padding: 20px 14px 14px 14px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 10px;
        color: {c["accent"]};
        font-size: {FONT_SIZE_SMALL};
        font-weight: 700;
        letter-spacing: 0.5px;
    }}

    /* ================================================================
       SPLITTER
       ================================================================ */
    QSplitter::handle {{
        background-color: {c["border"]};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
        margin: 0px;
    }}
    QSplitter::handle:vertical {{
        height: 1px;
        margin: 0px;
    }}
    QSplitter::handle:hover {{
        background-color: {c["accent"]};
    }}

    /* ================================================================
       SCROLLBAR
       ================================================================ */
    QScrollBar:vertical {{
        border: none;
        background-color: {c["scrollbar_bg"]};
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c["scrollbar_handle"]};
        min-height: 30px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c["scrollbar_hover"]};
    }}
    QScrollBar:horizontal {{
        border: none;
        background-color: {c["scrollbar_bg"]};
        height: 8px;
        margin: 0px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c["scrollbar_handle"]};
        min-width: 30px;
        border-radius: 4px;
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

    /* ================================================================
       SCROLLAREA
       ================================================================ */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    /* ================================================================
       TOOLTIP
       ================================================================ */
    QToolTip {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: 6px 10px;
        border-radius: {RADIUS_MD};
        font-size: {FONT_SIZE_SMALL};
    }}

    /* ================================================================
       LABEL
       ================================================================ */
    QLabel {{
        color: {c["text_primary"]};
        background-color: transparent;
    }}

    /* ================================================================
       MENU
       ================================================================ */
    QMenuBar {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border-bottom: 1px solid {c["border"]};
        padding: 2px;
    }}
    QMenuBar::item:selected {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
        border-radius: {RADIUS_SM};
    }}
    QMenu {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        padding: 4px;
        border-radius: {RADIUS_MD};
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: {RADIUS_SM};
    }}
    QMenu::item:selected {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {c["border"]};
        margin: 4px 8px;
    }}

    /* ================================================================
       PROGRESSBAR
       ================================================================ */
    QProgressBar {{
        border: none;
        background-color: {c["bg_tertiary"]};
        border-radius: {RADIUS_SM};
        text-align: center;
        color: {c["text_primary"]};
        height: 6px;
    }}
    QProgressBar::chunk {{
        background-color: {c["accent"]};
        border-radius: {RADIUS_SM};
    }}

    /* ================================================================
       FRAME  (horizontal / vertical lines)
       ================================================================ */
    QFrame[frameShape="4"] {{
        color: {c["border"]};
        max-height: 1px;
    }}
    QFrame[frameShape="5"] {{
        color: {c["border"]};
        max-width: 1px;
    }}

    /* ================================================================
       SLIDER
       ================================================================ */
    QSlider::groove:horizontal {{
        border: none;
        height: 4px;
        background: {c["bg_tertiary"]};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {c["accent"]};
        border: none;
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {c["accent_hover"]};
    }}
    QSlider::sub-page:horizontal {{
        background: {c["accent"]};
        border-radius: 2px;
    }}

    /* ================================================================
       LISTWIDGET
       ================================================================ */
    QListWidget {{
        background-color: {c["bg_secondary"]};
        border: 1px solid {c["border"]};
        border-radius: {RADIUS_MD};
        outline: none;
    }}
    QListWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid {c["border_subtle"]};
    }}
    QListWidget::item:selected {{
        background-color: {c["accent"]};
        color: {c["text_inverse"]};
        border-radius: {RADIUS_SM};
    }}
    QListWidget::item:hover:!selected {{
        background-color: {c["bg_hover"]};
    }}

    /* ================================================================
       STACKED WIDGET
       ================================================================ */
    QStackedWidget {{
        background-color: {c["bg_primary"]};
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
    global _current_theme
    _current_theme = theme

    app = QApplication.instance()
    if app is None:
        return

    app.setStyle("Fusion")
    app.setPalette(build_palette(theme))
    app.setStyleSheet(build_stylesheet(theme))


def get_colors(theme: str = "dark") -> dict:
    """Get the color dictionary for the given theme."""
    return PALETTES.get(theme, DARK)


def apply_chart_theme(fig, ax, theme: str = "dark", bg_override=None):
    """Apply theme-aware styling to a matplotlib figure and axes.

    Parameters
    ----------
    fig, ax
        The matplotlib figure and axes to style.
    theme
        "dark" or "light".
    bg_override
        Optional color (hex string or matplotlib-accepted color) used for
        both the figure patch and the axes face. When ``None`` the theme's
        default chart background is used.
    """
    if theme == "light":
        default_fig_bg = LIGHT["bg_secondary"]   # #ffffff
        default_ax_bg = "#ffffff"
        text_color = "#1a1b2e"
        tick_color = "#374151"
        title_color = "#0f172a"
        spine_color = (0.0, 0.0, 0.0, 0.18)
        legend_bg = "#ffffff"
        legend_edge = (0.0, 0.0, 0.0, 0.15)
    else:
        default_fig_bg = DARK["bg_secondary"]    # #1a1f2e
        default_ax_bg = DARK["bg_input"]         # #1e2433
        text_color = "#cbd5e1"
        tick_color = "#cbd5e1"
        title_color = "#f1f5f9"
        spine_color = (1.0, 1.0, 1.0, 0.15)
        legend_bg = DARK["bg_input"]
        legend_edge = (1.0, 1.0, 1.0, 0.15)

    fig_bg = bg_override if bg_override else default_fig_bg
    ax_bg = bg_override if bg_override else default_ax_bg

    fig.patch.set_facecolor(fig_bg)
    ax.set_facecolor(ax_bg)

    ax.tick_params(colors=tick_color)
    ax.xaxis.label.set_color(text_color)
    ax.yaxis.label.set_color(text_color)
    ax.title.set_color(title_color)

    ax.spines['bottom'].set_color(spine_color)
    ax.spines['left'].set_color(spine_color)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(tick_color)

    legend = ax.get_legend()
    if legend is not None:
        legend.get_frame().set_facecolor(legend_bg)
        for text in legend.get_texts():
            text.set_color(text_color)
        legend.get_frame().set_edgecolor(legend_edge)

    for cb_ax in fig.get_axes():
        if cb_ax is not ax:
            cb_ax.tick_params(colors=tick_color)
            cb_ax.yaxis.label.set_color(text_color)
            for label in cb_ax.get_yticklabels():
                label.set_color(tick_color)


def apply_dark_theme(fig, ax):
    """Apply dark theme styling to a matplotlib figure and axes.

    Call this after plotting data and before canvas.draw() so that all
    text, spines, and backgrounds match the app's dark palette.
    """
    c = DARK

    # Figure & axes background
    fig.patch.set_facecolor(c["bg_secondary"])      # #1a1f2e
    ax.set_facecolor(c["bg_input"])                  # #1e2433

    # Tick marks
    ax.tick_params(colors='#cbd5e1')

    # Axis labels
    ax.xaxis.label.set_color('#cbd5e1')
    ax.yaxis.label.set_color('#cbd5e1')

    # Title
    ax.title.set_color('#f1f5f9')

    # Spines
    ax.spines['bottom'].set_color((1.0, 1.0, 1.0, 0.15))
    ax.spines['left'].set_color((1.0, 1.0, 1.0, 0.15))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Tick label colors
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color('#cbd5e1')

    # Legend
    legend = ax.get_legend()
    if legend is not None:
        legend.get_frame().set_facecolor(c["bg_input"])
        for text in legend.get_texts():
            text.set_color('#cbd5e1')
        legend.get_frame().set_edgecolor((1.0, 1.0, 1.0, 0.15))

    # Colorbar (if any)
    for cb_ax in fig.get_axes():
        if cb_ax is not ax:
            cb_ax.tick_params(colors='#cbd5e1')
            cb_ax.yaxis.label.set_color('#cbd5e1')
            for label in cb_ax.get_yticklabels():
                label.set_color('#cbd5e1')
