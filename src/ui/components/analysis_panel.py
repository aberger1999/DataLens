"""
Analysis panel for data analysis operations.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QStackedWidget,
    QGridLayout, QSplitter, QSizePolicy, QStyledItemDelegate
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush
from . import modal
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import matplotlib.pyplot as plt
from ..theme import apply_dark_theme

class AnalysisPanel(QWidget):
    """Panel for data analysis operations."""
    
    def __init__(self, data_manager):
        """Initialize the analysis panel."""
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create a more compact control panel at the top
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        control_layout = QHBoxLayout(control_panel)

        # Column selection with label
        control_layout.addWidget(QLabel("Select Column:"))
        self.column_combo = QComboBox()
        self.column_combo.setMinimumWidth(200)
        control_layout.addWidget(self.column_combo)
        
        control_layout.addSpacing(20)
        
        # View selection buttons
        self.stats_btn = QPushButton("Statistics View")
        self.stats_btn.setCheckable(True)
        self.stats_btn.setChecked(True)

        self.viz_btn = QPushButton("Visualization View")
        self.viz_btn.setCheckable(True)

        self.corr_btn = QPushButton("Correlation Matrix")
        self.corr_btn.setCheckable(True)

        control_layout.addWidget(self.stats_btn)
        control_layout.addWidget(self.viz_btn)
        control_layout.addWidget(self.corr_btn)

        # Add run button
        self.run_btn = QPushButton("Run Analysis")
        self.run_btn.setProperty("cssClass", "primary")
        control_layout.addWidget(self.run_btn)

        main_layout.addWidget(control_panel)

        # Create a stacked widget to switch between statistics and visualization
        self.analysis_stack = QStackedWidget()

        # Create statistics frame with better styling
        self.stats_frame = QFrame()
        stats_layout = QVBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["Statistic", "Value"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        stats_layout.addWidget(self.results_table)

        self.analysis_stack.addWidget(self.stats_frame)

        # --- Page 2: Visualization ---
        self.viz_frame = QFrame()
        viz_layout = QVBoxLayout(self.viz_frame)
        viz_layout.setContentsMargins(0, 0, 0, 0)

        viz_control = QFrame()
        viz_control_layout = QHBoxLayout(viz_control)

        self.viz_type_label = QLabel("Visualization Type:")
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.setMinimumWidth(150)

        viz_control_layout.addWidget(self.viz_type_label)
        viz_control_layout.addWidget(self.viz_type_combo)
        viz_control_layout.addStretch()

        viz_layout.addWidget(viz_control)

        canvas_frame = QFrame()
        canvas_frame.setFrameShape(QFrame.Shape.StyledPanel)
        canvas_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas_layout.addWidget(self.canvas)

        viz_layout.addWidget(canvas_frame)

        self.analysis_stack.addWidget(self.viz_frame)

        # --- Page 3: Correlation Matrix ---
        self.corr_frame = QFrame()
        corr_layout = QVBoxLayout(self.corr_frame)
        corr_layout.setContentsMargins(0, 0, 0, 0)

        self.corr_figure = Figure(figsize=(8, 6), dpi=100)
        self.corr_canvas = FigureCanvas(self.corr_figure)
        self.corr_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        corr_layout.addWidget(self.corr_canvas)

        self.analysis_stack.addWidget(self.corr_frame)

        main_layout.addWidget(self.analysis_stack, 1)

    def setup_connections(self):
        """Setup signal connections."""
        self.run_btn.clicked.connect(self.run_analysis)
        self.data_manager.data_loaded.connect(self.on_data_loaded)
        self.stats_btn.clicked.connect(self.toggle_view)
        self.viz_btn.clicked.connect(self.toggle_view)
        self.corr_btn.clicked.connect(self.toggle_view)
        self.viz_type_combo.currentIndexChanged.connect(self.update_visualization)
        self.column_combo.currentTextChanged.connect(self.on_column_changed)

    def toggle_view(self):
        """Toggle between views."""
        sender = self.sender()
        self.stats_btn.setChecked(sender == self.stats_btn)
        self.viz_btn.setChecked(sender == self.viz_btn)
        self.corr_btn.setChecked(sender == self.corr_btn)

        if sender == self.stats_btn:
            self.analysis_stack.setCurrentIndex(0)
        elif sender == self.viz_btn:
            self.analysis_stack.setCurrentIndex(1)
            self.update_viz_options()
        elif sender == self.corr_btn:
            self.analysis_stack.setCurrentIndex(2)
            self.update_correlation_matrix()

    def update_correlation_matrix(self):
        """Update the correlation matrix heatmap."""
        if self.data_manager.data is None:
            return

        df = self.data_manager.data
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.empty:
            modal.show_warning(self, "Warning", "No numeric columns found for correlation matrix.")
            return

        self.corr_figure.clear()
        ax = self.corr_figure.add_subplot(111)

        # Calculate correlation
        corr = numeric_df.corr()

        # Plot heatmap
        sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax, fmt=".2f")
        ax.set_title("Correlation Matrix")

        apply_dark_theme(self.corr_figure, ax)
        self.corr_canvas.draw()

    def on_data_loaded(self, df):
        """Handle when new data is loaded."""
        # Update column dropdown
        self.column_combo.clear()

        if df is None or df.empty:
            self.run_btn.setEnabled(False)
            return

        self.column_combo.addItems(df.columns)

        # Enable run button
        self.run_btn.setEnabled(True)
        
    def on_column_changed(self, column):
        """Handle column selection change."""
        if self.analysis_stack.currentIndex() == 1:  # Visualization view
            self.update_viz_options()
            
    def update_viz_options(self):
        """Update visualization options based on column data type."""
        if self.data_manager.data is None or not self.column_combo.currentText():
            return
            
        column = self.column_combo.currentText()
        df = self.data_manager.data
        
        self.viz_type_combo.clear()
        
        # Check column data type and add appropriate visualization options
        if pd.api.types.is_numeric_dtype(df[column]):
            self.viz_type_combo.addItems(["Box Plot", "Histogram", "Density Plot"])
        else:
            self.viz_type_combo.addItems(["Bar Chart", "Pie Chart"])
            
        # Update the visualization
        self.update_visualization()
        
    def update_visualization(self):
        """Update the visualization based on selected options."""
        if self.data_manager.data is None or not self.column_combo.currentText():
            return

        column = self.column_combo.currentText()
        df = self.data_manager.data

        if self.viz_type_combo.count() == 0:
            return

        viz_type = self.viz_type_combo.currentText()

        # Clear the figure
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        try:
            if pd.api.types.is_numeric_dtype(df[column]):
                if viz_type == "Box Plot":
                    sns.boxplot(y=df[column], ax=ax)
                    ax.set_title(f"Box Plot of {column}")
                elif viz_type == "Histogram":
                    sns.histplot(df[column], kde=True, ax=ax)
                    ax.set_title(f"Histogram of {column}")
                elif viz_type == "Density Plot":
                    sns.kdeplot(df[column], ax=ax)
                    ax.set_title(f"Density Plot of {column}")
            else:
                # For categorical data
                value_counts = df[column].value_counts()
                if viz_type == "Bar Chart":
                    sns.barplot(x=value_counts.index, y=value_counts.values, ax=ax, palette='viridis')
                    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
                    ax.set_title(f"Bar Chart of {column}")
                elif viz_type == "Pie Chart":
                    ax.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
                    ax.set_title(f"Pie Chart of {column}")

            # Adjust layout and draw
            apply_dark_theme(self.figure, ax)
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            modal.show_error(self, "Error", f"Error creating visualization: {str(e)}")
            
    def update_theme(self, theme_name):
        """Update the panel theme — mostly handled by global stylesheet now."""
        from ..theme import get_colors
        c = get_colors(theme_name)

        if hasattr(self, 'figure'):
            self.figure.patch.set_facecolor(c['bg_secondary'])
            if hasattr(self, 'canvas'):
                self.canvas.draw()

        if hasattr(self, 'corr_figure'):
            self.corr_figure.patch.set_facecolor(c['bg_secondary'])
            if hasattr(self, 'corr_canvas'):
                self.corr_canvas.draw()

    def run_analysis(self):
        """Run the selected analysis on the selected column."""
        if self.data_manager.data is None:
            return
            
        column = self.column_combo.currentText()
        
        if not column:
            return
            
        if self.analysis_stack.currentIndex() == 0:  # Statistics view
            self.run_basic_statistics(column)
        else:  # Visualization view
            self.update_visualization()
            
    def run_basic_statistics(self, column):
        """Run basic statistics on the selected column."""
        df = self.data_manager.data
        
        # Clear previous results
        self.results_table.setRowCount(0)
        
        try:
            # Calculate statistics
            stats = []
            
            # Define all section headers
            section_headers = [
                "Basic Information", 
                "Central Tendency", 
                "Dispersion",
                "Quartiles", 
                "Distribution Shape", 
                "Outlier Boundaries (IQR method)", 
                "Correlations", 
                "Frequency Analysis"
            ]
            
            # Basic count statistics (for all data types)
            stats.append(("Basic Information", ""))
            stats.append(("Count", len(df)))
            stats.append(("Missing Values", df[column].isna().sum()))
            stats.append(("Missing Percentage", f"{df[column].isna().sum() / max(len(df), 1) * 100:.2f}%"))
            stats.append(("Unique Values", df[column].nunique()))
            
            # Numeric statistics
            if pd.api.types.is_numeric_dtype(df[column]):
                # Central tendency
                stats.append(("", ""))  # Empty row as separator
                stats.append(("Central Tendency", ""))
                stats.append(("Mean", f"{df[column].mean():.4f}"))
                stats.append(("Median", f"{df[column].median():.4f}"))
                stats.append(("Mode", f"{df[column].mode().iloc[0] if not df[column].mode().empty else 'N/A'}"))
                
                # Dispersion
                stats.append(("", ""))  # Empty row as separator
                stats.append(("Dispersion", ""))
                stats.append(("Standard Deviation", f"{df[column].std():.4f}"))
                stats.append(("Variance", f"{df[column].var():.4f}"))
                stats.append(("Range", f"{df[column].max() - df[column].min():.4f}"))
                stats.append(("Min", f"{df[column].min():.4f}"))
                stats.append(("Max", f"{df[column].max():.4f}"))
                
                # Quartiles
                stats.append(("", ""))  # Empty row as separator
                stats.append(("Quartiles", ""))
                q1 = df[column].quantile(0.25)
                q3 = df[column].quantile(0.75)
                iqr = q3 - q1
                stats.append(("Q1 (25%)", f"{q1:.4f}"))
                stats.append(("Q2 (50%)", f"{df[column].quantile(0.5):.4f}"))
                stats.append(("Q3 (75%)", f"{q3:.4f}"))
                stats.append(("IQR", f"{iqr:.4f}"))
                
                # Shape
                stats.append(("", ""))  # Empty row as separator
                stats.append(("Distribution Shape", ""))
                stats.append(("Skewness", f"{df[column].skew():.4f}"))
                stats.append(("Kurtosis", f"{df[column].kurtosis():.4f}"))
                
                # Outlier boundaries
                stats.append(("", ""))  # Empty row as separator
                stats.append(("Outlier Boundaries (IQR method)", ""))
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                stats.append(("Lower Bound", f"{lower_bound:.4f}"))
                stats.append(("Upper Bound", f"{upper_bound:.4f}"))
                stats.append(("Potential Outliers", f"{((df[column] < lower_bound) | (df[column] > upper_bound)).sum()}"))
                
                # Correlations
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 1:  # Only if there are other numeric columns
                    stats.append(("", ""))  # Empty row as separator
                    stats.append(("Correlations", ""))
                    for col in numeric_cols:
                        if col != column:
                            corr = df[column].corr(df[col])
                            stats.append((f"Correlation with {col}", f"{corr:.4f}"))
            
            # Categorical statistics
            else:
                # Frequency analysis
                stats.append(("", ""))  # Empty row as separator
                stats.append(("Frequency Analysis", ""))
                value_counts = df[column].value_counts()
                top_n = min(5, len(value_counts))
                
                for i in range(top_n):
                    value = value_counts.index[i]
                    count = value_counts.iloc[i]
                    percentage = count / max(len(df), 1) * 100
                    stats.append((f"Top {i+1}: {value}", f"{count} ({percentage:.2f}%)"))
            
            # Display results with formatting
            self.results_table.setRowCount(len(stats))
            
            # Create a dictionary to track header rows and separator rows
            header_rows = {}
            separator_rows = []
            
            # First pass: populate the table and track header rows
            for i, (key, value) in enumerate(stats):
                item_key = QTableWidgetItem(str(key))
                item_value = QTableWidgetItem(str(value))
                
                # Apply styling based on row type
                if key in section_headers:
                    # Header row
                    header_font = QFont()
                    header_font.setBold(True)
                    item_key.setFont(header_font)
                    item_value.setFont(header_font)

                elif key == "":
                    # Separator row
                    item_key.setFlags(Qt.ItemFlag.NoItemFlags)
                    item_value.setFlags(Qt.ItemFlag.NoItemFlags)

                self.results_table.setItem(i, 0, item_key)
                self.results_table.setItem(i, 1, item_value)

            # Set column widths to prevent text cutoff
            self.results_table.setColumnWidth(0, 250)  # Increase width of first column
            self.results_table.setColumnWidth(1, 200)  # Set width of second column

            # Make the table stretch to fill available space
            self.results_table.horizontalHeader().setStretchLastSection(True)

            # Force a repaint
            self.results_table.viewport().update()

            # Ensure the table takes up the full available space
            self.results_table.setMinimumWidth(self.stats_frame.width())
            self.results_table.setMinimumHeight(self.stats_frame.height() - 20)
            
        except Exception as e:
            modal.show_error(self, "Error", f"Error calculating statistics: {str(e)}") 