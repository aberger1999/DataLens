"""
Workspace view containing all data analysis tools.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSplitter, QTabWidget, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import os
from . import modal
from .data_preview import DataPreviewPanel
from .analysis_panel import AnalysisPanel
from .visualization_panel import VisualizationPanel
from .preprocessing_panel import PreprocessingPanel
from .feature_engineering_panel import FeatureEngineeringPanel
from .machine_learning_panel import MachineLearningPanel
from .report_generator_panel import ReportGeneratorPanel
from .dataset_manager_panel import DatasetManagerDialog
from ..data_manager import DataManager
from ..theme import get_colors, RADIUS_MD, RADIUS_LG

class WorkspaceView(QWidget):
    """View for working within a specific workspace."""

    back_to_home = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.workspace_id = None
        self.workspace_path = None
        self.workspace_name = ""
        self.has_unsaved_changes = False
        self.dataset_manager_dialog = None
        # Track which tab panels need a data refresh
        self._dirty_tabs = set()
        self._latest_df = None
        self.init_ui()
        self.setup_connections()

    def update_theme(self, theme_name):
        c = get_colors(theme_name)

        # Header bar
        self.header_frame.setStyleSheet(f"""
            QFrame#headerFrame {{
                background-color: {c['bg_secondary']};
                border-bottom: 1px solid {c['border']};
            }}
        """)

        # Update child panels
        if hasattr(self, 'analysis_panel'):
            self.analysis_panel.update_theme(theme_name)

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(10)

        self.back_btn = QPushButton("← Back")
        self.back_btn.setProperty("cssClass", "ghost")
        self.back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(self.back_btn)

        # Vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        header_layout.addWidget(sep)

        self.workspace_label = QLabel()
        workspace_font = QFont()
        workspace_font.setPointSize(12)
        workspace_font.setBold(True)
        self.workspace_label.setFont(workspace_font)
        header_layout.addWidget(self.workspace_label)

        header_layout.addStretch()

        # Action button group
        self.dataset_manager_btn = QPushButton("Dataset Manager")
        self.dataset_manager_btn.setProperty("cssClass", "outline")
        self.dataset_manager_btn.clicked.connect(self.show_dataset_manager)
        header_layout.addWidget(self.dataset_manager_btn)

        # Discard Changes button (left of Save)
        self.discard_btn = QPushButton("Discard Changes")
        self.discard_btn.setEnabled(False)
        self.discard_btn.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.discard_btn.clicked.connect(self.discard_changes)
        header_layout.addWidget(self.discard_btn)
        self._apply_discard_btn_style()

        self.save_btn = QPushButton("Save Workspace")
        self.save_btn.setProperty("cssClass", "primary")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_workspace)
        header_layout.addWidget(self.save_btn)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setProperty("cssClass", "primary")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.save_data)
        header_layout.addWidget(self.export_btn)

        layout.addWidget(self.header_frame)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(8, 8, 8, 8)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(6)

        self.data_preview = DataPreviewPanel(self.data_manager)
        self.data_preview.setMinimumWidth(200)
        main_splitter.addWidget(self.data_preview)

        self.tabs = QTabWidget()

        self.preprocessing_panel = PreprocessingPanel(self.data_manager)

        # Apply initial theme (will be updated by MainWindow)
        self.update_theme("dark")
        self.tabs.addTab(self.preprocessing_panel, "Preprocessing")

        self.analysis_panel = AnalysisPanel(self.data_manager)
        self.tabs.addTab(self.analysis_panel, "Analysis")

        self.visualization_panel = VisualizationPanel(self.data_manager)
        self.tabs.addTab(self.visualization_panel, "Visualization")

        self.feature_engineering_panel = FeatureEngineeringPanel(self.data_manager)
        self.tabs.addTab(self.feature_engineering_panel, "Feature Engineering")

        self.machine_learning_panel = MachineLearningPanel(self.data_manager)
        self.tabs.addTab(self.machine_learning_panel, "Machine Learning")

        self.report_generator_panel = ReportGeneratorPanel(self.data_manager)
        self.tabs.addTab(self.report_generator_panel, "Reports")

        self.tabs.setMinimumWidth(400)
        main_splitter.addWidget(self.tabs)
        main_splitter.setSizes([350, 850])
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        content_layout.addWidget(main_splitter)
        layout.addLayout(content_layout)
        
    def setup_connections(self):
        """Setup signal connections."""
        self.data_manager.data_error.connect(self.show_error)
        self.data_manager.data_loaded.connect(self.on_data_loaded)

        # Disconnect panels from data_loaded so workspace_view can manage
        # them lazily (only update the visible tab, defer the rest).
        # Each panel connected in its own __init__; disconnect them here.
        self.data_manager.data_loaded.disconnect(self.data_preview.on_data_loaded)
        self.data_manager.data_loaded.disconnect(self.preprocessing_panel.on_data_loaded)
        self.data_manager.data_loaded.disconnect(self.analysis_panel.on_data_loaded)
        self.data_manager.data_loaded.disconnect(self.visualization_panel.on_data_loaded)
        self.data_manager.data_loaded.disconnect(self.feature_engineering_panel.on_data_loaded)
        self.data_manager.data_loaded.disconnect(self.machine_learning_panel.on_data_loaded)

        self.preprocessing_panel.data_modified.connect(self.mark_unsaved_changes)
        self.feature_engineering_panel.data_modified.connect(self.mark_unsaved_changes)

        # Lazy-load: update deferred panels when the user switches tabs
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.back_btn.clicked.disconnect()
        self.back_btn.clicked.connect(self.on_back_clicked)

    def set_workspace(self, workspace_id, workspace_path, workspace_name):
        """Set the active workspace."""
        self.workspace_id = workspace_id
        self.workspace_path = workspace_path
        self.workspace_name = workspace_name
        self.has_unsaved_changes = False

        self.workspace_label.setText(workspace_name)

        # Clear existing data from previous workspace
        self.data_manager.clear_data()

        self.data_manager.set_workspace_path(workspace_path)
        self.data_manager.set_workspace_name(workspace_name)
        self.visualization_panel.set_workspace_path(workspace_path)
        self.report_generator_panel.set_workspace_path(workspace_path)

        # Try to load existing workspace data
        self.data_manager.load_workspace_data()
        
    def save_data(self):
        """Save current data."""
        if self.data_manager.data is None:
            return
            
        default_path = ""
        if self.workspace_path:
            default_path = os.path.join(self.workspace_path, "data", "data.csv")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Data File",
            default_path,
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.data_manager.data.to_csv(file_path, index=False)
                elif file_path.endswith('.xlsx'):
                    self.data_manager.data.to_excel(file_path, index=False)
                    
                modal.show_info(
                    self,
                    "Success",
                    f"Data saved successfully to {file_path}"
                )
            except Exception as e:
                modal.show_error(
                    self,
                    "Error",
                    f"Error saving data: {str(e)}"
                )
    
    def load_dataset_from_manager(self, file_path):
        """Load a dataset selected from the dataset manager."""
        if self.has_unsaved_changes:
            result = modal.show_question_3way(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before loading a new dataset?"
            )

            if result == "cancel":
                return
            elif result == "yes":
                self.save_workspace()

        self.data_manager.load_csv(file_path)
        self.has_unsaved_changes = False
        self.update_save_button()

        if self.dataset_manager_dialog:
            active = self.data_manager.active_working_copy
            self.dataset_manager_dialog.set_current_dataset(active)

    def on_dataset_deleted(self, rel_path):
        """Handle dataset deletion from the manager."""
        active = self.data_manager.active_working_copy
        if active is None:
            # Active dataset was deleted — clear UI
            self.data_manager.clear_data()
            self.has_unsaved_changes = False
            self.update_save_button()

    def on_dataset_renamed(self, old_rel, new_rel):
        """Handle dataset rename."""
        pass

    def on_workspace_reset(self):
        """Handle workspace reset — all data cleared."""
        self.has_unsaved_changes = False
        self.update_save_button()

    def show_dataset_manager(self):
        """Show the dataset manager dialog."""
        self.dataset_manager_dialog = DatasetManagerDialog(self)
        self.dataset_manager_dialog.dataset_selected.connect(self.load_dataset_from_manager)
        self.dataset_manager_dialog.dataset_deleted.connect(self.on_dataset_deleted)
        self.dataset_manager_dialog.dataset_renamed.connect(self.on_dataset_renamed)
        self.dataset_manager_dialog.workspace_reset.connect(self.on_workspace_reset)

        self.dataset_manager_dialog.set_workspace(self.workspace_path, self.workspace_name)
        self.dataset_manager_dialog.set_data_manager(self.data_manager)
        self.dataset_manager_dialog.exec()

    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes."""
        self.has_unsaved_changes = True
        self.update_save_button()

    def _apply_discard_btn_style(self):
        """Apply the correct style to the discard button based on state."""
        if self.discard_btn.isEnabled():
            self.discard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.discard_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #e2e4ed;
                    border: 1px solid rgba(255,255,255,0.25);
                    padding: 7px 16px;
                    border-radius: 6px;
                    min-height: 20px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.06);
                }
            """)
        else:
            self.discard_btn.setCursor(Qt.CursorShape.ForbiddenCursor)
            self.discard_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #6b7280;
                    border: 1px solid rgba(255,255,255,0.08);
                    padding: 7px 16px;
                    border-radius: 6px;
                    min-height: 20px;
                    font-weight: 500;
                }
            """)

    def update_save_button(self):
        """Update the save button and discard button state."""
        has_data = self.data_manager.data is not None
        self.save_btn.setEnabled(has_data)
        self.export_btn.setEnabled(has_data)

        # Update discard button
        self.discard_btn.setEnabled(self.has_unsaved_changes and has_data)
        self._apply_discard_btn_style()

        if self.has_unsaved_changes and has_data:
            self.save_btn.setText("Save Workspace *")
            self.save_btn.setProperty("cssClass", "warning")
            self.save_btn.setStyleSheet("")  # clear any overrides
            self.save_btn.style().unpolish(self.save_btn)
            self.save_btn.style().polish(self.save_btn)
        else:
            self.save_btn.setText("Save Workspace")
            self.save_btn.setProperty("cssClass", "primary")
            self.save_btn.setStyleSheet("")
            self.save_btn.style().unpolish(self.save_btn)
            self.save_btn.style().polish(self.save_btn)

    def save_workspace(self):
        """Save the current workspace data."""
        if self.data_manager.data is None:
            return

        try:
            self.data_manager.save_workspace_data()
            self.has_unsaved_changes = False
            self.update_save_button()

            if self.dataset_manager_dialog and self.data_manager.active_working_copy:
                self.dataset_manager_dialog.set_current_dataset(
                    self.data_manager.active_working_copy)

            modal.show_info(
                self,
                "Success",
                "Workspace data saved successfully!"
            )
        except Exception as e:
            modal.show_error(
                self,
                "Error",
                f"Error saving workspace: {str(e)}"
            )

    def discard_changes(self):
        """Discard all unsaved changes by reloading from last saved state."""
        if not self.has_unsaved_changes:
            return

        result = modal.show_discard_confirm(
            self,
            "Discard Changes",
            "Are you sure you want to discard all unsaved changes? This cannot be undone."
        )

        if result:
            # Reload from last saved workspace data
            self.data_manager.load_workspace_data()
            self.has_unsaved_changes = False
            self.update_save_button()

    def on_back_clicked(self):
        """Handle back button click with unsaved changes check."""
        if self.has_unsaved_changes:
            result = modal.show_question_3way(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before leaving?"
            )

            if result == "cancel":
                return
            elif result == "yes":
                self.save_workspace()

        self.back_to_home.emit()

    def on_data_loaded(self, df):
        """Handle when data is loaded.

        Only the data preview (always visible) and the currently active tab
        panel are updated immediately.  All other panels are marked dirty and
        refreshed lazily when the user switches to them.
        """
        self._latest_df = df
        self.update_save_button()
        if self.dataset_manager_dialog:
            self.dataset_manager_dialog.refresh()

        # Data preview is always visible – update immediately
        self.data_preview.on_data_loaded(df)

        # Map tab indices to panels that have on_data_loaded
        self._tab_panels = {
            0: self.preprocessing_panel,
            1: self.analysis_panel,
            2: self.visualization_panel,
            3: self.feature_engineering_panel,
            4: self.machine_learning_panel,
        }

        # Update the currently visible tab now, mark the rest dirty
        current = self.tabs.currentIndex()
        self._dirty_tabs = set(self._tab_panels.keys())

        if current in self._tab_panels:
            self._dirty_tabs.discard(current)
            self._tab_panels[current].on_data_loaded(df)

    def _on_tab_changed(self, index):
        """Refresh a tab panel when the user switches to it (if dirty)."""
        if index in self._dirty_tabs and self._latest_df is not None:
            self._dirty_tabs.discard(index)
            panel = self._tab_panels.get(index)
            if panel and hasattr(panel, 'on_data_loaded'):
                panel.on_data_loaded(self._latest_df)

    def show_error(self, message):
        """Show error message."""
        modal.show_error(self, "Error", message)
