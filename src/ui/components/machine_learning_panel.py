"""
Machine learning panel for model training, evaluation, and predictions.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QSpinBox,
    QGridLayout, QTabWidget, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QScrollArea, QFrame, QSizePolicy,
    QSlider, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QFont
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, r2_score, mean_absolute_error
)
from sklearn.linear_model import (
    LinearRegression, LogisticRegression, Ridge, Lasso
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor
)
from sklearn.svm import SVC, SVR
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from ui.theme import get_colors, apply_dark_theme
from ui.components import modal


# ── Shared styling helpers ─────────────────────────────────────────────────

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
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {c['bg_input']};
            color: {c['text_primary']};
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 22px;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
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


def _card_style(selected=False):
    c = _colors()
    if selected:
        return f"""
            QPushButton {{
                background-color: rgba(99,102,241,0.15);
                color: {c['text_primary']};
                border: 1.5px solid {c['accent']};
                border-radius: 8px;
                padding: 8px 4px;
                font-size: 12px;
                min-height: 64px;
                max-height: 64px;
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
                min-height: 64px;
                max-height: 64px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                color: {c['text_primary']};
                border-color: rgba(99,102,241,0.4);
            }}
        """


def _footer_btn_style():
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


def _footer_btn_disabled_style():
    c = _colors()
    return f"""
        QPushButton {{
            background-color: {c['bg_tertiary']};
            color: {c['text_disabled']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 0px 16px;
            font-size: 13px;
            font-weight: 600;
            min-height: 40px;
            max-height: 40px;
        }}
    """


def _scroll_wrap(widget):
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    return scroll


# ── Chip selector (single or multi) ───────────────────────────────────────

class ChipSelector(QWidget):
    selection_changed = pyqtSignal()

    def __init__(self, multi_select=False, columns=4, parent=None):
        super().__init__(parent)
        self.multi_select = multi_select
        self._columns = columns
        self._chips = {}
        self._selected = set()
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def set_items(self, items):
        for btn in self._chips.values():
            btn.deleteLater()
        self._chips.clear()
        self._selected.clear()
        for i, name in enumerate(items):
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(_chip_style(False))
            btn.clicked.connect(lambda checked, n=name: self._on_clicked(n))
            row, col = divmod(i, self._columns)
            self._layout.addWidget(btn, row, col)
            self._chips[name] = btn
        self.selection_changed.emit()

    def set_items_checked(self, items, default_checked=True):
        """Set items with optional default selection state."""
        for btn in self._chips.values():
            btn.deleteLater()
        self._chips.clear()
        self._selected.clear()
        for i, name in enumerate(items):
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            if default_checked:
                self._selected.add(name)
            btn.setStyleSheet(_chip_style(default_checked))
            btn.clicked.connect(lambda checked, n=name: self._on_clicked(n))
            row, col = divmod(i, self._columns)
            self._layout.addWidget(btn, row, col)
            self._chips[name] = btn
        self.selection_changed.emit()

    def _on_clicked(self, name):
        if self.multi_select:
            if name in self._selected:
                self._selected.discard(name)
            else:
                self._selected.add(name)
        else:
            self._selected = {name}
        for n, btn in self._chips.items():
            btn.setStyleSheet(_chip_style(n in self._selected))
        self.selection_changed.emit()

    def selected(self):
        return list(self._selected)

    def selected_one(self):
        return list(self._selected)[0] if self._selected else ""

    def count(self):
        return len(self._selected)

    def select_all(self):
        self._selected = set(self._chips.keys())
        for n, btn in self._chips.items():
            btn.setStyleSheet(_chip_style(True))
        self.selection_changed.emit()

    def deselect(self, name):
        self._selected.discard(name)
        if name in self._chips:
            self._chips[name].setStyleSheet(_chip_style(False))
        self.selection_changed.emit()


# ── Card selector (single select) ─────────────────────────────────────────

class CardSelector(QWidget):
    selection_changed = pyqtSignal(str)

    def __init__(self, columns=3, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._cards = {}
        self._selected = ""
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def add_card(self, key, label, subtitle=""):
        text = f"{label}\n{subtitle}" if subtitle else label
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(_card_style(False) + "QPushButton { text-align: center; }")
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFixedHeight(64)
        btn.clicked.connect(lambda: self._on_clicked(key))
        idx = len(self._cards)
        row, col = divmod(idx, self._columns)
        self._layout.addWidget(btn, row, col)
        self._cards[key] = btn

    def set_cards(self, card_list):
        """Replace all cards. card_list = [(key, label, subtitle), ...]"""
        for btn in self._cards.values():
            btn.deleteLater()
        self._cards.clear()
        self._selected = ""
        for key, label, subtitle in card_list:
            self.add_card(key, label, subtitle)

    def _on_clicked(self, key):
        self._selected = key
        for k, btn in self._cards.items():
            sel = k == key
            btn.setStyleSheet(_card_style(sel) + "QPushButton { text-align: center; }")
        self.selection_changed.emit(key)

    def selected(self):
        return self._selected

    def select(self, key):
        self._on_clicked(key)


# ── Segmented button group ────────────────────────────────────────────────

class SegmentedButtons(QWidget):
    selection_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}
        self._selected = ""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

    def add_button(self, key, label):
        btn = QPushButton(label)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(_chip_style(False))
        btn.setMinimumWidth(48)
        btn.clicked.connect(lambda: self._on_clicked(key))
        self._layout.addWidget(btn)
        self._buttons[key] = btn

    def _on_clicked(self, key):
        self._selected = key
        for k, btn in self._buttons.items():
            btn.setStyleSheet(_chip_style(k == key))
        self.selection_changed.emit(key)

    def selected(self):
        return self._selected

    def select(self, key):
        self._on_clicked(key)


# ── Metric stat card ──────────────────────────────────────────────────────

class MetricCard(QWidget):
    """A compact stat card showing metric name + value with color indicator."""

    def __init__(self, name="", parent=None):
        super().__init__(parent)
        c = _colors()
        self._name = name
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        self._name_label = QLabel(name)
        self._name_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_secondary']};
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.8px;
                padding: 0;
                background: transparent;
            }}
        """)

        self._value_label = QLabel("N/A")
        self._value_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_primary']};
                font-size: 20px;
                font-weight: 700;
                padding: 0;
                background: transparent;
            }}
        """)

        lay.addWidget(self._name_label)
        lay.addWidget(self._value_label)

        self.setStyleSheet(f"""
            MetricCard {{
                background-color: {c['bg_tertiary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
        """)

    def set_value(self, value, name=None, quality=None):
        """Update metric value. quality: 'good', 'moderate', 'poor', or None."""
        c = _colors()
        if name:
            self._name_label.setText(name)
        self._value_label.setText(f"{value:.4f}" if isinstance(value, float) else str(value))

        # Color indicator
        if quality == "good":
            color = c['success']
        elif quality == "moderate":
            color = c['warning']
        elif quality == "poor":
            color = c['danger']
        else:
            color = c['text_primary']

        self._value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 20px;
                font-weight: 700;
                padding: 0;
                background: transparent;
            }}
        """)

    def reset(self):
        c = _colors()
        self._value_label.setText("N/A")
        self._value_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_primary']};
                font-size: 20px;
                font-weight: 700;
                padding: 0;
                background: transparent;
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN PANEL
# ═══════════════════════════════════════════════════════════════════════════

class MachineLearningPanel(QWidget):
    """Panel for machine learning operations."""

    model_trained = pyqtSignal()

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.model = None
        self.scaler = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_columns = []
        self.init_ui()
        self.setup_connections()

    # ── UI Construction ────────────────────────────────────────────────────

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.addTab(self._build_training_tab(), "Model Training")
        tabs.addTab(self._build_evaluation_tab(), "Model Evaluation")
        tabs.addTab(self._build_predictions_tab(), "Predictions")
        layout.addWidget(tabs)

    # ── TAB 1: Model Training ──────────────────────────────────────────────

    def _build_training_tab(self):
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        # ─ DATA CONFIGURATION ─
        body_lay.addWidget(_section_header("Target Column"))
        self.target_chips = ChipSelector(multi_select=False, columns=4)
        body_lay.addWidget(self.target_chips)

        # Features
        feat_hdr_row = QHBoxLayout()
        feat_hdr_row.setContentsMargins(0, 0, 0, 0)
        feat_hdr_row.addWidget(_section_header("Features"))
        self._features_count_label = QLabel("0 of 0 selected")
        c = _colors()
        self._features_count_label.setStyleSheet(f"""
            QLabel {{
                color: {c['accent']};
                font-size: 11px;
                font-weight: 600;
                padding: 0;
                background: transparent;
            }}
        """)
        feat_hdr_row.addWidget(self._features_count_label, 0, Qt.AlignRight | Qt.AlignBottom)
        feat_container = QWidget()
        feat_container.setLayout(feat_hdr_row)
        body_lay.addWidget(feat_container)

        self.features_chips = ChipSelector(multi_select=True, columns=4)
        body_lay.addWidget(self.features_chips)

        # Problem type
        body_lay.addWidget(_section_header("Problem Type"))
        self.problem_type_btns = SegmentedButtons()
        self.problem_type_btns.add_button("Classification", "Classification")
        self.problem_type_btns.add_button("Regression", "Regression")
        self.problem_type_btns.add_button("Clustering", "Clustering")
        self.problem_type_btns.select("Classification")
        body_lay.addWidget(self.problem_type_btns)

        # ─ MODEL CONFIGURATION ─
        body_lay.addWidget(_section_header("Model"))
        self.model_cards = CardSelector(columns=3)
        body_lay.addWidget(self.model_cards)
        self._update_model_cards("Classification")

        # Test size (slider + spin)
        body_lay.addWidget(_section_header("Test Size"))
        test_row = QHBoxLayout()
        test_row.setContentsMargins(0, 0, 0, 0)
        test_row.setSpacing(10)

        self.test_size_slider = QSlider(Qt.Horizontal)
        self.test_size_slider.setRange(10, 40)
        self.test_size_slider.setValue(20)
        self.test_size_slider.setSingleStep(5)
        self.test_size_slider.setTickPosition(QSlider.TicksBelow)
        self.test_size_slider.setTickInterval(5)
        self.test_size_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {c['bg_input']};
                height: 6px;
                border-radius: 3px;
                border: 1px solid rgba(255,255,255,0.12);
            }}
            QSlider::handle:horizontal {{
                background: {c['accent']};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {c['accent']};
                border-radius: 3px;
            }}
        """)
        test_row.addWidget(self.test_size_slider, 1)

        self._test_size_badge = QLabel("20%")
        self._test_size_badge.setFixedWidth(44)
        self._test_size_badge.setAlignment(Qt.AlignCenter)
        self._test_size_badge.setStyleSheet(f"""
            QLabel {{
                color: {c['text_primary']};
                background: {c['bg_tertiary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px;
            }}
        """)
        test_row.addWidget(self._test_size_badge)

        self.test_size_spin = QDoubleSpinBox()
        self.test_size_spin.setRange(0.1, 0.5)
        self.test_size_spin.setValue(0.2)
        self.test_size_spin.setSingleStep(0.05)
        self.test_size_spin.setFixedWidth(70)
        self.test_size_spin.setStyleSheet(_input_style())
        test_row.addWidget(self.test_size_spin)

        test_w = QWidget()
        test_w.setLayout(test_row)
        body_lay.addWidget(test_w)

        # CV Folds
        body_lay.addWidget(_section_header("Cross-Validation Folds"))
        self.cv_btns = SegmentedButtons()
        self.cv_btns.add_button("3", "3")
        self.cv_btns.add_button("5", "5")
        self.cv_btns.add_button("10", "10")
        self.cv_btns.add_button("None", "None")
        self.cv_btns.select("5")
        body_lay.addWidget(self.cv_btns)

        # Feature Scaling
        body_lay.addWidget(_section_header("Feature Scaling"))
        self.scaling_btns = SegmentedButtons()
        self.scaling_btns.add_button("None", "None")
        self.scaling_btns.add_button("StandardScaler", "Standard Scaler")
        self.scaling_btns.add_button("MinMaxScaler", "Min-Max")
        self.scaling_btns.add_button("RobustScaler", "Robust Scaler")
        self.scaling_btns.select("None")
        body_lay.addWidget(self.scaling_btns)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        outer_lay.addWidget(scroll, 1)

        # ─ Footer: Train + Evaluate side by side ─
        footer = QWidget()
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(14, 6, 14, 10)
        f_lay.setSpacing(10)

        self.train_btn = QPushButton("Train Model")
        self.train_btn.setStyleSheet(_footer_btn_style())
        self.train_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        f_lay.addWidget(self.train_btn)

        self.evaluate_btn = QPushButton("Evaluate Model")
        self.evaluate_btn.setStyleSheet(_footer_btn_style())
        self.evaluate_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.evaluate_btn.setToolTip("Train a model first")
        self.evaluate_btn.setEnabled(False)
        f_lay.addWidget(self.evaluate_btn)

        outer_lay.addWidget(footer)
        return outer

    # ── TAB 2: Model Evaluation ────────────────────────────────────────────

    def _build_evaluation_tab(self):
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        # ─ Metric stat cards row ─
        body_lay.addWidget(_section_header("Model Metrics"))
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(8)

        self.metric_card_1 = MetricCard("Accuracy / R²")
        self.metric_card_2 = MetricCard("Precision / MAE")
        self.metric_card_3 = MetricCard("Recall / MSE")
        self.metric_card_4 = MetricCard("F1 / RMSE")
        for card in (self.metric_card_1, self.metric_card_2,
                      self.metric_card_3, self.metric_card_4):
            metrics_row.addWidget(card)

        metrics_w = QWidget()
        metrics_w.setLayout(metrics_row)
        body_lay.addWidget(metrics_w)

        # ─ Cross-validation results ─
        body_lay.addWidget(_section_header("Cross-Validation Results"))
        self.cv_table = QTableWidget()
        self.cv_table.setAlternatingRowColors(True)
        self.cv_table.setMaximumHeight(180)
        c = _colors()
        self.cv_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c['bg_input']};
                alternate-background-color: {c['table_alt']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                gridline-color: {c['table_grid']};
            }}
            QHeaderView::section {{
                background-color: {c['table_header']};
                color: {c['text_secondary']};
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                padding: 6px 8px;
                border: none;
                border-bottom: 2px solid {c['accent']};
            }}
        """)
        body_lay.addWidget(self.cv_table)

        # ─ Feature importance chart ─
        body_lay.addWidget(_section_header("Feature Importance"))
        self.importance_figure = plt.figure(facecolor='#0f1117')
        self.importance_canvas = FigureCanvas(self.importance_figure)
        self.importance_canvas.setMinimumHeight(250)
        fi_frame = QFrame()
        fi_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
            }}
        """)
        fi_lay = QVBoxLayout(fi_frame)
        fi_lay.setContentsMargins(8, 8, 8, 8)
        fi_lay.addWidget(self.importance_canvas)
        body_lay.addWidget(fi_frame)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        outer_lay.addWidget(scroll, 1)

        return outer

    # ── TAB 3: Predictions ─────────────────────────────────────────────────

    def _build_predictions_tab(self):
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 10, 14, 10)
        body_lay.setSpacing(12)
        body_lay.setAlignment(Qt.AlignTop)

        c = _colors()

        # ─ Prediction method ─
        body_lay.addWidget(_section_header("Prediction Method"))
        self.pred_method_btns = SegmentedButtons()
        self.pred_method_btns.add_button("Test Set", "Test Set")
        self.pred_method_btns.add_button("Current Data", "Current Data")
        self.pred_method_btns.add_button("New Data", "New Data")
        self.pred_method_btns.select("Test Set")
        body_lay.addWidget(self.pred_method_btns)

        # ─ Single-row input form (for New Data) ─
        self._new_data_section = QWidget()
        nd_lay = QVBoxLayout(self._new_data_section)
        nd_lay.setContentsMargins(0, 0, 0, 0)
        nd_lay.setSpacing(8)
        nd_lay.addWidget(_section_header("Enter Feature Values"))

        self._input_fields_container = QWidget()
        self._input_fields_layout = QGridLayout(self._input_fields_container)
        self._input_fields_layout.setContentsMargins(0, 0, 0, 0)
        self._input_fields_layout.setSpacing(8)
        nd_lay.addWidget(self._input_fields_container)

        self._new_data_section.setVisible(False)
        body_lay.addWidget(self._new_data_section)

        # ─ Prediction result card (for single prediction) ─
        self._result_card = QFrame()
        self._result_card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_tertiary']};
                border: 1.5px solid {c['accent']};
                border-radius: 10px;
            }}
        """)
        rc_lay = QVBoxLayout(self._result_card)
        rc_lay.setContentsMargins(16, 14, 16, 14)
        rc_lay.setSpacing(4)

        self._result_title = QLabel("PREDICTION RESULT")
        self._result_title.setStyleSheet(f"""
            QLabel {{
                color: {c['accent']};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1.2px;
                padding: 0;
                background: transparent;
            }}
        """)
        self._result_value = QLabel("—")
        self._result_value.setStyleSheet(f"""
            QLabel {{
                color: {c['text_primary']};
                font-size: 24px;
                font-weight: 700;
                padding: 0;
                background: transparent;
            }}
        """)
        rc_lay.addWidget(self._result_title)
        rc_lay.addWidget(self._result_value)
        self._result_card.setVisible(False)
        body_lay.addWidget(self._result_card)

        # ─ Divider ─
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background: {c['border']}; max-height: 1px;")
        body_lay.addWidget(divider)

        # ─ Batch results table ─
        body_lay.addWidget(_section_header("Prediction Results"))
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c['bg_input']};
                alternate-background-color: {c['table_alt']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                gridline-color: {c['table_grid']};
            }}
            QHeaderView::section {{
                background-color: {c['table_header']};
                color: {c['text_secondary']};
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                padding: 6px 8px;
                border: none;
                border-bottom: 2px solid {c['accent']};
            }}
        """)
        body_lay.addWidget(self.results_table)

        body_lay.addStretch()

        scroll = _scroll_wrap(body)
        outer_lay.addWidget(scroll, 1)

        # ─ Footer ─
        footer = QWidget()
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(14, 6, 14, 10)
        f_lay.setSpacing(10)

        self.predict_btn = QPushButton("Make Predictions")
        self.predict_btn.setStyleSheet(_footer_btn_style())
        self.predict_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.predict_btn.setEnabled(False)
        self.predict_btn.setToolTip("Train a model first")
        f_lay.addWidget(self.predict_btn)

        self.export_btn = QPushButton("Export Predictions")
        self.export_btn.setStyleSheet(_footer_btn_style())
        self.export_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.export_btn.setEnabled(False)
        f_lay.addWidget(self.export_btn)

        outer_lay.addWidget(footer)
        return outer

    # ── Signal Connections ─────────────────────────────────────────────────

    def setup_connections(self):
        self.data_manager.data_loaded.connect(self.on_data_loaded)
        self.problem_type_btns.selection_changed.connect(self._on_problem_type_changed)
        self.features_chips.selection_changed.connect(self._on_features_changed)
        self.target_chips.selection_changed.connect(self._on_target_changed)

        # Test size slider <-> spin sync
        self.test_size_slider.valueChanged.connect(self._on_slider_changed)
        self.test_size_spin.valueChanged.connect(self._on_spin_changed)

        # Buttons
        self.train_btn.clicked.connect(self.train_model)
        self.evaluate_btn.clicked.connect(self.evaluate_model)
        self.predict_btn.clicked.connect(self.make_predictions)
        self.export_btn.clicked.connect(self.export_predictions)

        # Prediction method toggle
        self.pred_method_btns.selection_changed.connect(self._on_pred_method_changed)

    # ── UI update helpers ──────────────────────────────────────────────────

    def _on_slider_changed(self, value):
        pct = value / 100.0
        self._test_size_badge.setText(f"{value}%")
        self.test_size_spin.blockSignals(True)
        self.test_size_spin.setValue(pct)
        self.test_size_spin.blockSignals(False)

    def _on_spin_changed(self, value):
        slider_val = int(round(value * 100))
        self._test_size_badge.setText(f"{slider_val}%")
        self.test_size_slider.blockSignals(True)
        self.test_size_slider.setValue(slider_val)
        self.test_size_slider.blockSignals(False)

    def _on_problem_type_changed(self, problem_type):
        self._update_model_cards(problem_type)

    def _on_features_changed(self):
        total = len(self.features_chips._chips)
        sel = self.features_chips.count()
        self._features_count_label.setText(f"{sel} of {total} selected")

    def _on_target_changed(self):
        # Auto-deselect target from features
        target = self.target_chips.selected_one()
        if target:
            self.features_chips.deselect(target)

    def _on_pred_method_changed(self, method):
        is_new = method == "New Data"
        self._new_data_section.setVisible(is_new)
        if is_new:
            self._build_input_fields()

    def _build_input_fields(self):
        """Build compact 3-column input grid for new data prediction."""
        # Clear existing
        while self._input_fields_layout.count():
            item = self._input_fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._new_data_inputs = {}
        cols = self.feature_columns if self.feature_columns else []
        for i, col_name in enumerate(cols):
            row, column = divmod(i, 3)
            container = QWidget()
            cl = QVBoxLayout(container)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(2)
            lbl = QLabel(col_name)
            c = _colors()
            lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px; padding: 0; background: transparent;")
            inp = QLineEdit()
            inp.setPlaceholderText("0.0")
            inp.setStyleSheet(_input_style())
            cl.addWidget(lbl)
            cl.addWidget(inp)
            self._input_fields_layout.addWidget(container, row, column)
            self._new_data_inputs[col_name] = inp

    def _update_model_cards(self, problem_type):
        if problem_type == "Classification":
            cards = [
                ("Logistic Regression", "Logistic Regression", "Linear"),
                ("Decision Tree", "Decision Tree", "Tree-based"),
                ("Random Forest", "Random Forest", "Ensemble"),
                ("Gradient Boosting", "Gradient Boosting", "Ensemble"),
                ("SVM", "SVM", "Kernel"),
            ]
        elif problem_type == "Regression":
            cards = [
                ("Linear Regression", "Linear Regression", "Linear"),
                ("Ridge Regression", "Ridge Regression", "Linear"),
                ("Lasso Regression", "Lasso Regression", "Linear"),
                ("Decision Tree", "Decision Tree", "Tree-based"),
                ("Random Forest", "Random Forest", "Ensemble"),
                ("Gradient Boosting", "Gradient Boosting", "Ensemble"),
                ("SVR", "SVR", "Kernel"),
            ]
        else:  # Clustering
            cards = [
                ("KMeans", "K-Means", "Centroid"),
                ("DBSCAN", "DBSCAN", "Density"),
            ]
        self.model_cards.set_cards(cards)

    def _update_btn_enabled_style(self):
        """Update button styles based on enabled state."""
        for btn in (self.evaluate_btn, self.predict_btn, self.export_btn):
            if btn.isEnabled():
                btn.setStyleSheet(_footer_btn_style())
            else:
                btn.setStyleSheet(_footer_btn_disabled_style())

    # ── Data Load Handler ──────────────────────────────────────────────────

    def on_data_loaded(self, df):
        if df is None:
            return

        columns = df.columns.tolist()
        self.target_chips.set_items(columns)
        self.features_chips.set_items_checked(columns, default_checked=True)
        self._on_features_changed()

    # ── Compatibility shims for backend ────────────────────────────────────

    def get_selected_features(self):
        """Get list of selected feature columns (chip-based)."""
        target = self.target_chips.selected_one()
        return [c for c in self.features_chips.selected() if c != target]

    def prepare_data(self):
        """Prepare data for model training."""
        df = self.data_manager.data
        if df is None:
            return False

        target_col = self.target_chips.selected_one()
        if not target_col:
            modal.show_warning(self, "Warning", "Please select a target column.")
            return False

        self.feature_columns = self.get_selected_features()

        if not self.feature_columns:
            modal.show_warning(self, "Warning", "Please select at least one feature.")
            return False

        non_numeric = [c for c in self.feature_columns
                       if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            modal.show_warning(
                self, "Warning",
                f"Non-numeric feature columns detected: {', '.join(non_numeric)}.\n"
                "Please encode categorical features first (Feature Engineering tab)."
            )
            return False

        X = df[self.feature_columns].copy()
        y = df[target_col].copy()

        scaling_method = self.scaling_btns.selected()
        if scaling_method != "None":
            if scaling_method == "StandardScaler":
                self.scaler = StandardScaler()
            elif scaling_method == "MinMaxScaler":
                self.scaler = MinMaxScaler()
            elif scaling_method == "RobustScaler":
                self.scaler = RobustScaler()
            X = pd.DataFrame(self.scaler.fit_transform(X), columns=X.columns)
        else:
            self.scaler = None

        test_size = self.test_size_spin.value()
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        return True

    def get_model_instance(self):
        """Get a new instance of the selected model."""
        model_name = self.model_cards.selected()
        problem_type = self.problem_type_btns.selected()

        if problem_type == "Classification":
            if model_name == "Logistic Regression":
                return LogisticRegression(random_state=42)
            elif model_name == "Decision Tree":
                return DecisionTreeClassifier(random_state=42)
            elif model_name == "Random Forest":
                return RandomForestClassifier(random_state=42)
            elif model_name == "Gradient Boosting":
                return GradientBoostingClassifier(random_state=42)
            elif model_name == "SVM":
                return SVC(random_state=42)
        else:  # Regression
            if model_name == "Linear Regression":
                return LinearRegression()
            elif model_name == "Ridge Regression":
                return Ridge(random_state=42)
            elif model_name == "Lasso Regression":
                return Lasso(random_state=42)
            elif model_name == "Decision Tree":
                return DecisionTreeRegressor(random_state=42)
            elif model_name == "Random Forest":
                return RandomForestRegressor(random_state=42)
            elif model_name == "Gradient Boosting":
                return GradientBoostingRegressor(random_state=42)
            elif model_name == "SVR":
                return SVR()

    def train_model(self):
        """Train the selected model."""
        if not self.prepare_data():
            return

        try:
            self.model = self.get_model_instance()
            if self.model is None:
                modal.show_warning(self, "Warning", "Please select a model.")
                return
            self.model.fit(self.X_train, self.y_train)

            self.evaluate_btn.setEnabled(True)
            self.predict_btn.setEnabled(True)
            self._update_btn_enabled_style()

            modal.show_info(self, "Success", "Model trained successfully!")

        except Exception as e:
            modal.show_error(self, "Error", f"Error training model: {str(e)}")

    def evaluate_model(self):
        """Evaluate the trained model."""
        if self.model is None:
            return

        try:
            y_pred = self.model.predict(self.X_test)
            problem_type = self.problem_type_btns.selected()

            if problem_type == "Classification":
                acc = accuracy_score(self.y_test, y_pred)
                prec = precision_score(self.y_test, y_pred, average='weighted')
                rec = recall_score(self.y_test, y_pred, average='weighted')
                f1 = f1_score(self.y_test, y_pred, average='weighted')

                self.metric_card_1.set_value(acc, "Accuracy",
                    "good" if acc >= 0.8 else "moderate" if acc >= 0.6 else "poor")
                self.metric_card_2.set_value(prec, "Precision",
                    "good" if prec >= 0.8 else "moderate" if prec >= 0.6 else "poor")
                self.metric_card_3.set_value(rec, "Recall",
                    "good" if rec >= 0.8 else "moderate" if rec >= 0.6 else "poor")
                self.metric_card_4.set_value(f1, "F1 Score",
                    "good" if f1 >= 0.8 else "moderate" if f1 >= 0.6 else "poor")
            else:
                r2 = r2_score(self.y_test, y_pred)
                mae = mean_absolute_error(self.y_test, y_pred)
                mse = mean_squared_error(self.y_test, y_pred)
                rmse = np.sqrt(mse)

                self.metric_card_1.set_value(r2, "R²",
                    "good" if r2 >= 0.8 else "moderate" if r2 >= 0.5 else "poor")
                self.metric_card_2.set_value(mae, "MAE")
                self.metric_card_3.set_value(mse, "MSE")
                self.metric_card_4.set_value(rmse, "RMSE")

            # Cross-validation
            cv_val = self.cv_btns.selected()
            if cv_val != "None":
                cv_folds = int(cv_val)
                cv_model = self.get_model_instance()
                cv_scores = cross_val_score(
                    cv_model, self.X_train, self.y_train,
                    cv=min(cv_folds, len(self.X_train))
                )
                self.cv_table.setRowCount(len(cv_scores))
                self.cv_table.setColumnCount(2)
                self.cv_table.setHorizontalHeaderLabels(["Fold", "Score"])
                for i, score in enumerate(cv_scores):
                    self.cv_table.setItem(i, 0, QTableWidgetItem(f"Fold {i+1}"))
                    self.cv_table.setItem(i, 1, QTableWidgetItem(f"{score:.4f}"))
            else:
                self.cv_table.setRowCount(0)

            self.plot_feature_importance()

        except Exception as e:
            modal.show_error(self, "Error", f"Error evaluating model: {str(e)}")

    def plot_feature_importance(self):
        """Plot feature importance with dark-themed horizontal bar chart."""
        try:
            self.importance_figure.clear()
            c = _colors()

            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_)
                if importances.ndim > 1:
                    importances = importances.mean(axis=0)
            else:
                return

            # Sort descending
            indices = np.argsort(importances)
            sorted_features = [self.feature_columns[i] for i in indices]
            sorted_importances = importances[indices]

            ax = self.importance_figure.add_subplot(111)

            y_pos = np.arange(len(sorted_features))
            ax.barh(y_pos, sorted_importances, color=c['accent'], height=0.6)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(sorted_features, fontsize=9)
            ax.set_xlabel('Importance', fontsize=10)
            ax.set_title('Feature Importance', fontsize=12, fontweight='bold')

            apply_dark_theme(self.importance_figure, ax)
            self.importance_figure.tight_layout()
            self.importance_canvas.draw()

        except Exception as e:
            print(f"Error plotting feature importance: {str(e)}")

    def make_predictions(self):
        """Make predictions using the trained model."""
        if self.model is None:
            return

        try:
            method = self.pred_method_btns.selected()

            if method == "New Data":
                self._predict_new_data()
                return

            if method == "Test Set":
                X = self.X_test
                y_true = self.y_test
            elif method == "Current Data":
                df = self.data_manager.data
                X = df[self.feature_columns]
                if self.scaler:
                    X = pd.DataFrame(
                        self.scaler.transform(X),
                        columns=X.columns
                    )
                y_true = df[self.target_chips.selected_one()]
            else:
                return

            y_pred = self.model.predict(X)

            self.results_table.setRowCount(len(y_pred))
            self.results_table.setColumnCount(3)
            self.results_table.setHorizontalHeaderLabels(
                ["Index", "Actual", "Predicted"]
            )

            for i in range(len(y_pred)):
                self.results_table.setItem(i, 0, QTableWidgetItem(str(i)))
                self.results_table.setItem(i, 1, QTableWidgetItem(str(y_true.iloc[i])))
                self.results_table.setItem(i, 2, QTableWidgetItem(str(y_pred[i])))

            self.export_btn.setEnabled(True)
            self._update_btn_enabled_style()
            self._result_card.setVisible(False)

        except Exception as e:
            modal.show_error(self, "Error", f"Error making predictions: {str(e)}")

    def _predict_new_data(self):
        """Handle single-row new data prediction."""
        if not hasattr(self, '_new_data_inputs') or not self._new_data_inputs:
            modal.show_warning(self, "Warning", "No feature input fields available.")
            return

        try:
            values = {}
            for col_name, inp in self._new_data_inputs.items():
                text = inp.text().strip()
                if not text:
                    modal.show_warning(self, "Warning", f"Please enter a value for '{col_name}'.")
                    return
                values[col_name] = float(text)

            X_new = pd.DataFrame([values])
            if self.scaler:
                X_new = pd.DataFrame(
                    self.scaler.transform(X_new),
                    columns=X_new.columns
                )

            prediction = self.model.predict(X_new)[0]

            c = _colors()
            self._result_value.setText(str(prediction))
            self._result_value.setStyleSheet(f"""
                QLabel {{
                    color: {c['accent']};
                    font-size: 24px;
                    font-weight: 700;
                    padding: 0;
                    background: transparent;
                }}
            """)
            self._result_card.setVisible(True)

        except ValueError:
            modal.show_warning(self, "Warning", "All feature values must be numeric.")
        except Exception as e:
            modal.show_error(self, "Error", f"Error making prediction: {str(e)}")

    def export_predictions(self):
        """Export predictions to a CSV file."""
        try:
            rows = self.results_table.rowCount()
            predictions = []

            for i in range(rows):
                predictions.append({
                    'Index': self.results_table.item(i, 0).text(),
                    'Actual': self.results_table.item(i, 1).text(),
                    'Predicted': self.results_table.item(i, 2).text()
                })

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Predictions", "predictions.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            if not file_path:
                return

            pred_df = pd.DataFrame(predictions)
            pred_df.to_csv(file_path, index=False)

            modal.show_info(
                self, "Success",
                f"Predictions exported to '{file_path}'"
            )

        except Exception as e:
            modal.show_error(
                self, "Error",
                f"Error exporting predictions: {str(e)}"
            )
