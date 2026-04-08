"""
Feature engineering panel for creating and modifying dataset features.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QComboBox, QPushButton, QSpinBox,
    QGridLayout, QTabWidget, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem,
    QGroupBox, QScrollArea, QDoubleSpinBox, QSizePolicy,
    QToolTip
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QCursor
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from datetime import datetime

from ui.theme import get_colors, current_theme
from ui.components import modal


# ── Shared styling helpers ─────────────────────────────────────────────────

def _colors():
    """Get current theme colors."""
    return get_colors(current_theme())


def _section_header(text):
    """Create a compact section header: ALL-CAPS accent label + divider."""
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
    """Consistent input field style."""
    c = _colors()
    return f"""
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {c['bg_input']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 22px;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border-color: {c['accent']};
        }}
    """


def _chip_style(selected=False):
    """Style for a selectable chip/pill button."""
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
                min-height: 0px;
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
                min-height: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
                border-color: {c['accent']};
            }}
        """


def _toggle_chip_style(on=False):
    """Style for a togglable chip (on/off)."""
    return _chip_style(selected=on)


def _card_style(selected=False):
    """Style for an operation card button."""
    c = _colors()
    if selected:
        return f"""
            QPushButton {{
                background-color: {c['accent_subtle']};
                color: {c['text_primary']};
                border: 1.5px solid {c['accent']};
                border-radius: 8px;
                padding: 8px 4px;
                font-size: 12px;
                min-height: 0px;
                text-align: center;
            }}
        """
    else:
        return f"""
            QPushButton {{
                background-color: {c['bg_tertiary']};
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 8px 4px;
                font-size: 12px;
                min-height: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
                border-color: {c['accent_glow']};
            }}
        """


def _footer_btn_style():
    """Full-width accent action button style for panel footers."""
    c = _colors()
    return f"""
        QPushButton {{
            background-color: {c['accent']};
            color: {c['text_inverse']};
            border: none;
            border-radius: 8px;
            padding: 0px 16px;
            font-size: 13px;
            font-weight: 600;
            min-height: 40px;
            max-height: 40px;
        }}
        QPushButton:hover {{
            background-color: {c['accent_hover']};
        }}
        QPushButton:pressed {{
            background-color: {c['accent_pressed']};
        }}
    """


def _scroll_wrap(widget):
    """Wrap a widget in a QScrollArea."""
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    return scroll


# ── Chip selector widget ──────────────────────────────────────────────────

class ChipSelector(QWidget):
    """A flow-layout grid of selectable chip buttons."""

    selection_changed = pyqtSignal()

    def __init__(self, multi_select=False, columns=4, parent=None):
        super().__init__(parent)
        self.multi_select = multi_select
        self._columns = columns
        self._chips = {}  # name -> QPushButton
        self._selected = set()
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def set_items(self, items):
        """Replace all chips with new item list."""
        # Clear existing
        for btn in self._chips.values():
            btn.deleteLater()
        self._chips.clear()
        self._selected.clear()

        for i, name in enumerate(items):
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(_chip_style(False))
            btn.clicked.connect(lambda checked, n=name: self._on_chip_clicked(n))
            row, col = divmod(i, self._columns)
            self._layout.addWidget(btn, row, col)
            self._chips[name] = btn

        self.selection_changed.emit()

    def _on_chip_clicked(self, name):
        if self.multi_select:
            if name in self._selected:
                self._selected.discard(name)
            else:
                self._selected.add(name)
        else:
            self._selected = {name}

        # Update styles
        for n, btn in self._chips.items():
            btn.setStyleSheet(_chip_style(n in self._selected))

        self.selection_changed.emit()

    def selected(self):
        """Return list of selected item names."""
        return list(self._selected)

    def selected_one(self):
        """Return single selected item or empty string."""
        return list(self._selected)[0] if self._selected else ""

    def count(self):
        return len(self._selected)

    def clear_selection(self):
        self._selected.clear()
        for btn in self._chips.values():
            btn.setStyleSheet(_chip_style(False))
        self.selection_changed.emit()

    def refresh_styles(self):
        for n, btn in self._chips.items():
            btn.setStyleSheet(_chip_style(n in self._selected))


# ── Toggle chip selector (for datetime features etc.) ─────────────────────

