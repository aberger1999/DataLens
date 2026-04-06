"""
Report generator panel for creating comprehensive data analysis reports.

Redesigned to match Feature Engineering / Machine Learning tab design language:
left config panel + right preview pane, chip selectors, section headers, etc.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QScrollArea, QSplitter, QSizePolicy, QFileDialog,
    QGridLayout, QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QTimer, QAbstractAnimation,
)
from PyQt5.QtGui import QCursor, QFont, QColor
from PyQt5 import sip
from . import modal
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import jinja2
from ..theme import apply_dark_theme
from ui.theme import get_colors
import os
import tempfile
import base64

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
#  Shared styling helpers  (same pattern as ML / Feature Engineering tabs)
# ═══════════════════════════════════════════════════════════════════════════

def _colors():
    return get_colors("dark")


def _section_header(text):
    c = _colors()
    frame = QWidget()
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(0, 6, 0, 2)
    lay.setSpacing(4)
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(f"""
        QLabel {{
            color: {c['accent']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
            padding: 0;
            background: transparent;
        }}
    """)
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"background: {c['border']}; max-height: 1px;")
    lay.addWidget(lbl)
    lay.addWidget(line)
    return frame


def _input_style():
    c = _colors()
    return f"""
        QLineEdit, QTextEdit {{
            background-color: {c['bg_input']};
            color: {c['text_primary']};
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 22px;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {c['accent']};
        }}
    """


def _chip_style(selected=False):
    c = _colors()
    if selected:
        return f"""
            QPushButton {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border: 1px solid {c['accent']};
                border-radius: 14px;
                padding: 4px 14px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
        """
    else:
        return f"""
            QPushButton {{
                background-color: {c['bg_tertiary']};
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 14px;
                padding: 4px 14px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
                border-color: {c['accent']};
            }}
        """


def _scroll_wrap(widget):
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    return scroll


# ═══════════════════════════════════════════════════════════════════════════
#  Chip toggle group  (multi-select)
# ═══════════════════════════════════════════════════════════════════════════

class _ChipToggleGroup(QWidget):
    """A flow-wrap grid of toggleable chip buttons (multi-select)."""

    changed = pyqtSignal()

    def __init__(self, columns=3, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._chips = {}       # key -> QPushButton
        self._selected = set()
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def add_chip(self, key, label, checked=True):
        btn = QPushButton(label)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        if checked:
            self._selected.add(key)
        btn.setStyleSheet(_chip_style(checked))
        btn.clicked.connect(lambda: self._toggle(key))
        idx = len(self._chips)
        row, col = divmod(idx, self._columns)
        self._layout.addWidget(btn, row, col)
        self._chips[key] = btn

    def _toggle(self, key):
        if key in self._selected:
            self._selected.discard(key)
        else:
            self._selected.add(key)
        self._chips[key].setStyleSheet(_chip_style(key in self._selected))
        self.changed.emit()

    def is_checked(self, key):
        return key in self._selected


# ═══════════════════════════════════════════════════════════════════════════
#  Single-select chip row
# ═══════════════════════════════════════════════════════════════════════════

class _SingleChipRow(QWidget):
    """A horizontal row of single-select chips."""

    changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._btns = {}
        self._selected = ""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def add_chip(self, key, label):
        btn = QPushButton(label)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(_chip_style(False))
        btn.clicked.connect(lambda: self._on_click(key))
        self._layout.addWidget(btn)
        self._btns[key] = btn

    def _on_click(self, key):
        self._selected = key
        for k, btn in self._btns.items():
            btn.setStyleSheet(_chip_style(k == key))
        self.changed.emit(key)

    def select(self, key):
        self._on_click(key)

    def selected(self):
        return self._selected


# ═══════════════════════════════════════════════════════════════════════════
#  Color swatch selector
# ═══════════════════════════════════════════════════════════════════════════

_ACCENT_SWATCHES = [
    ("indigo",  "#6366f1"),
    ("cyan",    "#06b6d4"),
    ("emerald", "#10b981"),
    ("amber",   "#f59e0b"),
    ("rose",    "#f43f5e"),
    ("slate",   "#94a3b8"),
]


class _ColorSwatchRow(QWidget):
    """Row of small colour circles; one is selected at a time."""

    changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected = _ACCENT_SWATCHES[0][0]
        self._btns = {}
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        for key, colour in _ACCENT_SWATCHES:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda _, k=key: self._on_click(k))
            self._btns[key] = (btn, colour)
            lay.addWidget(btn)
        lay.addStretch()
        self._repaint()

    def _on_click(self, key):
        self._selected = key
        self._repaint()
        self.changed.emit(self.selected_color())

    def _repaint(self):
        for key, (btn, colour) in self._btns.items():
            ring = "2.5px solid #ffffff" if key == self._selected else "2px solid transparent"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colour};
                    border: {ring};
                    border-radius: 13px;
                    min-height: 0px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    border: 2.5px solid rgba(255,255,255,0.5);
                }}
            """)

    def selected_color(self):
        for key, (_, colour) in self._btns.items():
            if key == self._selected:
                return colour
        return _ACCENT_SWATCHES[0][1]

    def select(self, key):
        self._on_click(key)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN PANEL
# ═══════════════════════════════════════════════════════════════════════════

class ReportGeneratorPanel(QWidget):
    """Panel for generating comprehensive data analysis reports."""

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.workspace_path = None

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        template_dir = os.path.join(project_root, "templates")
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )
        self._temp_files = []
        self._preview_stale = False
        self._last_html = ""
        # Stores the last generated report data (without style tokens)
        # so style controls can re-render with new styles without regenerating data.
        self._last_report_data = None

        self.init_ui()
        self.setup_connections()

    # ── UI Construction ────────────────────────────────────────────────────

    def init_ui(self):
        c = _colors()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── LEFT PANEL (config) ──────────────────────────────────────────
        left_outer = QWidget()
        left_outer.setFixedWidth(380)
        left_outer_lay = QVBoxLayout(left_outer)
        left_outer_lay.setContentsMargins(0, 0, 0, 0)
        left_outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        # ── REPORT TITLE ──
        body_lay.addWidget(_section_header("Report Title"))
        self.title_edit = QLineEdit("Data Analysis Report")
        self.title_edit.setStyleSheet(_input_style())
        body_lay.addWidget(self.title_edit)

        # ── STYLE ──
        body_lay.addWidget(_section_header("Style"))

        # Font family
        font_lbl = QLabel("Font")
        font_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px; background: transparent;")
        body_lay.addWidget(font_lbl)
        self.font_chips = _SingleChipRow()
        self.font_chips.add_chip("sans", "Sans-serif")
        self.font_chips.add_chip("serif", "Serif")
        self.font_chips.add_chip("mono", "Monospace")
        self.font_chips.select("sans")
        body_lay.addWidget(self.font_chips)

        # Font size
        size_lbl = QLabel("Size")
        size_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px; background: transparent;")
        body_lay.addWidget(size_lbl)
        self.size_chips = _SingleChipRow()
        self.size_chips.add_chip("small", "Small")
        self.size_chips.add_chip("medium", "Medium")
        self.size_chips.add_chip("large", "Large")
        self.size_chips.select("medium")
        body_lay.addWidget(self.size_chips)

        # Accent colour
        accent_lbl = QLabel("Accent Color")
        accent_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px; background: transparent;")
        body_lay.addWidget(accent_lbl)
        self.accent_swatches = _ColorSwatchRow()
        body_lay.addWidget(self.accent_swatches)

        # Page style
        page_lbl = QLabel("Page Style")
        page_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px; background: transparent;")
        body_lay.addWidget(page_lbl)
        self.page_style_chips = _SingleChipRow()
        self.page_style_chips.add_chip("light", "Light")
        self.page_style_chips.add_chip("dark", "Dark")
        self.page_style_chips.select("light")
        body_lay.addWidget(self.page_style_chips)

        # ── SECTIONS ──
        body_lay.addWidget(_section_header("Sections"))
        self.section_chips = _ChipToggleGroup(columns=2)
        self.section_chips.add_chip("overview",      "Data Overview",         True)
        self.section_chips.add_chip("stats",         "Descriptive Statistics", True)
        self.section_chips.add_chip("quality",       "Data Quality Analysis",  True)
        self.section_chips.add_chip("correlation",   "Correlation Analysis",   True)
        self.section_chips.add_chip("distributions", "Distribution Analysis",  True)
        self.section_chips.add_chip("timeseries",    "Time Series Analysis",   False)
        self.section_chips.add_chip("ml_results",    "ML Results",             False)
        self.section_chips.add_chip("custom_notes",  "Custom Notes",           True)
        body_lay.addWidget(self.section_chips)

        # ── NOTES (conditionally visible) ──
        body_lay.addWidget(_section_header("Notes"))
        self.notes_section = QWidget()
        notes_lay = QVBoxLayout(self.notes_section)
        notes_lay.setContentsMargins(0, 0, 0, 0)
        notes_lay.setSpacing(0)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter any additional notes or observations here...")
        self.notes_edit.setMinimumHeight(100)
        self.notes_edit.setMaximumHeight(180)
        self.notes_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 8px 10px;
            }}
            QTextEdit:focus {{
                border-color: {c['accent']};
            }}
        """)
        notes_lay.addWidget(self.notes_edit)
        body_lay.addWidget(self.notes_section)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        left_outer_lay.addWidget(scroll, 1)

        # ── Footer: Generate Preview + export row ──
        footer = QWidget()
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(14, 6, 14, 10)
        f_lay.setSpacing(8)

        self.preview_btn = QPushButton("Generate Preview")
        self.preview_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.preview_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 8px;
                padding: 0px 16px;
                font-size: 14px;
                font-weight: 600;
                min-height: 44px;
                max-height: 44px;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {c['accent_pressed']};
            }}
        """)
        # Glow effect for stale indicator
        self._glow = QGraphicsDropShadowEffect(self.preview_btn)
        self._glow.setBlurRadius(0)
        self._glow.setColor(QColor(c['accent']))
        self._glow.setOffset(0, 0)
        self.preview_btn.setGraphicsEffect(self._glow)

        # Pass self as parent so Qt retains ownership and prevents GC
        self._glow_anim = QPropertyAnimation(self._glow, b"blurRadius", self)
        self._glow_anim.setDuration(1200)
        self._glow_anim.setStartValue(0)
        self._glow_anim.setEndValue(22)
        self._glow_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._glow_anim.setLoopCount(-1)  # loop forever
        # Reverse each cycle so it pulses in and out
        self._glow_anim.finished.connect(self._on_glow_finished)

        f_lay.addWidget(self.preview_btn)

        export_row = QHBoxLayout()
        export_row.setSpacing(8)

        self.export_pdf_btn = QPushButton("Export as PDF")
        self.export_pdf_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_pdf_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.export_pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['text_primary']};
                border: 1px solid {c['border_medium']};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 500;
                min-height: 36px;
                max-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                border-color: {c['accent']};
                color: {c['accent']};
            }}
        """)
        export_row.addWidget(self.export_pdf_btn)

        self.export_html_btn = QPushButton("Export as HTML")
        self.export_html_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_html_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.export_html_btn.setStyleSheet(self.export_pdf_btn.styleSheet())
        export_row.addWidget(self.export_html_btn)

        f_lay.addLayout(export_row)
        left_outer_lay.addWidget(footer)

        root.addWidget(left_outer)

        # Thin vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {c['border']}; max-width: 1px;")
        root.addWidget(sep)

        # ─── RIGHT PANEL (preview) ────────────────────────────────────────
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setFrameShape(QFrame.NoFrame)
        self.preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.preview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.preview_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {c['bg_base']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: #0f1117;
                width: 10px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #4b5563;
                border-radius: 4px;
                border: 2px solid #0f1117;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #6366f1;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: #0f1117;
            }}
            QScrollBar:horizontal {{
                background: #0f1117;
                height: 10px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: #4b5563;
                border-radius: 4px;
                border: 2px solid #0f1117;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #6366f1;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: #0f1117;
            }}
            QScrollBar::corner {{
                background: #0f1117;
            }}
        """)

        # Inner container that centres the page card
        self._preview_container = QWidget()
        self._preview_container.setStyleSheet(f"background-color: {c['bg_base']};")
        pc_lay = QVBoxLayout(self._preview_container)
        pc_lay.setContentsMargins(20, 24, 20, 24)
        pc_lay.setSpacing(0)
        pc_lay.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        # The actual HTML preview widget
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(False)   # allow inline editing
        self.preview_edit.setMinimumHeight(1050)
        self.preview_edit.setMaximumWidth(900)
        self.preview_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: #ffffff;
                color: #1e293b;
                border: none;
                border-radius: 4px;
                padding: 32px 40px;
                selection-background-color: {c['accent']};
                selection-color: {c['text_inverse']};
            }}
        """)

        # Placeholder when nothing generated yet
        self.preview_edit.setPlaceholderText(
            "Click \"Generate Preview\" to render your report here."
        )

        # Drop shadow on the page card
        shadow = QGraphicsDropShadowEffect(self.preview_edit)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 102))
        shadow.setOffset(0, 4)
        self.preview_edit.setGraphicsEffect(shadow)

        pc_lay.addWidget(self.preview_edit)
        pc_lay.addStretch()

        self.preview_scroll.setWidget(self._preview_container)
        right_lay.addWidget(self.preview_scroll)

        root.addWidget(right, 1)

    # ── Signal Connections ─────────────────────────────────────────────────

    def setup_connections(self):
        self.preview_btn.clicked.connect(self.generate_preview)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_html_btn.clicked.connect(self.export_html)

        # Content changes mark stale (need full re-generation)
        self.title_edit.textChanged.connect(self._mark_stale)
        self.notes_edit.textChanged.connect(self._mark_stale)
        self.section_chips.changed.connect(self._mark_stale)
        self.section_chips.changed.connect(self._update_notes_visibility)

        # Style changes apply live to the preview (no re-generation needed)
        self.font_chips.changed.connect(self._on_style_changed)
        self.size_chips.changed.connect(self._on_style_changed)
        self.accent_swatches.changed.connect(self._on_style_changed)
        self.page_style_chips.changed.connect(self._on_style_changed)

    def _on_glow_finished(self):
        """Safe callback for glow animation finish — guarded against GC."""
        if (self._glow_anim is not None
                and not sip.isdeleted(self._glow_anim)
                and self._preview_stale):
            self._glow_anim.start()

    def _mark_stale(self, *_args):
        if not self._preview_stale:
            self._preview_stale = True
            self._start_glow()

    def _start_glow(self):
        if (self._glow_anim is not None
                and not sip.isdeleted(self._glow_anim)
                and self._glow_anim.state() != QAbstractAnimation.Running):
            self._glow_anim.setDirection(QPropertyAnimation.Forward)
            self._glow_anim.setLoopCount(-1)
            self._glow_anim.start()

    def _stop_glow(self):
        self._preview_stale = False
        if self._glow_anim is not None and not sip.isdeleted(self._glow_anim):
            self._glow_anim.stop()
        if self._glow is not None and not sip.isdeleted(self._glow):
            self._glow.setBlurRadius(0)

    def _update_notes_visibility(self):
        self.notes_section.setVisible(self.section_chips.is_checked("custom_notes"))

    def _on_style_changed(self, *_args):
        """Handle style control changes — live-update preview if report exists."""
        self._apply_preview_card_style()
        if self._last_report_data is not None:
            self._render_from_data()

    def _apply_preview_card_style(self):
        c = _colors()
        is_dark = self.page_style_chips.selected() == "dark"
        bg = "#1e2433" if is_dark else "#ffffff"
        fg = "#e2e8f0" if is_dark else "#1e293b"
        self.preview_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-radius: 4px;
                padding: 32px 40px;
                selection-background-color: {c['accent']};
                selection-color: {c['text_inverse']};
            }}
        """)

    # ── Style token helpers ────────────────────────────────────────────────

    def _get_font_family(self):
        sel = self.font_chips.selected()
        if sel == "serif":
            return "Georgia, 'Times New Roman', Times, serif"
        elif sel == "mono":
            return "'Courier New', Courier, monospace"
        return "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

    def _get_font_size(self):
        sel = self.size_chips.selected()
        if sel == "small":
            return "11px"
        elif sel == "large":
            return "15px"
        return "13px"

    def _get_style_tokens(self):
        """Build a dict of CSS tokens injected into the Jinja template."""
        accent = self.accent_swatches.selected_color()
        is_dark = self.page_style_chips.selected() == "dark"

        if is_dark:
            return {
                "font_family":  self._get_font_family(),
                "font_size":    self._get_font_size(),
                "accent_color": accent,
                "page_bg":      "#1e2433",
                "text_color":   "#e2e8f0",
                "heading_color": "#f1f5f9",
                "muted_color":  "#94a3b8",
                "sublabel_color": "#94a3b8",
                "value_color":  "#f1f5f9",
                "metric_bg":    "#252b3b",
                "border_color": "rgba(255,255,255,0.10)",
                "table_border": "rgba(255,255,255,0.08)",
                "table_alt":    "#252b3b",
                "table_row":    "#1e2433",
                "watermark_border": "rgba(255,255,255,0.08)",
            }
        else:
            return {
                "font_family":  self._get_font_family(),
                "font_size":    self._get_font_size(),
                "accent_color": accent,
                "page_bg":      "#ffffff",
                "text_color":   "#1e293b",
                "heading_color": "#0f172a",
                "muted_color":  "#64748b",
                "sublabel_color": "#475569",
                "value_color":  "#0f172a",
                "metric_bg":    "#f8fafc",
                "border_color": "#e2e8f0",
                "table_border": "#e2e8f0",
                "table_alt":    "#f8fafc",
                "table_row":    "#ffffff",
                "watermark_border": "#e2e8f0",
            }

    # ══════════════════════════════════════════════════════════════════════
    #  Backend data generators — UNCHANGED
    # ══════════════════════════════════════════════════════════════════════

    def generate_data_overview(self):
        """Generate data overview section."""
        df = self.data_manager.data
        if df is None:
            return ""
        overview = {
            "num_rows": len(df),
            "num_cols": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum() / 1024**2,
            "column_types": df.dtypes.value_counts().to_dict(),
            "columns": df.columns.tolist()
        }
        return overview

    def generate_descriptive_stats(self):
        """Generate descriptive statistics section."""
        df = self.data_manager.data
        if df is None:
            return ""
        numeric_stats = df.describe().round(2).to_html()
        categorical_stats = df.select_dtypes(include=['object']).describe().to_html()
        return {
            "numeric_stats": numeric_stats,
            "categorical_stats": categorical_stats
        }

    def generate_data_quality(self):
        """Generate data quality analysis section."""
        df = self.data_manager.data
        if df is None:
            return ""
        quality = {
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            "duplicates": len(df) - len(df.drop_duplicates()),
            "unique_values": {col: df[col].nunique() for col in df.columns}
        }
        return quality

    def generate_correlation_analysis(self):
        """Generate correlation analysis section."""
        df = self.data_manager.data
        if df is None:
            return ""
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr().round(2)
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
            ax.set_title('Correlation Heatmap')
            apply_dark_theme(fig, ax)
            fig.tight_layout()
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            tmp.close()
            fig.savefig(tmp.name, facecolor=fig.get_facecolor())
            plt.close(fig)
            self._temp_files.append(tmp.name)
            return {
                "correlation_matrix": corr_matrix.to_html(),
                "heatmap_path": tmp.name
            }
        return None

    def generate_distribution_analysis(self):
        """Generate distribution analysis section."""
        df = self.data_manager.data
        if df is None:
            return ""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        distributions = {}
        for col in numeric_cols[:5]:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(data=df, x=col, kde=True, ax=ax)
            ax.set_title(f'Distribution of {col}')
            apply_dark_theme(fig, ax)
            fig.tight_layout()
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            tmp.close()
            fig.savefig(tmp.name, facecolor=fig.get_facecolor())
            plt.close(fig)
            self._temp_files.append(tmp.name)
            distributions[col] = tmp.name
        return distributions

    def generate_time_series_analysis(self):
        """Generate time series analysis section if applicable."""
        df = self.data_manager.data
        if df is None:
            return ""
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            time_series_plots = {}
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:3]
            for dt_col in datetime_cols[:1]:
                for num_col in numeric_cols:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.plot(df[dt_col], df[num_col])
                    ax.set_title(f'{num_col} over Time')
                    ax.tick_params(axis='x', rotation=45)
                    apply_dark_theme(fig, ax)
                    fig.tight_layout()
                    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    tmp.close()
                    fig.savefig(tmp.name, facecolor=fig.get_facecolor())
                    plt.close(fig)
                    self._temp_files.append(tmp.name)
                    time_series_plots[num_col] = tmp.name
            return time_series_plots
        return None

    def generate_ml_results(self):
        """Generate machine learning results section if available."""
        return None

    # ══════════════════════════════════════════════════════════════════════
    #  Preview generation
    # ══════════════════════════════════════════════════════════════════════

    def _render_from_data(self):
        """Re-render the template using stored report data and current style tokens."""
        if self._last_report_data is None:
            return
        try:
            render_data = dict(self._last_report_data)
            render_data.update(self._get_style_tokens())
            template = self.template_env.get_template("report_template.html")
            html_content = template.render(**render_data)
            self._last_html = html_content
            self.preview_edit.setHtml(html_content)
            self._apply_preview_card_style()
        except Exception:
            pass  # silently ignore render errors during live updates

    def generate_preview(self):
        """Generate report preview."""
        if self.data_manager.data is None:
            modal.show_warning(self, "Warning", "No data loaded.")
            return

        self.cleanup_temp_files()

        try:
            report_data = {
                "title": self.title_edit.text(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "custom_notes": self.notes_edit.toPlainText()
                                if self.section_chips.is_checked("custom_notes") else "",
            }

            if self.section_chips.is_checked("overview"):
                report_data["overview"] = self.generate_data_overview()
            if self.section_chips.is_checked("stats"):
                report_data["stats"] = self.generate_descriptive_stats()
            if self.section_chips.is_checked("quality"):
                report_data["quality"] = self.generate_data_quality()
            if self.section_chips.is_checked("correlation"):
                report_data["correlation"] = self.generate_correlation_analysis()
            if self.section_chips.is_checked("distributions"):
                report_data["distributions"] = self.generate_distribution_analysis()
            if self.section_chips.is_checked("timeseries"):
                report_data["timeseries"] = self.generate_time_series_analysis()
            if self.section_chips.is_checked("ml_results"):
                report_data["ml_results"] = self.generate_ml_results()

            # Store report data (without style tokens) for live style updates
            self._last_report_data = dict(report_data)

            # Inject style tokens
            report_data.update(self._get_style_tokens())

            template = self.template_env.get_template("report_template.html")
            html_content = template.render(**report_data)

            self._last_html = html_content
            self.preview_edit.setHtml(html_content)
            self._apply_preview_card_style()
            self._stop_glow()

        except Exception as e:
            modal.show_error(self, "Error", f"Error generating preview: {str(e)}")

    # ══════════════════════════════════════════════════════════════════════
    #  Export — logic UNCHANGED (only wiring updated)
    # ══════════════════════════════════════════════════════════════════════

    def _get_export_html(self):
        """Get the current preview HTML for export (preserves edits)."""
        return self.preview_edit.toHtml()

    def export_pdf(self):
        """Export report as PDF."""
        try:
            default_dir = ""
            if self.workspace_path:
                default_dir = os.path.join(self.workspace_path, "reports", "report.pdf")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save PDF Report", default_dir, "PDF Files (*.pdf)")
            if file_path:
                if not WEASYPRINT_AVAILABLE:
                    modal.show_warning(
                        self, "Feature Not Available",
                        "PDF export requires WeasyPrint which is not available on this system.\n\n"
                        "Please use 'Export as HTML' instead, or install WeasyPrint with:\n"
                        "pip install weasyprint\n\n"
                        "Note: WeasyPrint requires additional system libraries on Windows."
                    )
                    return
                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'
                html_content = self._get_export_html()
                temp_html = 'temp_report.html'
                with open(temp_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                HTML(temp_html).write_pdf(file_path)
                os.remove(temp_html)
                modal.show_info(self, "Success",
                                f"Report exported successfully to {file_path}")
        except Exception as e:
            modal.show_error(self, "Error", f"Error exporting PDF: {str(e)}")

    def export_html(self):
        """Export report as HTML."""
        try:
            default_dir = ""
            if self.workspace_path:
                default_dir = os.path.join(self.workspace_path, "reports", "report.html")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save HTML Report", default_dir, "HTML Files (*.html)")
            if file_path:
                if not file_path.endswith('.html'):
                    file_path += '.html'
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._get_export_html())
                modal.show_info(self, "Success",
                                f"Report exported successfully to {file_path}")
        except Exception as e:
            modal.show_error(self, "Error", f"Error exporting HTML: {str(e)}")

    # ── Housekeeping ───────────────────────────────────────────────────────

    def cleanup_temp_files(self):
        """Remove all tracked temporary files."""
        for path in self._temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        self._temp_files.clear()

    def set_workspace_path(self, workspace_path):
        """Set the active workspace path."""
        self.workspace_path = workspace_path
