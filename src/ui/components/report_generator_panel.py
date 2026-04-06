"""
Report generator panel for creating comprehensive data analysis reports.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QSpinBox,
    QGridLayout, QTabWidget, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem,
    QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt
from . import modal
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import jinja2
from ..theme import apply_dark_theme
import os
import tempfile

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

class ReportGeneratorPanel(QWidget):
    """Panel for generating comprehensive data analysis reports."""
    
    def __init__(self, data_manager):
        """Initialize the report generator panel."""
        super().__init__()
        self.data_manager = data_manager
        self.workspace_path = None
        # Use absolute path relative to project root for template loading
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        template_dir = os.path.join(project_root, "templates")
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )
        self._temp_files = []  # Track temp files for cleanup
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Report Configuration Group
        config_group = QGroupBox("Report Configuration")
        config_layout = QGridLayout(config_group)
        
        # Report title
        title_label = QLabel("Report Title:")
        self.title_edit = QLineEdit("Data Analysis Report")
        config_layout.addWidget(title_label, 0, 0)
        config_layout.addWidget(self.title_edit, 0, 1)
        
        # Report sections selection
        sections_label = QLabel("Include Sections:")
        config_layout.addWidget(sections_label, 1, 0)
        
        # Data Overview section
        self.overview_check = QCheckBox("Data Overview")
        self.overview_check.setChecked(True)
        config_layout.addWidget(self.overview_check, 2, 0)
        
        # Descriptive Statistics section
        self.stats_check = QCheckBox("Descriptive Statistics")
        self.stats_check.setChecked(True)
        config_layout.addWidget(self.stats_check, 2, 1)
        
        # Data Quality section
        self.quality_check = QCheckBox("Data Quality Analysis")
        self.quality_check.setChecked(True)
        config_layout.addWidget(self.quality_check, 3, 0)
        
        # Correlation Analysis section
        self.correlation_check = QCheckBox("Correlation Analysis")
        self.correlation_check.setChecked(True)
        config_layout.addWidget(self.correlation_check, 3, 1)
        
        # Distribution Analysis section
        self.distribution_check = QCheckBox("Distribution Analysis")
        self.distribution_check.setChecked(True)
        config_layout.addWidget(self.distribution_check, 4, 0)
        
        # Time Series Analysis section (if applicable)
        self.timeseries_check = QCheckBox("Time Series Analysis")
        self.timeseries_check.setChecked(False)
        config_layout.addWidget(self.timeseries_check, 4, 1)
        
        # Machine Learning Results section (if model is trained)
        self.ml_results_check = QCheckBox("Machine Learning Results")
        self.ml_results_check.setChecked(False)
        config_layout.addWidget(self.ml_results_check, 5, 0)
        
        # Custom Notes section
        self.custom_notes_check = QCheckBox("Custom Notes")
        self.custom_notes_check.setChecked(True)
        config_layout.addWidget(self.custom_notes_check, 5, 1)
        
        layout.addWidget(config_group)
        
        # Custom Notes Group
        notes_group = QGroupBox("Custom Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter any additional notes or observations here...")
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        
        # Preview Group
        preview_group = QGroupBox("Report Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        preview_layout.addWidget(self.preview_edit)
        
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Generate Preview")
        self.preview_btn.setProperty("cssClass", "primary")
        self.export_pdf_btn = QPushButton("Export as PDF")
        self.export_pdf_btn.setProperty("cssClass", "primary")
        self.export_html_btn = QPushButton("Export as HTML")
        self.export_html_btn.setProperty("cssClass", "primary")
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.export_pdf_btn)
        button_layout.addWidget(self.export_html_btn)
        
        layout.addLayout(button_layout)
        
    def setup_connections(self):
        """Setup signal connections."""
        self.preview_btn.clicked.connect(self.generate_preview)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_html_btn.clicked.connect(self.export_html)
        
    def generate_data_overview(self):
        """Generate data overview section."""
        df = self.data_manager.data
        if df is None:
            return ""
            
        overview = {
            "num_rows": len(df),
            "num_cols": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum() / 1024**2,  # MB
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
            
            # Create correlation heatmap
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
            ax.set_title('Correlation Heatmap')
            apply_dark_theme(fig, ax)
            fig.tight_layout()

            # Save plot to temporary file
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
        
        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
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
            
        # Check for datetime columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            time_series_plots = {}
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:3]
            
            for dt_col in datetime_cols[:1]:  # Use first datetime column
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
        # This would need to be connected to the ML panel's results
        return None
        
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
            }
            
            # Add selected sections
            if self.overview_check.isChecked():
                report_data["overview"] = self.generate_data_overview()
                
            if self.stats_check.isChecked():
                report_data["stats"] = self.generate_descriptive_stats()
                
            if self.quality_check.isChecked():
                report_data["quality"] = self.generate_data_quality()
                
            if self.correlation_check.isChecked():
                report_data["correlation"] = self.generate_correlation_analysis()
                
            if self.distribution_check.isChecked():
                report_data["distributions"] = self.generate_distribution_analysis()
                
            if self.timeseries_check.isChecked():
                report_data["timeseries"] = self.generate_time_series_analysis()
                
            if self.ml_results_check.isChecked():
                report_data["ml_results"] = self.generate_ml_results()
                
            # Generate HTML preview
            template = self.template_env.get_template("report_template.html")
            html_content = template.render(**report_data)
            
            # Update preview
            self.preview_edit.setHtml(html_content)
            
        except Exception as e:
            modal.show_error(self, "Error", f"Error generating preview: {str(e)}")
            
    def export_pdf(self):
        """Export report as PDF."""
        try:
            default_dir = ""
            if self.workspace_path:
                default_dir = os.path.join(self.workspace_path, "reports", "report.pdf")

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save PDF Report",
                default_dir,
                "PDF Files (*.pdf)"
            )

            if file_path:
                if not WEASYPRINT_AVAILABLE:
                    modal.show_warning(
                        self,
                        "Feature Not Available",
                        "PDF export requires WeasyPrint which is not available on this system.\n\n"
                        "Please use 'Export as HTML' instead, or install WeasyPrint with:\n"
                        "pip install weasyprint\n\n"
                        "Note: WeasyPrint requires additional system libraries on Windows."
                    )
                    return

                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'

                html_content = self.preview_edit.toHtml()

                temp_html = 'temp_report.html'
                with open(temp_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                HTML(temp_html).write_pdf(file_path)

                os.remove(temp_html)

                modal.show_info(
                    self,
                    "Success",
                    f"Report exported successfully to {file_path}"
                )

        except Exception as e:
            modal.show_error(
                self,
                "Error",
                f"Error exporting PDF: {str(e)}"
            )
            
    def export_html(self):
        """Export report as HTML."""
        try:
            default_dir = ""
            if self.workspace_path:
                default_dir = os.path.join(self.workspace_path, "reports", "report.html")

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save HTML Report",
                default_dir,
                "HTML Files (*.html)"
            )

            if file_path:
                if not file_path.endswith('.html'):
                    file_path += '.html'

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.preview_edit.toHtml())

                modal.show_info(
                    self,
                    "Success",
                    f"Report exported successfully to {file_path}"
                )

        except Exception as e:
            modal.show_error(
                self,
                "Error",
                f"Error exporting HTML: {str(e)}"
            )

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