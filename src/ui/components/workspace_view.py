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
from ..theme import get_colors, current_theme, RADIUS_MD, RADIUS_LG

class WorkspaceView(QWidget):
    """View for working within a specific workspace."""

    back_to_home = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Main View (left): reflects the currently loaded dataset (last applied),
        # and is the only source of truth for disk saves.
        self.main_data_manager = DataManager()
        # Editing View (right): sandbox for edits. Nothing is promoted to the
        # Main View until "Apply Changes to Main View" is pressed.
        self.edit_data_manager = DataManager()
        self.workspace_id = None
        self.workspace_path = None
        self.workspace_name = ""
        self.has_unsaved_changes = False
        self.has_pending_edits = False
        self.dataset_manager_dialog = None
        # Track which tab panels need a data refresh
        self._dirty_tabs = set()
        self._latest_df = None
        self._syncing_edit_from_main = False
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

        # Discard button
        self._apply_discard_btn_style()

        # Update child panels
        if hasattr(self, 'analysis_panel'):
            self.analysis_panel.update_theme(theme_name)
        if hasattr(self, 'visualization_panel'):
            self.visualization_panel.update_theme(theme_name)
        if hasattr(self, 'feature_engineering_panel'):
            self.feature_engineering_panel.update_theme(theme_name)
        if hasattr(self, 'machine_learning_panel'):
            self.machine_learning_panel.update_theme(theme_name)
        if hasattr(self, 'report_generator_panel'):
            self.report_generator_panel.update_theme(theme_name)

        if hasattr(self, "dataset_label"):
            self._apply_dataset_label_style()

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

        # Current dataset indicator (Original | Copy OR Original)
        self.dataset_label = QLabel("Dataset: —")
        dataset_font = QFont()
        dataset_font.setPointSize(10)
        self.dataset_label.setFont(dataset_font)
        self.dataset_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.dataset_label.setToolTip("Currently loaded dataset (Original | Copy OR Original)")
        self._apply_dataset_label_style()
        header_layout.addWidget(self.dataset_label)

        header_layout.addStretch()

        # Action button group
        self.dataset_manager_btn = QPushButton("Dataset Manager")
        self.dataset_manager_btn.setProperty("cssClass", "outline")
        self.dataset_manager_btn.clicked.connect(self.show_dataset_manager)
        header_layout.addWidget(self.dataset_manager_btn)

        # Promote edits (Editing View -> Main View)
        self.apply_btn = QPushButton("Apply Changes to Main View")
        self.apply_btn.setProperty("cssClass", "success")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply_edits_to_main_view)
        header_layout.addWidget(self.apply_btn)

        # Reset Editing View back to Main View
        self.reset_edit_btn = QPushButton("Reset Editing View")
        self.reset_edit_btn.setProperty("cssClass", "outline")
        self.reset_edit_btn.setEnabled(False)
        self.reset_edit_btn.clicked.connect(self.reset_editing_view)
        header_layout.addWidget(self.reset_edit_btn)

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

        self.data_preview = DataPreviewPanel(self.main_data_manager)
        self.data_preview.setMinimumWidth(200)
        main_splitter.addWidget(self.data_preview)

        self.tabs = QTabWidget()

        self.preprocessing_panel = PreprocessingPanel(self.edit_data_manager)

        # Apply initial theme (will be updated by MainWindow)
        self.update_theme("dark")
        self.tabs.addTab(self.preprocessing_panel, "Preprocessing")

        self.analysis_panel = AnalysisPanel(self.edit_data_manager)
        self.tabs.addTab(self.analysis_panel, "Analysis")

        self.visualization_panel = VisualizationPanel(self.edit_data_manager)
        self.tabs.addTab(self.visualization_panel, "Visualization")

        self.feature_engineering_panel = FeatureEngineeringPanel(self.edit_data_manager)
        self.tabs.addTab(self.feature_engineering_panel, "Feature Engineering")

        self.machine_learning_panel = MachineLearningPanel(self.edit_data_manager)
        self.tabs.addTab(self.machine_learning_panel, "Machine Learning")

        self.report_generator_panel = ReportGeneratorPanel(self.edit_data_manager)
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
        self.main_data_manager.data_error.connect(self.show_error)
        self.edit_data_manager.data_error.connect(self.show_error)
        self.main_data_manager.data_loaded.connect(self.on_main_data_loaded)
        self.edit_data_manager.data_loaded.connect(self.on_edit_data_loaded)

        # Hard guard: the Main View preview must never update from Editing View
        # signals (undo/redo included). If any accidental connection exists,
        # disconnect it.
        try:
            self.edit_data_manager.data_loaded.disconnect(self.data_preview.on_data_loaded)
        except Exception:
            pass

        # Panels were connected to edit_data_manager.data_loaded in their own
        # __init__. Disconnect so this view can update them lazily (only the
        # visible tab immediately, defer the rest).
        self.edit_data_manager.data_loaded.disconnect(self.preprocessing_panel.on_data_loaded)
        self.edit_data_manager.data_loaded.disconnect(self.analysis_panel.on_data_loaded)
        self.edit_data_manager.data_loaded.disconnect(self.visualization_panel.on_data_loaded)
        self.edit_data_manager.data_loaded.disconnect(self.feature_engineering_panel.on_data_loaded)
        self.edit_data_manager.data_loaded.disconnect(self.machine_learning_panel.on_data_loaded)

        # Any edit changes the Editing View only; it becomes "pending" until applied.
        self.preprocessing_panel.data_modified.connect(self.mark_pending_edits)
        self.feature_engineering_panel.data_modified.connect(self.mark_pending_edits)
        self.preprocessing_panel.apply_requested.connect(self.apply_edits_to_main_view)

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
        self.has_pending_edits = False

        self.workspace_label.setText(workspace_name)
        self._update_dataset_label()

        # Clear existing data from previous workspace
        self.main_data_manager.clear_data()
        self.edit_data_manager.clear_data()
        self._update_dataset_label()

        self.main_data_manager.set_workspace_path(workspace_path)
        self.main_data_manager.set_workspace_name(workspace_name)
        self.edit_data_manager.set_workspace_path(workspace_path)
        self.edit_data_manager.set_workspace_name(workspace_name)
        self.visualization_panel.set_workspace_path(workspace_path)
        self.report_generator_panel.set_workspace_path(workspace_path)

        # Try to load existing workspace data
        self.main_data_manager.load_workspace_data()
        self._update_apply_buttons()
        self._update_dataset_label()
        
    def save_data(self):
        """Save current data."""
        if self.main_data_manager.data is None:
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
                    self.main_data_manager.data.to_csv(file_path, index=False)
                elif file_path.endswith('.xlsx'):
                    self.main_data_manager.data.to_excel(file_path, index=False)
                    
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
    
    def activate_dataset_from_manager(self, relative_path):
        """Activate a workspace-internal dataset (original or working copy).

        Loads the file via ``DataManager.activate_dataset`` so that the
        active_working_copy pointer is the only thing that changes —
        the file is never re-imported and never re-registered as a new
        original.
        """
        if self.has_pending_edits:
            # Edits in the sandbox will be replaced by the new dataset.
            result = modal.show_question_3way(
                self,
                "Pending Edits",
                "You have pending edits in the Editing View. Do you want to apply them before loading a new dataset?"
            )
            if result == "cancel":
                return
            elif result == "yes":
                self.apply_edits_to_main_view()
            else:
                self.reset_editing_view()

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

        self.main_data_manager.activate_dataset(relative_path)
        self.has_unsaved_changes = False
        self.update_save_button()
        self._update_dataset_label()

        if self.dataset_manager_dialog:
            active = self.main_data_manager.active_working_copy
            self.dataset_manager_dialog.set_current_dataset(active)

    def on_dataset_deleted(self, rel_path):
        """Handle dataset deletion from the manager."""
        # The active dataset pointer may be cleared (or may still be set but
        # point to a file that no longer exists). Treat either case as "active
        # dataset removed" and clear the UI session state.
        active = self.main_data_manager.active_working_copy
        active_missing = (
            active is not None
            and hasattr(self.main_data_manager, "file_exists_on_disk")
            and not self.main_data_manager.file_exists_on_disk(active)
        )
        if active is None or active_missing:
            self.main_data_manager.clear_data()
            self.edit_data_manager.clear_data()
            self.has_unsaved_changes = False
            self.has_pending_edits = False
            self.update_save_button()
            self._update_apply_buttons()
            self._update_dataset_label()

    def on_dataset_renamed(self, old_rel, new_rel):
        """Handle dataset rename."""
        # The dialog blocks renaming the currently active dataset, but keep the
        # UI's notion of "current dataset" consistent if it changes elsewhere.
        if self.dataset_manager_dialog and self.main_data_manager.active_working_copy:
            self.dataset_manager_dialog.set_current_dataset(
                self.main_data_manager.active_working_copy
            )

    def on_workspace_reset(self):
        """Handle workspace reset — all data cleared."""
        self.has_unsaved_changes = False
        self.has_pending_edits = False
        self.update_save_button()
        self._update_apply_buttons()
        self._update_dataset_label()

    def show_dataset_manager(self):
        """Show the dataset manager dialog."""
        self.dataset_manager_dialog = DatasetManagerDialog(self)
        self.dataset_manager_dialog.dataset_activated.connect(self.activate_dataset_from_manager)
        self.dataset_manager_dialog.dataset_deleted.connect(self.on_dataset_deleted)
        self.dataset_manager_dialog.dataset_renamed.connect(self.on_dataset_renamed)
        self.dataset_manager_dialog.workspace_reset.connect(self.on_workspace_reset)

        self.dataset_manager_dialog.set_workspace(self.workspace_path, self.workspace_name)
        self.dataset_manager_dialog.set_data_manager(self.main_data_manager)
        self.dataset_manager_dialog.exec()

    def mark_pending_edits(self):
        """Mark that the Editing View has pending edits not yet applied."""
        self.has_pending_edits = True
        self._update_apply_buttons()

    def _update_apply_buttons(self):
        has_edit_data = self.edit_data_manager.data is not None
        self.apply_btn.setEnabled(has_edit_data and self.has_pending_edits)
        self.reset_edit_btn.setEnabled(has_edit_data and self.has_pending_edits)

    def _apply_discard_btn_style(self):
        """Apply the correct style to the discard button based on state."""
        c = get_colors(current_theme())
        if self.discard_btn.isEnabled():
            self.discard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.discard_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['text_primary']};
                    border: 1px solid {c['border_medium']};
                    padding: 7px 16px;
                    border-radius: 6px;
                    min-height: 20px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {c['bg_hover']};
                }}
            """)
        else:
            self.discard_btn.setCursor(Qt.CursorShape.ForbiddenCursor)
            self.discard_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['text_disabled']};
                    border: 1px solid {c['border_subtle']};
                    padding: 7px 16px;
                    border-radius: 6px;
                    min-height: 20px;
                    font-weight: 500;
                }}
            """)

    def update_save_button(self):
        """Update the save button and discard button state."""
        has_data = self.main_data_manager.data is not None
        # "Save Workspace" only matters when there is something to save.
        self.save_btn.setEnabled(has_data and self.has_unsaved_changes)
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
        if self.main_data_manager.data is None:
            return

        try:
            self.main_data_manager.save_workspace_data()
            self.has_unsaved_changes = False
            self.update_save_button()

            if self.dataset_manager_dialog and self.main_data_manager.active_working_copy:
                self.dataset_manager_dialog.set_current_dataset(
                    self.main_data_manager.active_working_copy)

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
            self.main_data_manager.load_workspace_data()
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

    def on_main_data_loaded(self, df):
        """Handle when Main View data is loaded.

        Updates the left-hand preview and refreshes the Editing View draft to
        match the newly loaded dataset.
        """
        self.update_save_button()
        self._update_dataset_label()
        if self.dataset_manager_dialog:
            self.dataset_manager_dialog.refresh()

        # Main View preview is always visible
        self.data_preview.on_data_loaded(df)

        # Sync Editing View draft from Main View load/activation
        self._syncing_edit_from_main = True
        try:
            if df is None:
                self.edit_data_manager.clear_data()
            else:
                self.edit_data_manager._data = df.copy()
                self.edit_data_manager.data_loaded.emit(self.edit_data_manager._data)
            self.has_pending_edits = False
            self._update_apply_buttons()
        finally:
            self._syncing_edit_from_main = False

    # ── Header dataset label helpers ───────────────────────────────────────

    def _apply_dataset_label_style(self):
        """Apply theme-aware styling to the current-dataset header label."""
        c = get_colors(current_theme())
        self.dataset_label.setStyleSheet(f"""
            QLabel {{
                color: {c['text_secondary']};
                background: transparent;
                border: none;
                padding: 0px 0px;
            }}
        """)

    def _format_active_dataset_text(self):
        """Return 'Dataset: Original | Copy' (or 'Dataset: Original')."""
        active = getattr(self.main_data_manager, "active_working_copy", None)
        if not active:
            return "Dataset: —"

        norm = str(active).replace("\\", "/")
        active_base = os.path.basename(norm)

        if norm.startswith("originals/"):
            return f"Dataset: {active_base}"

        orig = None
        if hasattr(self.main_data_manager, "get_original_for_copy"):
            try:
                orig = self.main_data_manager.get_original_for_copy(norm)
            except Exception:
                orig = None

        if orig:
            return f"Dataset: {orig} | {active_base}"

        return f"Dataset: {active_base}"

    def _update_dataset_label(self):
        if hasattr(self, "dataset_label"):
            self.dataset_label.setText(self._format_active_dataset_text())

    def on_edit_data_loaded(self, df):
        """Handle when Editing View data changes."""
        self._latest_df = df
        if not self._syncing_edit_from_main:
            self.has_pending_edits = True
            self._update_apply_buttons()

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

    def apply_edits_to_main_view(self):
        """Promote Editing View data into the Main View."""
        if self.edit_data_manager.data is None:
            return
        df = self.edit_data_manager.data.copy()
        self.main_data_manager._data = df
        self.main_data_manager.data_loaded.emit(df)
        self.has_unsaved_changes = True
        self.has_pending_edits = False
        self.update_save_button()
        self._update_apply_buttons()

    def reset_editing_view(self):
        """Discard pending edits by resetting Editing View to Main View data."""
        if self.main_data_manager.data is None:
            self.edit_data_manager.clear_data()
            self.has_pending_edits = False
            self._update_apply_buttons()
            return
        self._syncing_edit_from_main = True
        try:
            df = self.main_data_manager.data.copy()
            self.edit_data_manager._data = df
            self.edit_data_manager.data_loaded.emit(df)
            self.has_pending_edits = False
            self._update_apply_buttons()
        finally:
            self._syncing_edit_from_main = False