class ToggleChipSelector(QWidget):
    """A grid of toggle-able chips (multi-select, accent fill when ON)."""

    def __init__(self, columns=4, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._chips = {}  # key -> (QPushButton, bool)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def add_chip(self, key, label):
        btn = QPushButton(label)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(_toggle_chip_style(False))
        btn.clicked.connect(lambda: self._toggle(key))
        idx = len(self._chips)
        row, col = divmod(idx, self._columns)
        self._layout.addWidget(btn, row, col)
        self._chips[key] = (btn, False)

    def _toggle(self, key):
        btn, state = self._chips[key]
        state = not state
        self._chips[key] = (btn, state)
        btn.setStyleSheet(_toggle_chip_style(state))

    def is_checked(self, key):
        if key in self._chips:
            return self._chips[key][1]
        return False

    def set_checked(self, key, checked):
        if key in self._chips:
            btn, _ = self._chips[key]
            self._chips[key] = (btn, checked)
            btn.setStyleSheet(_toggle_chip_style(checked))

    def refresh_styles(self):
        for key, (btn, state) in self._chips.items():
            btn.setStyleSheet(_toggle_chip_style(state))


# ── Card selector (for operations / methods) ──────────────────────────────

class CardSelector(QWidget):
    """A grid of selectable operation/method cards."""

    selection_changed = pyqtSignal(str)

    def __init__(self, columns=3, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._cards = {}  # key -> QPushButton
        self._selected = ""
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def add_card(self, key, symbol, label):
        btn = QPushButton(f"{symbol}  {label}")
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(_card_style(False))
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.clicked.connect(lambda: self._on_clicked(key))
        idx = len(self._cards)
        row, col = divmod(idx, self._columns)
        self._layout.addWidget(btn, row, col)
        self._cards[key] = btn

    def _on_clicked(self, key):
        self._selected = key
        for k, btn in self._cards.items():
            btn.setStyleSheet(_card_style(k == key))
        self.selection_changed.emit(key)

    def selected(self):
        return self._selected

    def select(self, key):
        """Programmatically select a card."""
        self._on_clicked(key)

    def refresh_styles(self):
        for k, btn in self._cards.items():
            btn.setStyleSheet(_card_style(k == self._selected))


# ── Encoding method card (wider, with description + tooltip) ──────────────

class EncodingCardSelector(QWidget):
    """Horizontal card row for encoding methods with descriptions."""

    selection_changed = pyqtSignal(str)

    DESCRIPTIONS = {
        "Label Encoding": "Integer rank per category",
        "One-Hot Encoding": "Binary column per category",
        "Binary Encoding": "Binary-coded columns",
        "Frequency Encoding": "Replace with frequency %",
        "Target Encoding": "Replace with target mean",
    }

    TOOLTIPS = {
        "Label Encoding": "Assigns integer ranks (0, 1, 2 ...) to each unique category. Order is alphabetical.",
        "One-Hot Encoding": "Creates a new binary (0/1) column for each unique category value.",
        "Binary Encoding": "Encodes categories as binary digits, using fewer columns than one-hot.",
        "Frequency Encoding": "Replaces each category with its relative frequency in the dataset.",
        "Target Encoding": "Replaces each category with the mean of the target variable for that category.",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = {}
        self._selected = ""
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def add_card(self, key):
        c = _colors()
        btn = QPushButton()
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setToolTip(self.TOOLTIPS.get(key, ""))
        # Two-line text: name + description
        desc = self.DESCRIPTIONS.get(key, "")
        btn.setText(f"{key}\n{desc}")
        btn.setStyleSheet(_card_style(False) + "QPushButton { text-align: center; }")
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setMinimumHeight(48)
        btn.clicked.connect(lambda: self._on_clicked(key))
        idx = len(self._cards)
        row, col = divmod(idx, 3)
        self._layout.addWidget(btn, row, col)
        self._cards[key] = btn

    def _on_clicked(self, key):
        self._selected = key
        for k, btn in self._cards.items():
            btn.setStyleSheet(_card_style(k == key) + "QPushButton { text-align: center; }")
        self.selection_changed.emit(key)

    def selected(self):
        return self._selected

    def refresh_styles(self):
        for k, btn in self._cards.items():
            btn.setStyleSheet(_card_style(k == self._selected) + "QPushButton { text-align: center; }")


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN PANEL
# ═══════════════════════════════════════════════════════════════════════════

class FeatureEngineeringPanel(QWidget):
    """Panel for feature engineering operations."""

    feature_created = pyqtSignal()
    data_modified = pyqtSignal()

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.label_encoders = {}
        self.init_ui()
        self.setup_connections()

    # ── UI Construction ────────────────────────────────────────────────────

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.addTab(self._build_numeric_tab(), "Numeric Features")
        tabs.addTab(self._build_categorical_tab(), "Categorical Features")
        tabs.addTab(self._build_datetime_tab(), "DateTime Features")
        tabs.addTab(self._build_combination_tab(), "Feature Combinations")
        layout.addWidget(tabs)

    def update_theme(self, theme_name=None):
        """Re-apply inline styles for the current theme."""
        c = _colors()

        # Refresh all chip/card selector widgets
        for selector in (self.numeric_chip_selector, self.second_chip_selector,
                         self.cat_chip_selector, self.dt_chip_selector,
                         self.combine_chip_selector):
            selector.refresh_styles()

        self.numeric_ops_cards.refresh_styles()
        self.combine_method_cards.refresh_styles()
        self.encoding_cards.refresh_styles()
        self.dt_toggle_chips.refresh_styles()

        # Poly degree chips
        self._poly_deg2.setStyleSheet(_chip_style(self._poly_degree == 2))
        self._poly_deg3.setStyleSheet(_chip_style(self._poly_degree == 3))

        # Footer buttons
        for btn in (self.apply_numeric_btn, self.apply_cat_btn,
                    self.apply_dt_btn, self.apply_combine_btn):
            btn.setStyleSheet(_footer_btn_style())

        # Input fields
        for inp in (self.power_spin, self.bins_spin, self.numeric_name_edit,
                    self.rare_threshold_spin, self.target_col_combo,
                    self.concat_separator_edit, self.combine_name_edit):
            inp.setStyleSheet(_input_style())

        # Labels with inline styles
        self._cat_preview_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_secondary']};
                font-size: 11px;
                padding: 4px 8px;
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
            }}
        """)

        self._dt_empty_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_disabled']};
                font-size: 13px;
                padding: 30px;
                background: transparent;
            }}
        """)

        self._combine_count_label.setStyleSheet(f"""
            QLabel {{
                color: {c['accent']};
                font-size: 11px;
                font-weight: 600;
                padding: 0;
                background: transparent;
            }}
        """)

        self._combine_preview_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_secondary']};
                font-size: 11px;
                padding: 8px;
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                font-family: monospace;
            }}
        """)

        self._ratio_warning.setStyleSheet(f"color: {c['warning']}; font-size: 11px; padding: 0; background: transparent;")

    # ── TAB 1: Numeric Features ────────────────────────────────────────────

    def _build_numeric_tab(self):
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        # — Base Column chip selector
        body_lay.addWidget(_section_header("Base Column"))
        self.numeric_chip_selector = ChipSelector(multi_select=False, columns=4)
        body_lay.addWidget(self.numeric_chip_selector)

        # — Second Column chip selector (for binary ops)
        body_lay.addWidget(_section_header("Second Column (for ratio / arithmetic ops)"))
        self.second_chip_selector = ChipSelector(multi_select=False, columns=4)
        self.second_chip_section = body_lay.count() - 1  # track position
        body_lay.addWidget(self.second_chip_selector)
        self._second_col_header = body_lay.itemAt(body_lay.count() - 2).widget()
        # Start hidden
        self._second_col_header.setVisible(False)
        self.second_chip_selector.setVisible(False)

        # — Operation card grid
        body_lay.addWidget(_section_header("Operation"))
        self.numeric_ops_cards = CardSelector(columns=3)
        ops = [
            ("square", "x²", "Square"),
            ("power", "xⁿ", "Power"),
            ("sqrt", "√x", "Sqrt"),
            ("log", "ln", "Log"),
            ("abs", "|x|", "Abs"),
            ("ratio", "÷", "Ratio"),
            ("add", "+", "Add"),
            ("subtract", "−", "Subtract"),
            ("multiply", "×", "Multiply"),
            ("bin", "≡", "Bin"),
            ("normalize", "±", "Normalize"),
            ("zscore", "z", "Z-Score"),
        ]
        for key, sym, label in ops:
            self.numeric_ops_cards.add_card(key, sym, label)
        body_lay.addWidget(self.numeric_ops_cards)

        # — Sub-options (shown contextually)
        sub_opts = QWidget()
        sub_lay = QHBoxLayout(sub_opts)
        sub_lay.setContentsMargins(0, 0, 0, 0)
        sub_lay.setSpacing(10)

        # Power value
        self._power_widget = QWidget()
        pw_lay = QVBoxLayout(self._power_widget)
        pw_lay.setContentsMargins(0, 0, 0, 0)
        pw_lay.setSpacing(2)
        pw_lay.addWidget(QLabel("Power Value"))
        self.power_spin = QDoubleSpinBox()
        self.power_spin.setRange(-10, 10)
        self.power_spin.setValue(2)
        self.power_spin.setStyleSheet(_input_style())
        pw_lay.addWidget(self.power_spin)
        self._power_widget.setVisible(False)
        sub_lay.addWidget(self._power_widget)

        # Bins value
        self._bins_widget = QWidget()
        bn_lay = QVBoxLayout(self._bins_widget)
        bn_lay.setContentsMargins(0, 0, 0, 0)
        bn_lay.setSpacing(2)
        bn_lay.addWidget(QLabel("Number of Bins"))
        self.bins_spin = QSpinBox()
        self.bins_spin.setRange(2, 100)
        self.bins_spin.setValue(5)
        self.bins_spin.setStyleSheet(_input_style())
        bn_lay.addWidget(self.bins_spin)
        self._bins_widget.setVisible(False)
        sub_lay.addWidget(self._bins_widget)

        sub_lay.addStretch()
        body_lay.addWidget(sub_opts)

        # — New column name
        body_lay.addWidget(_section_header("New Column Name"))
        self.numeric_name_edit = QLineEdit()
        self.numeric_name_edit.setPlaceholderText("e.g. ApplicantIncome_log")
        self.numeric_name_edit.setStyleSheet(_input_style())
        body_lay.addWidget(self.numeric_name_edit)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        outer_lay.addWidget(scroll, 1)

        # — Footer button
        footer = QWidget()
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(14, 6, 14, 10)
        self.apply_numeric_btn = QPushButton("Create Feature")
        self.apply_numeric_btn.setStyleSheet(_footer_btn_style())
        f_lay.addWidget(self.apply_numeric_btn)
        outer_lay.addWidget(footer)

        return outer

    # ── TAB 2: Categorical Features ────────────────────────────────────────

    def _build_categorical_tab(self):
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        # — Column selector chips
        body_lay.addWidget(_section_header("Categorical Column"))
        self.cat_chip_selector = ChipSelector(multi_select=False, columns=4)
        body_lay.addWidget(self.cat_chip_selector)

        # — Category preview (inline)
        self._cat_preview_label = QLabel("")
        c = _colors()
        self._cat_preview_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_secondary']};
                font-size: 11px;
                padding: 4px 8px;
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
            }}
        """)
        self._cat_preview_label.setWordWrap(True)
        self._cat_preview_label.setVisible(False)
        body_lay.addWidget(self._cat_preview_label)

        # — Rare Category Grouping toggle
        body_lay.addWidget(_section_header("Rare Category Grouping"))
        rare_row = QHBoxLayout()
        rare_row.setSpacing(10)
        self.rare_group_check = QCheckBox("Collapse rare categories into 'Other'")
        rare_row.addWidget(self.rare_group_check)
        thresh_lbl = QLabel("Threshold %:")
        self.rare_threshold_spin = QDoubleSpinBox()
        self.rare_threshold_spin.setRange(0.1, 50.0)
        self.rare_threshold_spin.setValue(5.0)
        self.rare_threshold_spin.setSingleStep(0.5)
        self.rare_threshold_spin.setStyleSheet(_input_style())
        self.rare_threshold_spin.setFixedWidth(80)
        self.rare_threshold_spin.setEnabled(False)
        rare_row.addWidget(thresh_lbl)
        rare_row.addWidget(self.rare_threshold_spin)
        rare_row.addStretch()
        rare_w = QWidget()
        rare_w.setLayout(rare_row)
        body_lay.addWidget(rare_w)

        # — Encoding method cards
        body_lay.addWidget(_section_header("Encoding Method"))
        self.encoding_cards = EncodingCardSelector()
        for method in ["Label Encoding", "One-Hot Encoding", "Binary Encoding",
                        "Frequency Encoding", "Target Encoding"]:
            self.encoding_cards.add_card(method)
        body_lay.addWidget(self.encoding_cards)

        # — Target column (only for Target Encoding)
        self._target_col_widget = QWidget()
        tc_lay = QVBoxLayout(self._target_col_widget)
        tc_lay.setContentsMargins(0, 0, 0, 0)
        tc_lay.setSpacing(2)
        tc_lay.addWidget(QLabel("Target Column"))
        self.target_col_combo = QComboBox()
        self.target_col_combo.setStyleSheet(_input_style())
        tc_lay.addWidget(self.target_col_combo)
        self._target_col_widget.setVisible(False)
        body_lay.addWidget(self._target_col_widget)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        outer_lay.addWidget(scroll, 1)

        # — Footer
        footer = QWidget()
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(14, 6, 14, 10)
        self.apply_cat_btn = QPushButton("Apply Encoding")
        self.apply_cat_btn.setStyleSheet(_footer_btn_style())
        f_lay.addWidget(self.apply_cat_btn)
        outer_lay.addWidget(footer)

        return outer

    # ── TAB 3: DateTime Features ───────────────────────────────────────────

    def _build_datetime_tab(self):
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        # — Column selector chips
        body_lay.addWidget(_section_header("DateTime Column"))
        self.dt_chip_selector = ChipSelector(multi_select=False, columns=4)
        body_lay.addWidget(self.dt_chip_selector)

        # — Empty state
        c = _colors()
        self._dt_empty_label = QLabel("No DateTime columns detected.\nConvert a column in Preprocessing first.")
        self._dt_empty_label.setAlignment(Qt.AlignCenter)
        self._dt_empty_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_disabled']};
                font-size: 13px;
                padding: 30px;
                background: transparent;
            }}
        """)
        self._dt_empty_label.setVisible(False)
        body_lay.addWidget(self._dt_empty_label)

        # — Feature toggle chips
        body_lay.addWidget(_section_header("Extract Features"))
        self.dt_toggle_chips = ToggleChipSelector(columns=4)
        for key, label in [
            ("year", "Year"), ("month", "Month"), ("day", "Day"),
            ("weekday", "Day of Week"), ("hour", "Hour"), ("minute", "Minute"),
            ("quarter", "Quarter"), ("is_weekend", "Is Weekend"),
            ("is_month_start", "Is Month Start"), ("is_month_end", "Is Month End"),
            ("season", "Season"), ("days_since_min", "Days Since Min"),
            ("cyclical_month", "Cyclical Month"), ("cyclical_dow", "Cyclical DoW"),
        ]:
            self.dt_toggle_chips.add_chip(key, label)
        body_lay.addWidget(self.dt_toggle_chips)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        outer_lay.addWidget(scroll, 1)

        # — Footer
        footer = QWidget()
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(14, 6, 14, 10)
        self.apply_dt_btn = QPushButton("Extract Features")
        self.apply_dt_btn.setStyleSheet(_footer_btn_style())
        f_lay.addWidget(self.apply_dt_btn)
        outer_lay.addWidget(footer)

        return outer

    # ── TAB 4: Feature Combinations ────────────────────────────────────────

    def _build_combination_tab(self):
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        # — Column multi-selector chips
        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(0, 0, 0, 0)
        hdr_w = _section_header("Select Columns")
        hdr_row.addWidget(hdr_w)
        self._combine_count_label = QLabel("0 selected")
        c = _colors()
        self._combine_count_label.setStyleSheet(f"""
            QLabel {{
                color: {c['accent']};
                font-size: 11px;
                font-weight: 600;
                padding: 0;
                background: transparent;
            }}
        """)
        hdr_row.addWidget(self._combine_count_label, 0, Qt.AlignRight | Qt.AlignBottom)
        hdr_container = QWidget()
        hdr_container.setLayout(hdr_row)
        body_lay.addWidget(hdr_container)

        self.combine_chip_selector = ChipSelector(multi_select=True, columns=4)
        body_lay.addWidget(self.combine_chip_selector)

        # — Combination method cards
        body_lay.addWidget(_section_header("Combination Method"))
        self.combine_method_cards = CardSelector(columns=3)
        for key, sym, label in [
            ("sum", "Σ", "Sum"), ("mean", "x̄", "Mean"), ("product", "×", "Product"),
            ("ratio", "÷", "Ratio"), ("poly", "x²", "Poly"), ("concat", "‖", "Concat"),
        ]:
            self.combine_method_cards.add_card(key, sym, label)
        body_lay.addWidget(self.combine_method_cards)

        # — Sub-options
        sub_opts = QWidget()
        sub_lay = QHBoxLayout(sub_opts)
        sub_lay.setContentsMargins(0, 0, 0, 0)
        sub_lay.setSpacing(10)

        # Polynomial degree
        self._poly_widget = QWidget()
        pl_lay = QHBoxLayout(self._poly_widget)
        pl_lay.setContentsMargins(0, 0, 0, 0)
        pl_lay.setSpacing(6)
        pl_lay.addWidget(QLabel("Degree:"))
        self._poly_deg2 = QPushButton("2")
        self._poly_deg3 = QPushButton("3")
        for btn in (self._poly_deg2, self._poly_deg3):
            btn.setFixedSize(36, 28)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._poly_degree = 2
        self._poly_deg2.setStyleSheet(_chip_style(True))
        self._poly_deg3.setStyleSheet(_chip_style(False))
        self._poly_deg2.clicked.connect(lambda: self._set_poly_degree(2))
        self._poly_deg3.clicked.connect(lambda: self._set_poly_degree(3))
        pl_lay.addWidget(self._poly_deg2)
        pl_lay.addWidget(self._poly_deg3)
        pl_lay.addStretch()
        self._poly_widget.setVisible(False)
        sub_lay.addWidget(self._poly_widget)

        # Concat separator
        self._concat_widget = QWidget()
        cc_lay = QHBoxLayout(self._concat_widget)
        cc_lay.setContentsMargins(0, 0, 0, 0)
        cc_lay.setSpacing(6)
        cc_lay.addWidget(QLabel("Separator:"))
        self.concat_separator_edit = QLineEdit("_")
        self.concat_separator_edit.setFixedWidth(60)
        self.concat_separator_edit.setStyleSheet(_input_style())
        cc_lay.addWidget(self.concat_separator_edit)
        cc_lay.addStretch()
        self._concat_widget.setVisible(False)
        sub_lay.addWidget(self._concat_widget)

        # Ratio warning
        self._ratio_warning = QLabel("")
        self._ratio_warning.setStyleSheet(f"color: {c['warning']}; font-size: 11px; padding: 0; background: transparent;")
        self._ratio_warning.setVisible(False)
        sub_lay.addWidget(self._ratio_warning)

        sub_lay.addStretch()
        body_lay.addWidget(sub_opts)

        # — Preview panel
        body_lay.addWidget(_section_header("Preview (first 5 rows)"))
        self._combine_preview_label = QLabel("Select columns and method to see preview")
        self._combine_preview_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_secondary']};
                font-size: 11px;
                padding: 8px;
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                font-family: monospace;
            }}
        """)
        self._combine_preview_label.setWordWrap(True)
        self._combine_preview_label.setMinimumHeight(60)
        body_lay.addWidget(self._combine_preview_label)

        # — New column name
        body_lay.addWidget(_section_header("New Column Name"))
        self.combine_name_edit = QLineEdit()
        self.combine_name_edit.setPlaceholderText("e.g. income_ratio")
        self.combine_name_edit.setStyleSheet(_input_style())
        body_lay.addWidget(self.combine_name_edit)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        outer_lay.addWidget(scroll, 1)

        # — Footer
        footer = QWidget()
        f_lay = QVBoxLayout(footer)
        f_lay.setContentsMargins(14, 6, 14, 10)
        self.apply_combine_btn = QPushButton("Create Combined Feature")
        self.apply_combine_btn.setStyleSheet(_footer_btn_style())
        f_lay.addWidget(self.apply_combine_btn)
        outer_lay.addWidget(footer)

        return outer

    def _set_poly_degree(self, deg):
        self._poly_degree = deg
        self._poly_deg2.setStyleSheet(_chip_style(deg == 2))
        self._poly_deg3.setStyleSheet(_chip_style(deg == 3))
        self._update_combine_preview()

    # ── Signal Connections ─────────────────────────────────────────────────

    def setup_connections(self):
        self.data_manager.data_loaded.connect(self.on_data_loaded)

        # Numeric tab
        self.numeric_ops_cards.selection_changed.connect(self._on_numeric_op_changed)
        self.apply_numeric_btn.clicked.connect(self.apply_numeric_operation)

        # Categorical tab
        self.cat_chip_selector.selection_changed.connect(self._on_cat_col_changed)
        self.encoding_cards.selection_changed.connect(self._on_encoding_method_changed)
        self.rare_group_check.toggled.connect(self.rare_threshold_spin.setEnabled)
        self.apply_cat_btn.clicked.connect(self.apply_categorical_encoding)

        # DateTime tab
        self.apply_dt_btn.clicked.connect(self.extract_datetime_features)

        # Combination tab
        self.combine_chip_selector.selection_changed.connect(self._on_combine_selection_changed)
        self.combine_method_cards.selection_changed.connect(self._on_combine_method_changed)
        self.apply_combine_btn.clicked.connect(self.create_combined_feature)

    # ── Data Load Handler ──────────────────────────────────────────────────

    def on_data_loaded(self, df):
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_columns = df.select_dtypes(include=['datetime64']).columns.tolist()

        # Numeric tab
        self.numeric_chip_selector.set_items(numeric_columns)
        self.second_chip_selector.set_items(numeric_columns)

        # Categorical tab
        self.cat_chip_selector.set_items(categorical_columns)
        self.target_col_combo.clear()
        self.target_col_combo.addItems(numeric_columns)

        # DateTime tab
        self.dt_chip_selector.set_items(datetime_columns)
        has_dt = len(datetime_columns) > 0
        self.dt_chip_selector.setVisible(has_dt)
        self.dt_toggle_chips.setVisible(has_dt)
        self._dt_empty_label.setVisible(not has_dt)

        # Combination tab
        all_columns = df.columns.tolist()
        self.combine_chip_selector.set_items(all_columns)

    # ── Numeric Tab Logic ──────────────────────────────────────────────────

    def _on_numeric_op_changed(self, op):
        binary_ops = {"ratio", "add", "subtract", "multiply"}
        show_second = op in binary_ops
        self._second_col_header.setVisible(show_second)
        self.second_chip_selector.setVisible(show_second)
        self._power_widget.setVisible(op == "power")
        self._bins_widget.setVisible(op == "bin")

    def apply_numeric_operation(self):
        if self.data_manager.data is None:
            return

        df = self.data_manager.data.copy()
        col = self.numeric_chip_selector.selected_one()
        operation = self.numeric_ops_cards.selected()
        new_name = self.numeric_name_edit.text()

        if not col:
            modal.show_warning(self, "Warning", "Please select a base column.")
            return
        if not operation:
            modal.show_warning(self, "Warning", "Please select an operation.")
            return
        if not new_name:
            modal.show_warning(self, "Warning", "Please specify a name for the new feature.")
            return

        try:
            if operation == "square":
                df[new_name] = df[col] ** 2
            elif operation == "power":
                power = self.power_spin.value()
                df[new_name] = df[col] ** power
            elif operation == "sqrt":
                if (df[col] < 0).any():
                    raise ValueError("Cannot compute square root of negative values")
                df[new_name] = np.sqrt(df[col])
            elif operation == "log":
                # Handle zeros with +1 offset
                df[new_name] = np.log(df[col] + 1)
            elif operation == "abs":
                df[new_name] = df[col].abs()
            elif operation == "bin":
                bins = self.bins_spin.value()
                df[new_name] = pd.qcut(df[col], bins, labels=False, duplicates='drop')
            elif operation == "normalize":
                col_min = df[col].min()
                col_max = df[col].max()
                if col_max == col_min:
                    df[new_name] = 0.0
                else:
                    df[new_name] = (df[col] - col_min) / (col_max - col_min)
            elif operation == "zscore":
                col_mean = df[col].mean()
                col_std = df[col].std()
                if col_std == 0:
                    df[new_name] = 0.0
                else:
                    df[new_name] = (df[col] - col_mean) / col_std
            else:
                # Binary operations requiring second column
                col2 = self.second_chip_selector.selected_one()
                if not col2:
                    modal.show_warning(self, "Warning", "Please select a second column.")
                    return
                if operation == "ratio":
                    if (df[col2] == 0).any():
                        raise ValueError("Division by zero encountered")
                    df[new_name] = df[col] / df[col2]
                elif operation == "add":
                    df[new_name] = df[col] + df[col2]
                elif operation == "subtract":
                    df[new_name] = df[col] - df[col2]
                elif operation == "multiply":
                    df[new_name] = df[col] * df[col2]

            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            modal.show_info(self, "Success", "New feature created successfully!")

        except Exception as e:
            modal.show_error(self, "Error", f"Error creating feature: {str(e)}")

    # ── Categorical Tab Logic ──────────────────────────────────────────────

    def _on_cat_col_changed(self):
        col = self.cat_chip_selector.selected_one()
        if col and self.data_manager.data is not None:
            df = self.data_manager.data
            counts = df[col].value_counts()
            parts = [f"{val}: {cnt}" for val, cnt in counts.head(10).items()]
            if len(counts) > 10:
                parts.append(f"... +{len(counts) - 10} more")
            self._cat_preview_label.setText("  |  ".join(parts))
            self._cat_preview_label.setVisible(True)
        else:
            self._cat_preview_label.setVisible(False)

    def _on_encoding_method_changed(self, method):
        self._target_col_widget.setVisible(method == "Target Encoding")

    def apply_categorical_encoding(self):
        if self.data_manager.data is None:
            return

        df = self.data_manager.data.copy()
        col = self.cat_chip_selector.selected_one()
        method = self.encoding_cards.selected()

        if not col:
            modal.show_warning(self, "Warning", "Please select a categorical column.")
            return
        if not method:
            modal.show_warning(self, "Warning", "Please select an encoding method.")
            return

        try:
            # Apply rare category grouping if enabled
            if self.rare_group_check.isChecked():
                threshold = self.rare_threshold_spin.value() / 100.0
                freq = df[col].value_counts(normalize=True)
                rare_cats = freq[freq < threshold].index
                if len(rare_cats) > 0:
                    df[col] = df[col].replace(rare_cats, "Other")

            if method == "Label Encoding":
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(df[col])

            elif method == "One-Hot Encoding":
                encoded = pd.get_dummies(df[col], prefix=col)
                df = pd.concat([df, encoded], axis=1)

            elif method == "Binary Encoding":
                unique_values = df[col].unique()
                n_values = len(unique_values)
                n_bits = int(np.ceil(np.log2(max(n_values, 2))))
                value_to_binary = {val: format(i, f'0{n_bits}b')
                                   for i, val in enumerate(unique_values)}
                for bit in range(n_bits):
                    df[f"{col}_bin_{bit}"] = df[col].map(
                        lambda x, b=bit: int(value_to_binary[x][b]))

            elif method == "Frequency Encoding":
                frequency = df[col].value_counts(normalize=True)
                df[f"{col}_freq"] = df[col].map(frequency)

            elif method == "Target Encoding":
                target_col = self.target_col_combo.currentText()
                if not target_col:
                    modal.show_warning(self, "Warning", "Please select a target column.")
                    return
                target_mean = df.groupby(col)[target_col].mean()
                df[f"{col}_target_encoded"] = df[col].map(target_mean)

            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            modal.show_info(self, "Success", "Categorical encoding applied successfully!")

        except Exception as e:
            modal.show_error(self, "Error", f"Error applying encoding: {str(e)}")

    # ── DateTime Tab Logic ─────────────────────────────────────────────────

    def extract_datetime_features(self):
        if self.data_manager.data is None:
            return

        df = self.data_manager.data.copy()
        col = self.dt_chip_selector.selected_one()

        if not col:
            modal.show_warning(self, "Warning", "Please select a datetime column.")
            return

        try:
            dt_series = pd.to_datetime(df[col])

            if self.dt_toggle_chips.is_checked("year"):
                df[f"{col}_year"] = dt_series.dt.year
            if self.dt_toggle_chips.is_checked("month"):
                df[f"{col}_month"] = dt_series.dt.month
            if self.dt_toggle_chips.is_checked("day"):
                df[f"{col}_day"] = dt_series.dt.day
            if self.dt_toggle_chips.is_checked("weekday"):
                df[f"{col}_weekday"] = dt_series.dt.dayofweek
            if self.dt_toggle_chips.is_checked("hour"):
                df[f"{col}_hour"] = dt_series.dt.hour
            if self.dt_toggle_chips.is_checked("minute"):
                df[f"{col}_minute"] = dt_series.dt.minute
            if self.dt_toggle_chips.is_checked("quarter"):
                df[f"{col}_quarter"] = dt_series.dt.quarter
            if self.dt_toggle_chips.is_checked("is_weekend"):
                df[f"{col}_is_weekend"] = dt_series.dt.dayofweek.isin([5, 6]).astype(int)

            # New extractions
            if self.dt_toggle_chips.is_checked("is_month_start"):
                df[f"{col}_is_month_start"] = dt_series.dt.is_month_start.astype(int)
            if self.dt_toggle_chips.is_checked("is_month_end"):
                df[f"{col}_is_month_end"] = dt_series.dt.is_month_end.astype(int)
            if self.dt_toggle_chips.is_checked("season"):
                month = dt_series.dt.month
                df[f"{col}_season"] = month.map({
                    12: "Winter", 1: "Winter", 2: "Winter",
                    3: "Spring", 4: "Spring", 5: "Spring",
                    6: "Summer", 7: "Summer", 8: "Summer",
                    9: "Fall", 10: "Fall", 11: "Fall",
                })
            if self.dt_toggle_chips.is_checked("days_since_min"):
                min_date = dt_series.min()
                df[f"{col}_days_since_min"] = (dt_series - min_date).dt.days
            if self.dt_toggle_chips.is_checked("cyclical_month"):
                month = dt_series.dt.month
                df[f"{col}_month_sin"] = np.sin(2 * np.pi * month / 12)
                df[f"{col}_month_cos"] = np.cos(2 * np.pi * month / 12)
            if self.dt_toggle_chips.is_checked("cyclical_dow"):
                dow = dt_series.dt.dayofweek
                df[f"{col}_dow_sin"] = np.sin(2 * np.pi * dow / 7)
                df[f"{col}_dow_cos"] = np.cos(2 * np.pi * dow / 7)

            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            modal.show_info(self, "Success", "DateTime features extracted successfully!")

        except Exception as e:
            modal.show_error(self, "Error", f"Error extracting datetime features: {str(e)}")

    # ── Combination Tab Logic ──────────────────────────────────────────────

    def _on_combine_selection_changed(self):
        count = self.combine_chip_selector.count()
        self._combine_count_label.setText(f"{count} selected")
        self._update_combine_preview()
        self._update_ratio_warning()

    def _on_combine_method_changed(self, method):
        self._poly_widget.setVisible(method == "poly")
        self._concat_widget.setVisible(method == "concat")
        self._update_combine_preview()
        self._update_ratio_warning()

    def _update_ratio_warning(self):
        method = self.combine_method_cards.selected()
        count = self.combine_chip_selector.count()
        if method == "ratio" and count != 2:
            self._ratio_warning.setText("⚠ Ratio requires exactly 2 columns")
            self._ratio_warning.setVisible(True)
        else:
            self._ratio_warning.setVisible(False)

    def _update_combine_preview(self):
        """Show live preview of first 5 rows."""
        df = self.data_manager.data
        if df is None:
            return

        cols = self.combine_chip_selector.selected()
        method = self.combine_method_cards.selected()

        if len(cols) < 2 or not method:
            self._combine_preview_label.setText("Select columns and method to see preview")
            return

        try:
            sample = df[cols].head(5).copy()
            result = None

            if method == "sum":
                result = sample.select_dtypes(include=[np.number]).sum(axis=1)
            elif method == "mean":
                result = sample.select_dtypes(include=[np.number]).mean(axis=1)
            elif method == "product":
                result = sample.select_dtypes(include=[np.number]).prod(axis=1)
            elif method == "ratio" and len(cols) == 2:
                c1, c2 = cols[0], cols[1]
                if np.issubdtype(df[c1].dtype, np.number) and np.issubdtype(df[c2].dtype, np.number):
                    result = sample[c1] / sample[c2].replace(0, np.nan)
            elif method == "poly":
                # Show first interaction term as preview
                num_cols = [c for c in cols if np.issubdtype(df[c].dtype, np.number)]
                if len(num_cols) >= 2:
                    result = sample[num_cols[0]] * sample[num_cols[1]]
            elif method == "concat":
                sep = self.concat_separator_edit.text() or "_"
                result = sample.astype(str).agg(sep.join, axis=1)

            if result is not None:
                lines = [f"Row {i}: {v}" for i, v in enumerate(result.values)]
                self._combine_preview_label.setText("\n".join(lines))
            else:
                self._combine_preview_label.setText("Cannot preview with current selection")

        except Exception:
            self._combine_preview_label.setText("Cannot preview with current selection")

    def update_combination_columns_table(self):
        """Legacy compat — now updates chip selector instead."""
        df = self.data_manager.data
        if df is None:
            return
        self.combine_chip_selector.set_items(df.columns.tolist())

    def create_combined_feature(self):
        if self.data_manager.data is None:
            return

        df = self.data_manager.data.copy()
        method = self.combine_method_cards.selected()
        new_name = self.combine_name_edit.text()

        if not method:
            modal.show_warning(self, "Warning", "Please select a combination method.")
            return
        if not new_name:
            modal.show_warning(self, "Warning", "Please specify a name for the new feature.")
            return

        selected_columns = self.combine_chip_selector.selected()

        if len(selected_columns) < 2:
            modal.show_warning(self, "Warning", "Please select at least two columns to combine.")
            return

        try:
            if method == "sum":
                df[new_name] = df[selected_columns].sum(axis=1)
            elif method == "mean":
                df[new_name] = df[selected_columns].mean(axis=1)
            elif method == "product":
                df[new_name] = df[selected_columns].prod(axis=1)
            elif method == "ratio":
                if len(selected_columns) != 2:
                    modal.show_warning(self, "Warning", "Ratio requires exactly 2 columns.")
                    return
                c1, c2 = selected_columns
                if (df[c2] == 0).any():
                    raise ValueError("Division by zero encountered")
                df[new_name] = df[c1] / df[c2]
            elif method == "poly":
                # Generate polynomial combinations up to chosen degree
                degree = self._poly_degree
                num_cols = [c for c in selected_columns
                            if np.issubdtype(df[c].dtype, np.number)]
                if len(num_cols) < 2:
                    modal.show_warning(self, "Warning",
                                        "Polynomial requires at least 2 numeric columns.")
                    return
                # Squared terms
                for c in num_cols:
                    df[f"{c}_sq"] = df[c] ** 2
                # Interaction terms
                for i in range(len(num_cols)):
                    for j in range(i + 1, len(num_cols)):
                        df[f"{num_cols[i]}_x_{num_cols[j]}"] = df[num_cols[i]] * df[num_cols[j]]
                if degree >= 3:
                    for c in num_cols:
                        df[f"{c}_cb"] = df[c] ** 3
            elif method == "concat":
                sep = self.concat_separator_edit.text() or "_"
                df[new_name] = df[selected_columns].astype(str).agg(sep.join, axis=1)

            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            modal.show_info(self, "Success", "Combined feature created successfully!")

        except Exception as e:
            modal.show_error(self, "Error", f"Error creating combined feature: {str(e)}")
