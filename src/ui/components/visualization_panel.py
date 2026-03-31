"""
Visualization panel for creating and customizing data visualizations.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QComboBox, QPushButton, QScrollArea,
    QGridLayout, QSpinBox, QDoubleSpinBox, QColorDialog, QCheckBox,
    QFileDialog, QListWidget, QToolButton, QSlider,
    QSizePolicy, QGroupBox, QTabWidget, QSplitter,
    QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import matplotlib
matplotlib.use('Qt5Agg')  # Set the backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats
import os

class VisualizationPanel(QWidget):
    """Panel for creating and customizing visualizations."""

    def __init__(self, data_manager):
        """Initialize the visualization panel."""
        super().__init__()
        self.data_manager = data_manager
        self.workspace_path = None

        # Set up matplotlib figure
        plt.style.use('seaborn-v0_8')  # Use a more specific style name
        self.figure = Figure(figsize=(10, 8), dpi=100)  # Increased figure size
        self.canvas = FigureCanvas(self.figure)

        # Set up navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Store selected colors for series
        self.series_colors = {}
        self.custom_color = None
        self.color_map = None

        # Store selected series for multi-series plots
        self.selected_series = []

        # Set up update timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_visualization)

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Create a vertical splitter to allow resizing
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # Controls container using tabs for better organization
        controls_container = QWidget()
        controls_tabs = QTabWidget(controls_container)
        controls_tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Data Selection Tab
        data_tab = QWidget()
        data_layout = QGridLayout(data_tab)

        # Chart type selector
        chart_label = QLabel("Chart Type:")
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "Line Chart",
            "Bar Chart",
            "Scatter Plot",
            "Histogram",
            "Box Plot",
            "Violin Plot",
            "Heatmap",
            "KDE Plot",
            "Pie Chart",
            "Area Chart"
        ])
        data_layout.addWidget(chart_label, 0, 0)
        data_layout.addWidget(self.chart_combo, 0, 1)

        # Data selection
        x_axis_label = QLabel("X-Axis:")
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.setEnabled(False)
        data_layout.addWidget(x_axis_label, 1, 0)
        data_layout.addWidget(self.x_axis_combo, 1, 1)

        y_axis_label = QLabel("Y-Axis:")
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.setEnabled(False)
        data_layout.addWidget(y_axis_label, 2, 0)
        data_layout.addWidget(self.y_axis_combo, 2, 1)

        # Color by selector
        color_by_label = QLabel("Color By:")
        self.color_by_combo = QComboBox()
        self.color_by_combo.setEnabled(False)
        data_layout.addWidget(color_by_label, 3, 0)
        data_layout.addWidget(self.color_by_combo, 3, 1)

        # Aggregation method
        agg_label = QLabel("Aggregation:")
        self.agg_combo = QComboBox()
        self.agg_combo.addItems(["None", "Mean", "Sum", "Count", "Median", "Min", "Max"])
        self.agg_combo.setEnabled(False)
        data_layout.addWidget(agg_label, 4, 0)
        data_layout.addWidget(self.agg_combo, 4, 1)

        # Series selection for multi-series plots
        series_label = QLabel("Series (Multi-select):")
        self.series_list = QListWidget()
        self.series_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.series_list.setMaximumHeight(100)  # Limit height to save space
        data_layout.addWidget(series_label, 5, 0)
        data_layout.addWidget(self.series_list, 5, 1)

        controls_tabs.addTab(data_tab, "Data Selection")

        # Style Tab
        style_tab = QWidget()
        style_layout = QGridLayout(style_tab)

        # Title customization
        title_label = QLabel("Chart Title:")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter chart title")
        style_layout.addWidget(title_label, 0, 0)
        style_layout.addWidget(self.title_edit, 0, 1)

        # Style selection
        style_label = QLabel("Plot Style:")
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "seaborn-v0_8",
            "seaborn-v0_8-darkgrid",
            "seaborn-v0_8-whitegrid",
            "ggplot",
            "default",
            "dark_background"
        ])
        style_layout.addWidget(style_label, 1, 0)
        style_layout.addWidget(self.style_combo, 1, 1)

        # Color selection
        color_theme_label = QLabel("Color Theme:")
        self.color_combo = QComboBox()
        self.color_combo.addItems([
            "Default",
            "Viridis",
            "Plasma",
            "Inferno",
            "Magma",
            "Cividis",
            "Blues",
            "Reds",
            "Greens",
            "Custom"
        ])
        style_layout.addWidget(color_theme_label, 2, 0)
        style_layout.addWidget(self.color_combo, 2, 1)

        # Custom color button
        self.color_button = QPushButton("Choose Color")
        self.color_button.setEnabled(False)
        style_layout.addWidget(self.color_button, 3, 1)

        # Trend line / fit options
        trend_group = QGroupBox("Trend Line / Fit")
        trend_layout = QGridLayout(trend_group)

        trend_type_label = QLabel("Trend Line:")
        self.trend_combo = QComboBox()
        self.trend_combo.addItems([
            "None", "Linear", "Polynomial (2)", "Polynomial (3)",
            "Polynomial (4)", "LOWESS", "Moving Average"
        ])
        trend_layout.addWidget(trend_type_label, 0, 0)
        trend_layout.addWidget(self.trend_combo, 0, 1)

        self.confidence_check = QCheckBox("Show Confidence Interval")
        self.confidence_check.setChecked(False)
        trend_layout.addWidget(self.confidence_check, 1, 0, 1, 2)

        ci_label = QLabel("Confidence Level:")
        self.ci_combo = QComboBox()
        self.ci_combo.addItems(["90%", "95%", "99%"])
        self.ci_combo.setCurrentText("95%")
        trend_layout.addWidget(ci_label, 2, 0)
        trend_layout.addWidget(self.ci_combo, 2, 1)

        self.show_equation_check = QCheckBox("Show Equation / R²")
        self.show_equation_check.setChecked(False)
        trend_layout.addWidget(self.show_equation_check, 3, 0, 1, 2)

        style_layout.addWidget(trend_group, 3, 0, 1, 2)

        # Additional options
        options_group = QGroupBox("Display Options")
        options_layout = QGridLayout(options_group)

        self.grid_check = QCheckBox("Show Grid")
        self.grid_check.setChecked(True)
        options_layout.addWidget(self.grid_check, 0, 0)

        self.legend_check = QCheckBox("Show Legend")
        self.legend_check.setChecked(True)
        options_layout.addWidget(self.legend_check, 0, 1)

        self.data_labels_check = QCheckBox("Show Data Labels")
        self.data_labels_check.setChecked(False)
        options_layout.addWidget(self.data_labels_check, 1, 0, 1, 2)

        style_layout.addWidget(options_group, 5, 0, 1, 2)

        controls_tabs.addTab(style_tab, "Style")

        # Advanced Tab - use a scroll area for all the options
        advanced_tab = QWidget()
        advanced_scroll = QScrollArea()
        advanced_scroll.setWidgetResizable(True)
        advanced_scroll.setWidget(advanced_tab)
        advanced_layout = QGridLayout(advanced_tab)
        row = 0

        # -- Axis Labels --
        labels_group = QGroupBox("Axis Labels")
        labels_layout = QGridLayout(labels_group)

        x_label_label = QLabel("X-Axis Label:")
        self.x_label_edit = QLineEdit()
        self.x_label_edit.setPlaceholderText("Auto (from column name)")
        labels_layout.addWidget(x_label_label, 0, 0)
        labels_layout.addWidget(self.x_label_edit, 0, 1)

        y_label_label = QLabel("Y-Axis Label:")
        self.y_label_edit = QLineEdit()
        self.y_label_edit.setPlaceholderText("Auto (from column name)")
        labels_layout.addWidget(y_label_label, 1, 0)
        labels_layout.addWidget(self.y_label_edit, 1, 1)

        advanced_layout.addWidget(labels_group, row, 0, 1, 2)
        row += 1

        # -- Axis Scale & Limits --
        axis_group = QGroupBox("Axis Scale & Limits")
        axis_layout = QGridLayout(axis_group)

        x_scale_label = QLabel("X-Axis Scale:")
        self.x_scale_combo = QComboBox()
        self.x_scale_combo.addItems(["Linear", "Log"])
        axis_layout.addWidget(x_scale_label, 0, 0)
        axis_layout.addWidget(self.x_scale_combo, 0, 1)

        y_scale_label = QLabel("Y-Axis Scale:")
        self.y_scale_combo = QComboBox()
        self.y_scale_combo.addItems(["Linear", "Log"])
        axis_layout.addWidget(y_scale_label, 1, 0)
        axis_layout.addWidget(self.y_scale_combo, 1, 1)

        self.auto_limits_check = QCheckBox("Auto Axis Limits")
        self.auto_limits_check.setChecked(True)
        axis_layout.addWidget(self.auto_limits_check, 2, 0, 1, 2)

        x_min_label = QLabel("X Min:")
        self.x_min_spin = QDoubleSpinBox()
        self.x_min_spin.setRange(-1e9, 1e9)
        self.x_min_spin.setDecimals(4)
        self.x_min_spin.setEnabled(False)
        axis_layout.addWidget(x_min_label, 3, 0)
        axis_layout.addWidget(self.x_min_spin, 3, 1)

        x_max_label = QLabel("X Max:")
        self.x_max_spin = QDoubleSpinBox()
        self.x_max_spin.setRange(-1e9, 1e9)
        self.x_max_spin.setValue(100)
        self.x_max_spin.setDecimals(4)
        self.x_max_spin.setEnabled(False)
        axis_layout.addWidget(x_max_label, 4, 0)
        axis_layout.addWidget(self.x_max_spin, 4, 1)

        y_min_label = QLabel("Y Min:")
        self.y_min_spin = QDoubleSpinBox()
        self.y_min_spin.setRange(-1e9, 1e9)
        self.y_min_spin.setDecimals(4)
        self.y_min_spin.setEnabled(False)
        axis_layout.addWidget(y_min_label, 5, 0)
        axis_layout.addWidget(self.y_min_spin, 5, 1)

        y_max_label = QLabel("Y Max:")
        self.y_max_spin = QDoubleSpinBox()
        self.y_max_spin.setRange(-1e9, 1e9)
        self.y_max_spin.setValue(100)
        self.y_max_spin.setDecimals(4)
        self.y_max_spin.setEnabled(False)
        axis_layout.addWidget(y_max_label, 6, 0)
        axis_layout.addWidget(self.y_max_spin, 6, 1)

        advanced_layout.addWidget(axis_group, row, 0, 1, 2)
        row += 1

        # -- Appearance --
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QGridLayout(appearance_group)

        # Transparency slider
        alpha_label = QLabel("Transparency:")
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(10, 100)
        self.alpha_slider.setValue(80)
        appearance_layout.addWidget(alpha_label, 0, 0)
        appearance_layout.addWidget(self.alpha_slider, 0, 1)

        # Marker size for scatter plots
        marker_label = QLabel("Marker Size:")
        self.marker_size = QSpinBox()
        self.marker_size.setRange(1, 20)
        self.marker_size.setValue(6)
        appearance_layout.addWidget(marker_label, 1, 0)
        appearance_layout.addWidget(self.marker_size, 1, 1)

        # Number of bins for histograms
        bins_label = QLabel("Histogram Bins:")
        self.bins_spinbox = QSpinBox()
        self.bins_spinbox.setRange(5, 100)
        self.bins_spinbox.setValue(30)
        appearance_layout.addWidget(bins_label, 2, 0)
        appearance_layout.addWidget(self.bins_spinbox, 2, 1)

        # Font size
        font_label = QLabel("Font Size:")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 24)
        self.font_size_spin.setValue(10)
        appearance_layout.addWidget(font_label, 3, 0)
        appearance_layout.addWidget(self.font_size_spin, 3, 1)

        # Tick label rotation
        x_rot_label = QLabel("X-Tick Rotation:")
        self.x_tick_rotation_spin = QSpinBox()
        self.x_tick_rotation_spin.setRange(0, 90)
        self.x_tick_rotation_spin.setValue(0)
        self.x_tick_rotation_spin.setSuffix("°")
        appearance_layout.addWidget(x_rot_label, 4, 0)
        appearance_layout.addWidget(self.x_tick_rotation_spin, 4, 1)

        advanced_layout.addWidget(appearance_group, row, 0, 1, 2)
        row += 1

        # Export buttons
        export_group = QGroupBox("Export Options")
        export_layout = QHBoxLayout(export_group)

        self.export_png_btn = QPushButton("Export PNG")
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_svg_btn = QPushButton("Export SVG")

        export_layout.addWidget(self.export_png_btn)
        export_layout.addWidget(self.export_pdf_btn)
        export_layout.addWidget(self.export_svg_btn)

        advanced_layout.addWidget(export_group, row, 0, 1, 2)

        controls_tabs.addTab(advanced_scroll, "Advanced")

        # Set up tab container layout
        controls_container_layout = QVBoxLayout(controls_container)
        controls_container_layout.addWidget(controls_tabs)
        controls_container_layout.setContentsMargins(0, 0, 0, 0)

        # Preview area with matplotlib canvas
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # Add toolbar for interactive navigation
        preview_layout.addWidget(self.toolbar)

        # Create a frame for the canvas
        canvas_frame = QFrame()
        canvas_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        canvas_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.addWidget(self.canvas)

        # Placeholder message
        self.placeholder = QLabel("Import data to create visualizations")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        canvas_layout.addWidget(self.placeholder)

        preview_layout.addWidget(canvas_frame)

        # Add widgets to splitter and set initial sizes
        splitter.addWidget(controls_container)
        splitter.addWidget(preview_container)

        # Set initial splitter sizes (30% controls, 70% chart)
        splitter.setSizes([300, 700])

        main_layout.addWidget(splitter)

    def setup_connections(self):
        """Setup signal connections."""
        self.data_manager.data_loaded.connect(self.on_data_loaded)
        self.chart_combo.currentTextChanged.connect(self.on_chart_type_changed)
        self.x_axis_combo.currentTextChanged.connect(self.schedule_update)
        self.y_axis_combo.currentTextChanged.connect(self.schedule_update)
        self.color_by_combo.currentTextChanged.connect(self.schedule_update)
        self.series_list.itemSelectionChanged.connect(self.on_series_selection_changed)
        self.title_edit.textChanged.connect(self.schedule_update)
        self.style_combo.currentTextChanged.connect(self.schedule_update)
        self.color_combo.currentTextChanged.connect(self.on_color_theme_changed)
        self.color_button.clicked.connect(self.choose_custom_color)
        self.grid_check.stateChanged.connect(self.schedule_update)
        self.legend_check.stateChanged.connect(self.schedule_update)
        self.alpha_slider.valueChanged.connect(self.schedule_update)
        self.marker_size.valueChanged.connect(self.schedule_update)
        self.bins_spinbox.valueChanged.connect(self.schedule_update)
        self.x_scale_combo.currentTextChanged.connect(self.schedule_update)
        self.y_scale_combo.currentTextChanged.connect(self.schedule_update)
        self.agg_combo.currentTextChanged.connect(self.schedule_update)

        # Trend line / CI connections
        self.trend_combo.currentTextChanged.connect(self.schedule_update)
        self.confidence_check.stateChanged.connect(self.schedule_update)
        self.ci_combo.currentTextChanged.connect(self.schedule_update)
        self.show_equation_check.stateChanged.connect(self.schedule_update)
        self.data_labels_check.stateChanged.connect(self.schedule_update)

        # Axis label / limit connections
        self.x_label_edit.textChanged.connect(self.schedule_update)
        self.y_label_edit.textChanged.connect(self.schedule_update)
        self.auto_limits_check.stateChanged.connect(self._on_auto_limits_changed)
        self.x_min_spin.valueChanged.connect(self.schedule_update)
        self.x_max_spin.valueChanged.connect(self.schedule_update)
        self.y_min_spin.valueChanged.connect(self.schedule_update)
        self.y_max_spin.valueChanged.connect(self.schedule_update)
        self.font_size_spin.valueChanged.connect(self.schedule_update)
        self.x_tick_rotation_spin.valueChanged.connect(self.schedule_update)

        # Export connections
        self.export_png_btn.clicked.connect(lambda: self.export_plot('png'))
        self.export_pdf_btn.clicked.connect(lambda: self.export_plot('pdf'))
        self.export_svg_btn.clicked.connect(lambda: self.export_plot('svg'))

    def on_chart_type_changed(self, chart_type):
        """Handle chart type changes by updating UI components."""
        is_scatter_plot = chart_type == "Scatter Plot"
        supports_agg = chart_type in ("Line Chart", "Bar Chart", "Area Chart")
        supports_color_by = chart_type in (
            "Line Chart", "Bar Chart", "Scatter Plot", "Histogram",
            "Box Plot", "Violin Plot", "KDE Plot", "Area Chart",
        )

        self.x_axis_combo.setEnabled(True)
        self.y_axis_combo.setEnabled(True)

        # Series list for multi-series selection (not used by scatter plots)
        self.series_list.setEnabled(not is_scatter_plot)

        # Color-by adds a categorical grouping dimension
        self.color_by_combo.setEnabled(supports_color_by)

        # Aggregation for charts that plot y vs categorical/grouped x
        self.agg_combo.setEnabled(supports_agg)

        # Schedule update
        self.schedule_update()

    def on_color_theme_changed(self, theme):
        """Handle color theme selection."""
        self.color_button.setEnabled(theme == "Custom")
        self.color_map = theme.lower() if theme != "Default" and theme != "Custom" else None
        self.schedule_update()

    def choose_custom_color(self):
        """Open color dialog for custom color selection."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_color = (color.red()/255, color.green()/255, color.blue()/255)
            self.schedule_update()

    def schedule_update(self):
        """Schedule a visualization update with a delay to prevent rapid updates."""
        self.update_timer.start(300)  # 300ms delay

    def on_data_loaded(self, df):
        """Handle when new data is loaded."""
        if df is None or df.empty:
            self.x_axis_combo.clear()
            self.y_axis_combo.clear()
            self.color_by_combo.clear()
            self.series_list.clear()
            self.x_axis_combo.setEnabled(False)
            self.y_axis_combo.setEnabled(False)
            self.color_by_combo.setEnabled(False)
            return

        # Get all columns
        all_columns = df.columns.tolist()
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        self.color_by_combo.clear()
        self.series_list.clear()

        # Add "None" option to dropdowns
        self.x_axis_combo.addItem("None")
        self.y_axis_combo.addItem("None")
        self.color_by_combo.addItem("None")

        # For X-axis, offer all columns for categorical options
        self.x_axis_combo.addItems(all_columns)

        # For Y-axis, only offer numeric columns
        self.y_axis_combo.addItems(numeric_columns)

        # For Color By, offer all columns
        self.color_by_combo.addItems(all_columns)

        # Add numeric columns to the series list for multi-series selection
        self.series_list.addItems(numeric_columns)

        if len(numeric_columns) >= 2:
            self.x_axis_combo.setCurrentIndex(1)  # Skip "None"
            self.y_axis_combo.setCurrentIndex(2)  # Skip "None" and first option

        self.placeholder.setVisible(False)
        self.canvas.setVisible(True)

        # Apply correct enabled states for the current chart type
        self.on_chart_type_changed(self.chart_combo.currentText())

    def on_series_selection_changed(self):
        """Handle changes in selected series."""
        self.selected_series = [item.text() for item in self.series_list.selectedItems()]
        self.schedule_update()

    def export_plot(self, format_type):
        """Export the plot to a file."""
        if self.data_manager.data is None:
            return

        chart_title = self.title_edit.text() or "chart"
        filename = f"{chart_title.replace(' ', '_')}.{format_type}"

        default_dir = ""
        if self.workspace_path:
            default_dir = os.path.join(self.workspace_path, "graphs", filename)
        else:
            default_dir = filename

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {format_type.upper()} File",
            default_dir,
            f"{format_type.upper()} Files (*.{format_type})"
        )

        if file_path:
            try:
                self.figure.savefig(file_path, format=format_type, dpi=300, bbox_inches='tight')
                print(f"Plot saved to {file_path}")
            except Exception as e:
                print(f"Error saving plot: {str(e)}")

    def set_workspace_path(self, workspace_path):
        """Set the active workspace path."""
        self.workspace_path = workspace_path

    def _get_series_colors(self, n):
        """Return a list of n colors based on the current color theme."""
        if self.color_combo.currentText() == "Custom" and self.custom_color:
            return [self.custom_color] * n
        if self.color_map:
            cmap = plt.cm.get_cmap(self.color_map)
            return [cmap(i / max(n - 1, 1)) for i in range(n)]
        # Fall back to matplotlib default color cycle
        return [f'C{i}' for i in range(n)]

    def _get_single_color(self):
        """Return a single color based on the current color theme, or None for default."""
        if self.color_combo.currentText() == "Custom" and self.custom_color:
            return self.custom_color
        if self.color_map:
            cmap = plt.cm.get_cmap(self.color_map)
            return cmap(0.5)
        return None

    def _apply_aggregation(self, df, x_col, value_cols):
        """Group df by x_col and aggregate value_cols.

        Returns (grouped_df, x_values) or (df, x_values) if no aggregation.
        """
        agg_method = self.agg_combo.currentText()
        if agg_method == "None" or not x_col:
            return df, df[x_col] if x_col else df.index

        agg_map = {
            "Mean": "mean", "Sum": "sum", "Count": "count",
            "Median": "median", "Min": "min", "Max": "max",
        }
        func = agg_map.get(agg_method, "mean")
        grouped = df.groupby(x_col, sort=True)[value_cols].agg(func).reset_index()
        return grouped, grouped[x_col]

    def _on_auto_limits_changed(self, state):
        """Toggle manual axis limit inputs."""
        manual = not self.auto_limits_check.isChecked()
        self.x_min_spin.setEnabled(manual)
        self.x_max_spin.setEnabled(manual)
        self.y_min_spin.setEnabled(manual)
        self.y_max_spin.setEnabled(manual)
        self.schedule_update()

    def _apply_axis_scales(self, ax, chart_type):
        """Apply log/linear scale settings and manual limits to axes."""
        # Scale doesn't apply to pie charts
        if chart_type == "Pie Chart":
            return

        if self.x_scale_combo.currentText() == "Log":
            ax.set_xscale('log')
        if self.y_scale_combo.currentText() == "Log":
            ax.set_yscale('log')

        # Apply manual axis limits
        if not self.auto_limits_check.isChecked():
            x_min = self.x_min_spin.value()
            x_max = self.x_max_spin.value()
            y_min = self.y_min_spin.value()
            y_max = self.y_max_spin.value()
            if x_min < x_max:
                ax.set_xlim(x_min, x_max)
            if y_min < y_max:
                ax.set_ylim(y_min, y_max)

    def _add_trend_line(self, ax, x_data, y_data):
        """Add a trend line and optional confidence interval to the axes."""
        trend_type = self.trend_combo.currentText()
        if trend_type == "None":
            return

        try:
            # Convert to numpy arrays and drop NaN
            x_arr = np.asarray(x_data, dtype=float)
            y_arr = np.asarray(y_data, dtype=float)
            mask = np.isfinite(x_arr) & np.isfinite(y_arr)
            x_arr = x_arr[mask]
            y_arr = y_arr[mask]
            if len(x_arr) < 2:
                return

            x_sorted = np.sort(x_arr)
            x_line = np.linspace(x_sorted[0], x_sorted[-1], 200)

            ci_level_map = {"90%": 0.90, "95%": 0.95, "99%": 0.99}
            ci_level = ci_level_map.get(self.ci_combo.currentText(), 0.95)

            if trend_type == "Linear":
                coeffs = np.polyfit(x_arr, y_arr, 1)
                poly = np.poly1d(coeffs)
                y_line = poly(x_line)

                if self.show_equation_check.isChecked():
                    y_pred = poly(x_arr)
                    ss_res = np.sum((y_arr - y_pred) ** 2)
                    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
                    r_sq = 1 - ss_res / ss_tot if ss_tot != 0 else 0
                    eq = f"y = {coeffs[0]:.4g}x + {coeffs[1]:.4g}\nR² = {r_sq:.4f}"
                    ax.annotate(eq, xy=(0.05, 0.95), xycoords='axes fraction',
                                fontsize=8, verticalalignment='top',
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.7))

                ax.plot(x_line, y_line, '--', color='red', linewidth=1.5,
                        label='Linear Fit', zorder=10)

                if self.confidence_check.isChecked():
                    self._add_confidence_band(ax, x_arr, y_arr, x_line, y_line, 1, ci_level)

            elif trend_type.startswith("Polynomial"):
                degree = int(trend_type.split("(")[1].rstrip(")"))
                coeffs = np.polyfit(x_arr, y_arr, degree)
                poly = np.poly1d(coeffs)
                y_line = poly(x_line)

                if self.show_equation_check.isChecked():
                    y_pred = poly(x_arr)
                    ss_res = np.sum((y_arr - y_pred) ** 2)
                    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
                    r_sq = 1 - ss_res / ss_tot if ss_tot != 0 else 0
                    ax.annotate(f"Poly({degree}) R² = {r_sq:.4f}",
                                xy=(0.05, 0.95), xycoords='axes fraction',
                                fontsize=8, verticalalignment='top',
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.7))

                ax.plot(x_line, y_line, '--', color='red', linewidth=1.5,
                        label=f'Poly({degree}) Fit', zorder=10)

                if self.confidence_check.isChecked():
                    self._add_confidence_band(ax, x_arr, y_arr, x_line, y_line, degree, ci_level)

            elif trend_type == "LOWESS":
                try:
                    import statsmodels.api as sm
                    lowess = sm.nonparametric.lowess(y_arr, x_arr, frac=0.3)
                    ax.plot(lowess[:, 0], lowess[:, 1], '--', color='red',
                            linewidth=1.5, label='LOWESS', zorder=10)
                except ImportError:
                    # Fall back to simple moving average if statsmodels not available
                    window = max(len(x_arr) // 10, 3)
                    sorted_idx = np.argsort(x_arr)
                    x_s = x_arr[sorted_idx]
                    y_s = y_arr[sorted_idx]
                    y_ma = pd.Series(y_s).rolling(window=window, center=True, min_periods=1).mean()
                    ax.plot(x_s, y_ma, '--', color='red', linewidth=1.5,
                            label='Smoothed', zorder=10)

            elif trend_type == "Moving Average":
                window = max(len(x_arr) // 10, 3)
                sorted_idx = np.argsort(x_arr)
                x_s = x_arr[sorted_idx]
                y_s = y_arr[sorted_idx]
                y_ma = pd.Series(y_s).rolling(window=window, center=True, min_periods=1).mean()
                ax.plot(x_s, y_ma, '--', color='red', linewidth=1.5,
                        label='Moving Avg', zorder=10)

        except Exception:
            pass  # Silently skip if trend line fails

    def _add_confidence_band(self, ax, x_arr, y_arr, x_line, y_line, degree, ci_level):
        """Add a confidence interval band around a polynomial fit."""
        n = len(x_arr)
        if n <= degree + 1:
            return

        poly = np.poly1d(np.polyfit(x_arr, y_arr, degree))
        y_pred = poly(x_arr)
        residuals = y_arr - y_pred
        mse = np.sum(residuals ** 2) / (n - degree - 1)

        # Build design matrix for prediction intervals
        t_val = stats.t.ppf((1 + ci_level) / 2, n - degree - 1)

        # Simple approach: use standard error of the estimate
        se = np.sqrt(mse)
        y_upper = y_line + t_val * se
        y_lower = y_line - t_val * se

        ax.fill_between(x_line, y_lower, y_upper, alpha=0.15, color='red',
                        label=f'{int(ci_level*100)}% CI')

    def update_visualization(self):
        """Update the visualization with current settings."""
        if self.data_manager.data is None:
            return

        # Clear the figure
        self.figure.clear()

        # Get the data
        df = self.data_manager.data
        x_col = self.x_axis_combo.currentText()
        y_col = self.y_axis_combo.currentText()
        color_by = self.color_by_combo.currentText()

        # Handle "None" selection
        if x_col == "None":
            x_col = None
        if y_col == "None":
            y_col = None
        if color_by == "None":
            color_by = None

        # Get selected series for multi-series plots
        chart_type = self.chart_combo.currentText()
        if chart_type == "Scatter Plot":
            selected_series = []
        else:
            selected_series = self.selected_series
            # Fall back to Y-axis selection when no series are selected
            if not selected_series and y_col:
                selected_series = [y_col]

        # Skip if insufficient data to plot
        if chart_type == "Scatter Plot":
            if not x_col or not y_col:
                self.placeholder.setText("Please select X and Y axes")
                self.placeholder.setVisible(True)
                self.canvas.setVisible(False)
                return
        elif not selected_series and chart_type != "Heatmap":
            self.placeholder.setText("Please select a Y-Axis variable or data series")
            self.placeholder.setVisible(True)
            self.canvas.setVisible(False)
            return

        self.placeholder.setVisible(False)
        self.canvas.setVisible(True)

        # Get alpha (transparency) value
        alpha = self.alpha_slider.value() / 100.0

        # Set the style
        plt.style.use(self.style_combo.currentText())

        # Create subplot
        ax = self.figure.add_subplot(111)
        ax.set_axisbelow(True)  # Put grid behind plot elements

        try:
            # ----- helpers for color-by grouping -----
            categories = None
            cat_colors = None
            if color_by and chart_type != "Scatter Plot":
                categories = df[color_by].dropna().unique()
                cat_colors = self._get_series_colors(len(categories))

            if chart_type == "Line Chart":
                if color_by and categories is not None and len(selected_series) == 1:
                    # One line per category of the color-by column
                    series = selected_series[0]
                    agg_method = self.agg_combo.currentText()
                    for j, cat in enumerate(categories):
                        sub = df[df[color_by] == cat]
                        if agg_method != "None" and x_col:
                            sub, x_data = self._apply_aggregation(sub, x_col, [series])
                        else:
                            if x_col and (pd.api.types.is_numeric_dtype(sub[x_col])
                                          or pd.api.types.is_datetime64_any_dtype(sub[x_col])):
                                sub = sub.sort_values(by=x_col)
                            x_data = sub[x_col] if x_col else sub.index
                        kwargs = dict(alpha=alpha, label=str(cat), color=cat_colors[j])
                        if len(sub) <= 50:
                            kwargs['marker'] = 'o'
                        ax.plot(x_data, sub[series], **kwargs)
                else:
                    plot_df, x_data = self._apply_aggregation(df, x_col, selected_series)
                    if x_col and (pd.api.types.is_numeric_dtype(plot_df[x_col])
                                  or pd.api.types.is_datetime64_any_dtype(plot_df[x_col])):
                        plot_df = plot_df.sort_values(by=x_col)
                        x_data = plot_df[x_col]
                    colors = self._get_series_colors(len(selected_series))
                    use_markers = len(plot_df) <= 50
                    for i, series in enumerate(selected_series):
                        kwargs = dict(alpha=alpha, label=series, color=colors[i])
                        if use_markers:
                            kwargs['marker'] = 'o'
                        ax.plot(x_data if x_col else plot_df.index, plot_df[series], **kwargs)

                if x_col and not pd.api.types.is_numeric_dtype(df[x_col]):
                    ax.tick_params(axis='x', rotation=45)
                    for label in ax.get_xticklabels():
                        label.set_ha('right')

            elif chart_type == "Bar Chart":
                if color_by and categories is not None and len(selected_series) == 1:
                    series = selected_series[0]
                    agg_method = self.agg_combo.currentText()
                    n_cats = len(categories)
                    # Build a grouped frame: one aggregated column per category
                    group_data = {}
                    for cat in categories:
                        sub = df[df[color_by] == cat]
                        if agg_method != "None" and x_col:
                            sub, _ = self._apply_aggregation(sub, x_col, [series])
                            group_data[cat] = sub.set_index(x_col)[series]
                        elif x_col:
                            group_data[cat] = sub.groupby(x_col)[series].mean()
                        else:
                            group_data[cat] = sub[series].values
                    grouped = pd.DataFrame(group_data)
                    x_positions = np.arange(len(grouped))
                    width = 0.8 / n_cats
                    for j, cat in enumerate(categories):
                        offset = j - n_cats / 2 + 0.5
                        ax.bar(x_positions + offset * width, grouped[cat], width,
                               alpha=alpha, label=str(cat), color=cat_colors[j])
                    ax.set_xticks(x_positions)
                    tick_labels = [str(v) for v in grouped.index]
                    if len(tick_labels) > 20:
                        step = max(1, len(tick_labels) // 20)
                        ax.set_xticks(x_positions[::step])
                        ax.set_xticklabels(tick_labels[::step], rotation=45, ha='right')
                    else:
                        ax.set_xticklabels(tick_labels, rotation=45, ha='right')
                else:
                    plot_df, x_data = self._apply_aggregation(df, x_col, selected_series)
                    colors = self._get_series_colors(len(selected_series))
                    x_positions = np.arange(len(plot_df))
                    width = 0.8 / len(selected_series)
                    for i, series in enumerate(selected_series):
                        offset = i - len(selected_series) / 2 + 0.5
                        ax.bar(x_positions + offset * width, plot_df[series], width,
                               alpha=alpha, label=series, color=colors[i])
                    ax.set_xticks(x_positions)
                    tick_labels = plot_df[x_col].astype(str) if x_col else plot_df.index.astype(str)
                    if len(tick_labels) > 20:
                        step = max(1, len(tick_labels) // 20)
                        ax.set_xticks(x_positions[::step])
                        tl = tick_labels.iloc[::step] if hasattr(tick_labels, 'iloc') else tick_labels[::step]
                        ax.set_xticklabels(tl, rotation=45, ha='right')
                    else:
                        ax.set_xticklabels(tick_labels, rotation=45, ha='right')

            elif chart_type == "Scatter Plot":
                marker_size = self.marker_size.value()
                color = self._get_single_color()

                if color_by and pd.api.types.is_numeric_dtype(df[color_by]):
                    scatter = ax.scatter(
                        df[x_col], df[y_col],
                        c=df[color_by], alpha=alpha,
                        s=marker_size * 10,
                        cmap=self.color_map or 'viridis'
                    )
                    cbar = self.figure.colorbar(scatter, ax=ax)
                    cbar.set_label(color_by)
                elif color_by:
                    sc_cats = df[color_by].dropna().unique()
                    sc_colors = self._get_series_colors(len(sc_cats))
                    for j, category in enumerate(sc_cats):
                        mask = df[color_by] == category
                        ax.scatter(
                            df[x_col][mask], df[y_col][mask],
                            alpha=alpha, s=marker_size * 10,
                            label=str(category), color=sc_colors[j]
                        )
                else:
                    ax.scatter(df[x_col], df[y_col], alpha=alpha,
                               s=marker_size * 10, color=color)

            elif chart_type == "Histogram":
                bins = self.bins_spinbox.value()
                if color_by and categories is not None and len(selected_series) == 1:
                    series = selected_series[0]
                    for j, cat in enumerate(categories):
                        sub = df[df[color_by] == cat][series].dropna()
                        ax.hist(sub, bins=bins, alpha=alpha, density=True,
                                label=str(cat), color=cat_colors[j])
                else:
                    colors = self._get_series_colors(len(selected_series))
                    for i, series in enumerate(selected_series):
                        series_clean = df[series].dropna()
                        ax.hist(series_clean, bins=bins, alpha=alpha, density=True,
                                label=series, color=colors[i])
                        if len(series_clean) > 1:
                            density = stats.gaussian_kde(series_clean)
                            xs = np.linspace(series_clean.min(), series_clean.max(), 200)
                            ax.plot(xs, density(xs), label=f'{series} KDE',
                                    color=colors[i], linestyle='--')
                ax.set_ylabel('Density')

            elif chart_type == "Box Plot":
                if color_by and categories is not None and len(selected_series) == 1:
                    series = selected_series[0]
                    plot_data = df[[series, color_by]].dropna()
                    plot_data[color_by] = plot_data[color_by].astype(str)
                    palette = {str(c): cat_colors[j] for j, c in enumerate(categories)}
                    sns.boxplot(x=color_by, y=series, data=plot_data, ax=ax,
                                palette=palette)
                    for patch in ax.patches:
                        patch.set_alpha(alpha)
                else:
                    data = []
                    labels = []
                    for series in selected_series:
                        series_data = df[series].dropna()
                        if len(series_data) > 0:
                            data.append(series_data.values)
                            labels.append(series)
                    if data:
                        bp = ax.boxplot(data, labels=labels, patch_artist=True)
                        colors = self._get_series_colors(len(data))
                        for i, box in enumerate(bp['boxes']):
                            box.set_facecolor(colors[i])
                            box.set_alpha(alpha)
                        for median in bp['medians']:
                            median.set_color('black')

            elif chart_type == "Violin Plot":
                if color_by and categories is not None and len(selected_series) == 1:
                    series = selected_series[0]
                    plot_data = df[[series, color_by]].dropna()
                    plot_data[color_by] = plot_data[color_by].astype(str)
                    palette = {str(c): cat_colors[j] for j, c in enumerate(categories)}
                    sns.violinplot(x=color_by, y=series, data=plot_data, ax=ax,
                                   alpha=alpha, palette=palette)
                else:
                    plot_data = pd.DataFrame()
                    for series in selected_series:
                        temp_df = pd.DataFrame({
                            'value': df[series].dropna(),
                            'variable': series
                        })
                        plot_data = pd.concat([plot_data, temp_df])
                    palette = self.color_map if self.color_map else None
                    sns.violinplot(x='variable', y='value', data=plot_data, ax=ax,
                                   alpha=alpha, palette=palette)

            elif chart_type == "Heatmap":
                if selected_series and len(selected_series) > 1:
                    corr = df[selected_series].corr()
                elif selected_series and len(selected_series) == 1:
                    numeric_df = df.select_dtypes(include=[np.number])
                    corr = numeric_df.corr()[[selected_series[0]]].sort_values(
                        by=selected_series[0], ascending=False)
                else:
                    corr = df.select_dtypes(include=[np.number]).corr()

                sns.heatmap(
                    corr, annot=True,
                    cmap=self.color_map or 'coolwarm',
                    ax=ax, center=0, vmin=-1, vmax=1
                )

            elif chart_type == "KDE Plot":
                if color_by and categories is not None and len(selected_series) == 1:
                    series = selected_series[0]
                    for j, cat in enumerate(categories):
                        sub = df[df[color_by] == cat]
                        sns.kdeplot(data=sub, x=series, ax=ax, alpha=alpha,
                                    fill=True, label=str(cat), color=cat_colors[j])
                else:
                    colors = self._get_series_colors(len(selected_series))
                    for i, series in enumerate(selected_series):
                        sns.kdeplot(
                            data=df, x=series, ax=ax, alpha=alpha,
                            fill=True, label=series, color=colors[i]
                        )

            elif chart_type == "Pie Chart":
                if len(df) > 10:
                    data = df.iloc[:10]
                    title_suffix = " (first 10 entries)"
                else:
                    data = df
                    title_suffix = ""

                if not x_col:
                    labels = data.index
                else:
                    labels = data[x_col]

                if len(selected_series) > 0:
                    values = data[selected_series[0]]
                    colors = self._get_series_colors(len(values))
                    ax.pie(values, labels=labels, autopct='%1.1f%%',
                           alpha=alpha, startangle=90, colors=colors)
                    ax.axis('equal')

            elif chart_type == "Area Chart":
                if color_by and categories is not None and len(selected_series) == 1:
                    series = selected_series[0]
                    agg_method = self.agg_combo.currentText()
                    for j, cat in enumerate(categories):
                        sub = df[df[color_by] == cat]
                        if agg_method != "None" and x_col:
                            sub, x_data = self._apply_aggregation(sub, x_col, [series])
                        else:
                            if x_col and (pd.api.types.is_numeric_dtype(sub[x_col])
                                          or pd.api.types.is_datetime64_any_dtype(sub[x_col])):
                                sub = sub.sort_values(by=x_col)
                            x_data = sub[x_col] if x_col else sub.index
                        ax.fill_between(x_data, sub[series], alpha=alpha,
                                        label=str(cat), color=cat_colors[j])
                else:
                    plot_df, x_data = self._apply_aggregation(df, x_col, selected_series)
                    if x_col and (pd.api.types.is_numeric_dtype(plot_df[x_col])
                                  or pd.api.types.is_datetime64_any_dtype(plot_df[x_col])):
                        plot_df = plot_df.sort_values(by=x_col)
                        x_data = plot_df[x_col]
                    colors = self._get_series_colors(len(selected_series))
                    for i, series in enumerate(selected_series):
                        ax.fill_between(x_data if x_col else plot_df.index,
                                        plot_df[series], alpha=alpha,
                                        label=series, color=colors[i])

            # Apply trend line for applicable chart types
            if chart_type in ("Scatter Plot", "Line Chart"):
                if chart_type == "Scatter Plot" and x_col and y_col:
                    x_numeric = pd.to_numeric(df[x_col], errors='coerce')
                    y_numeric = pd.to_numeric(df[y_col], errors='coerce')
                    self._add_trend_line(ax, x_numeric, y_numeric)
                elif chart_type == "Line Chart" and x_col and len(selected_series) == 1:
                    x_numeric = pd.to_numeric(df[x_col], errors='coerce')
                    y_numeric = pd.to_numeric(df[selected_series[0]], errors='coerce')
                    self._add_trend_line(ax, x_numeric, y_numeric)

            # Apply axis scales and manual limits
            self._apply_axis_scales(ax, chart_type)

            # Font size
            font_size = self.font_size_spin.value()

            # Set title
            title = self.title_edit.text()
            if not title:
                if chart_type == "Pie Chart":
                    title = f"{chart_type}: {selected_series[0] if selected_series else ''}"
                elif chart_type == "Scatter Plot":
                    title = f"{chart_type}: {x_col} vs {y_col}"
                elif not x_col:
                    title = f"{chart_type}: {', '.join(selected_series)}"
                else:
                    title = f"{chart_type}: {x_col} vs {', '.join(selected_series)}"
                if color_by and chart_type != "Scatter Plot":
                    title += f" (by {color_by})"

            if chart_type == "Pie Chart" and len(df) > 10:
                title += title_suffix

            ax.set_title(title, fontsize=font_size + 2)

            # Set labels - use custom labels if provided, otherwise auto
            x_custom = self.x_label_edit.text().strip()
            y_custom = self.y_label_edit.text().strip()

            if chart_type == "Scatter Plot":
                ax.set_xlabel(x_custom or x_col, fontsize=font_size)
                ax.set_ylabel(y_custom or y_col, fontsize=font_size)
            elif chart_type != "Pie Chart":
                if x_col:
                    ax.set_xlabel(x_custom or x_col, fontsize=font_size)
                elif chart_type not in ["Box Plot", "Violin Plot"]:
                    ax.set_xlabel(x_custom or "Index", fontsize=font_size)

                if chart_type not in ["Histogram", "KDE Plot"]:
                    if len(selected_series) == 1:
                        ax.set_ylabel(y_custom or selected_series[0], fontsize=font_size)
                    else:
                        ax.set_ylabel(y_custom or "Value", fontsize=font_size)
                elif y_custom:
                    ax.set_ylabel(y_custom, fontsize=font_size)

            # Apply tick label font size and rotation
            ax.tick_params(axis='both', labelsize=font_size - 1)
            x_rotation = self.x_tick_rotation_spin.value()
            if x_rotation > 0:
                for label in ax.get_xticklabels():
                    label.set_rotation(x_rotation)
                    label.set_ha('right')

            # Add data labels for bar and scatter charts
            if self.data_labels_check.isChecked():
                if chart_type == "Bar Chart":
                    for container in ax.containers:
                        ax.bar_label(container, fmt='%.1f', fontsize=max(6, font_size - 2))
                elif chart_type == "Scatter Plot" and x_col and y_col:
                    for i in range(min(len(df), 50)):  # Limit to 50 labels
                        ax.annotate(f"({df[x_col].iloc[i]:.1f}, {df[y_col].iloc[i]:.1f})",
                                    (df[x_col].iloc[i], df[y_col].iloc[i]),
                                    fontsize=max(5, font_size - 3), alpha=0.7,
                                    textcoords="offset points", xytext=(4, 4))

            # Configure grid
            ax.grid(self.grid_check.isChecked())

            # Configure legend
            if self.legend_check.isChecked() and chart_type not in ["Heatmap"]:
                handles, labels = ax.get_legend_handles_labels()
                if len(handles) > 0:
                    ax.legend(loc='best', fontsize=max(6, font_size - 1))

            # Adjust layout to prevent label cutoff
            self.figure.tight_layout()

        except Exception as e:
            # Clear the figure and show error
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"Error: {str(e)}",
                   ha='center', va='center', color='red',
                   transform=ax.transAxes)

        # Redraw the canvas
        self.canvas.draw()
