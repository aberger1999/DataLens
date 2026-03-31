"""
Dataset manager dialog for managing datasets within a workspace.
"""

import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
    QInputDialog, QLabel, QMenu, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor
from ..theme import get_colors, RADIUS_MD, RADIUS_LG

class DatasetItem(QWidget):
    """Custom widget for dataset list items."""

    def __init__(self, filename, file_path, is_active=False, theme="dark"):
        super().__init__()
        self.filename = filename
        self.file_path = file_path
        self.is_active = is_active
        c = get_colors(theme)

        self.setMinimumHeight(88)
        self.setFixedHeight(88)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        file_size = os.path.getsize(file_path)
        size_str = self.format_size(file_size)

        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        time_str = mod_time.strftime("%Y-%m-%d %H:%M")

        name_without_ext = filename.replace('.csv', '')

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name_without_ext)
        name_label.setStyleSheet(f"font-weight: bold; font-size: 12pt; color: {c['text_primary']}; background: transparent;")
        name_label.setWordWrap(False)

        details_label = QLabel(f"{size_str}  ·  {time_str}")
        details_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 9pt; background: transparent;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(details_label)

        layout.addLayout(info_layout, 1)

        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(36, 36)
        self.menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 16pt;
                font-weight: bold;
                color: {c['text_secondary']};
            }}
            QPushButton:hover {{
                background-color: {c['bg_hover']};
                border-radius: 6px;
                color: {c['text_primary']};
            }}
        """)
        layout.addWidget(self.menu_btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def format_size(self, size):
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

class DatasetManagerDialog(QDialog):
    """Dialog for managing datasets in a workspace."""

    dataset_selected = pyqtSignal(str)
    dataset_deleted = pyqtSignal(str)
    dataset_renamed = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.workspace_path = None
        self.current_dataset = "workspace_data.csv"
        self.init_ui()

    def _get_theme(self):
        """Get the current theme from the app palette heuristic."""
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            bg = app.palette().color(app.palette().ColorRole.Window)
            return "dark" if bg.lightness() < 128 else "light"
        return "dark"

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Dataset Manager")
        self.setModal(True)
        self.setMinimumSize(700, 500)

        c = get_colors(self._get_theme())

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Dataset Manager")
        header.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {c['text_primary']};")
        layout.addWidget(header)

        self.dataset_list = QListWidget()
        self.dataset_list.setSpacing(4)
        self.dataset_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border_subtle']};
                border-radius: {RADIUS_MD};
                padding: 6px;
                outline: none;
            }}
            QListWidget::item {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border_subtle']};
                border-radius: 6px;
                padding: 0px;
                margin: 3px;
                min-height: 88px;
            }}
            QListWidget::item:hover {{
                background-color: {c['bg_hover']};
                border: 1px solid {c['border']};
            }}
            QListWidget::item:selected {{
                background-color: {c['accent_subtle']};
                border: 2px solid {c['accent']};
            }}
        """)
        self.dataset_list.itemDoubleClicked.connect(self.load_selected_dataset)
        layout.addWidget(self.dataset_list)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.import_btn = QPushButton("Import Dataset")
        self.import_btn.setProperty("cssClass", "primary")
        self.import_btn.clicked.connect(self.import_dataset)

        self.load_btn = QPushButton("Load Selected")
        self.load_btn.clicked.connect(self.load_selected_dataset)
        self.load_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['success']};
                color: {c['text_inverse']};
                border: none;
                border-radius: {RADIUS_MD};
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.load_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def set_workspace(self, workspace_path):
        """Set the workspace path and refresh the dataset list."""
        self.workspace_path = workspace_path
        self.refresh_dataset_list()

    def set_current_dataset(self, filename):
        """Set the currently active dataset."""
        self.current_dataset = filename
        self.refresh_dataset_list()

    def refresh_dataset_list(self):
        """Refresh the list of datasets."""
        self.dataset_list.clear()

        if not self.workspace_path:
            return

        data_folder = os.path.join(self.workspace_path, "data")
        if not os.path.exists(data_folder):
            return

        csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]
        csv_files.sort()

        theme = self._get_theme()
        for filename in csv_files:
            file_path = os.path.join(data_folder, filename)
            is_active = (filename == self.current_dataset)

            item = QListWidgetItem(self.dataset_list)
            widget = DatasetItem(filename, file_path, is_active, theme)

            widget.menu_btn.clicked.connect(lambda checked, f=filename: self.show_context_menu(f))

            item.setSizeHint(QSize(widget.sizeHint().width(), 92))
            self.dataset_list.addItem(item)
            self.dataset_list.setItemWidget(item, widget)

            if is_active:
                item.setSelected(True)

    def show_context_menu(self, filename):
        """Show context menu for dataset actions."""
        c = get_colors(self._get_theme())
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                color: {c['text_primary']};
                font-size: 10pt;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {c['accent']};
                color: {c['text_inverse']};
            }}
        """)

        rename_action = menu.addAction("✏️ Rename")
        delete_action = menu.addAction("🗑️ Delete")

        if filename == "workspace_data.csv":
            rename_action.setEnabled(False)

        action = menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

        if action == rename_action:
            self.rename_dataset(filename)
        elif action == delete_action:
            self.delete_dataset(filename)

    def import_dataset(self):
        """Import a new dataset from a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Dataset",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.workspace_path, "data", filename)

            if os.path.exists(dest_path):
                reply = QMessageBox.question(
                    self,
                    "File Exists",
                    f"A dataset named '{filename}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            shutil.copy2(file_path, dest_path)
            self.refresh_dataset_list()

            QMessageBox.information(
                self,
                "Success",
                f"Dataset '{filename}' imported successfully!"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error importing dataset: {str(e)}"
            )

    def load_selected_dataset(self):
        """Load the selected dataset."""
        current_item = self.dataset_list.currentItem()
        if not current_item:
            return

        widget = self.dataset_list.itemWidget(current_item)
        if not widget:
            return

        file_path = widget.file_path
        self.dataset_selected.emit(file_path)
        self.set_current_dataset(widget.filename)

    def rename_dataset(self, filename):
        """Rename a dataset."""
        if filename == "workspace_data.csv":
            QMessageBox.warning(
                self,
                "Cannot Rename",
                "The active workspace data file cannot be renamed."
            )
            return

        name_without_ext = filename.replace('.csv', '')
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Dataset",
            "Enter new name:",
            text=name_without_ext
        )

        if not ok or not new_name:
            return

        if not new_name.endswith('.csv'):
            new_name += '.csv'

        try:
            old_path = os.path.join(self.workspace_path, "data", filename)
            new_path = os.path.join(self.workspace_path, "data", new_name)

            if os.path.exists(new_path):
                QMessageBox.warning(
                    self,
                    "Error",
                    f"A dataset named '{new_name}' already exists."
                )
                return

            os.rename(old_path, new_path)
            self.dataset_renamed.emit(filename, new_name)
            self.refresh_dataset_list()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error renaming dataset: {str(e)}"
            )

    def delete_dataset(self, filename):
        """Delete a dataset."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{filename}'?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            file_path = os.path.join(self.workspace_path, "data", filename)
            os.remove(file_path)
            self.dataset_deleted.emit(filename)
            self.refresh_dataset_list()

            QMessageBox.information(
                self,
                "Success",
                f"Dataset '{filename}' deleted successfully!"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error deleting dataset: {str(e)}"
            )
