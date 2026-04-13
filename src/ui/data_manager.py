"""
Data manager for handling CSV file operations and data storage.
"""

import os
import re
import json
import shutil
import pandas as pd
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from scipy import stats
from .logging_utils import get_logger


logger = get_logger(__name__)


def sanitize_basename(name: str) -> str:
    """Normalize a filename base for use in copy filenames.

    Strips the extension, trims leading/trailing underscores or spaces,
    and collapses internal underscore runs to a single underscore so
    that joining sanitized parts with '_' never produces double
    underscores.
    """
    base = os.path.splitext(name)[0]
    base = base.strip('_ ')
    base = re.sub(r'_+', '_', base)
    return base


def get_next_copy_name(workspace_name, original_filename, copies_dir):
    """Return the next numbered copy filename for an original.

    The first copy is always ``..._1.csv`` (never unnumbered) and
    subsequent copies increment the trailing number. Both the workspace
    name and the original filename are sanitized first to avoid double
    underscore artefacts.
    """
    workspace_clean = sanitize_basename(workspace_name) if workspace_name else "workspace"
    file_clean = sanitize_basename(original_filename)
    base = f"{workspace_clean}_{file_clean}"

    counter = 1
    while True:
        candidate = f"{base}_{counter}.csv"
        if not os.path.exists(os.path.join(copies_dir, candidate)):
            return candidate
        counter += 1


class DataManager(QObject):
    """Manages data operations and storage for the application."""

    # Signals for notifying UI of data changes
    data_loaded = pyqtSignal(pd.DataFrame)
    data_error = pyqtSignal(str)

    def __init__(self):
        """Initialize the data manager."""
        super().__init__()
        self._data = None
        self.history = []  # Stack for undo
        self.redo_stack = []  # Stack for redo
        self.max_history = 20  # Maximum number of operations to store
        self.workspace_path = None
        self.workspace_name = ""
        self._active_working_copy = None  # filename of the current working copy
        self._originals = {}  # {original_filename: {"imported_at": str, "copies": [str]}}
        self._unassigned_copies = []  # copy rel paths found on disk with no parent original

    def clear_data(self):
        """Clear the current data."""
        self._data = None
        self.history = []
        self.redo_stack = []
        self._active_working_copy = None
        self._originals = {}
        self._unassigned_copies = []
        self.data_loaded.emit(pd.DataFrame())

    @property
    def data(self):
        """Get the current dataframe."""
        return self._data

    @property
    def active_working_copy(self):
        """Get the filename of the current working copy."""
        return self._active_working_copy

    @property
    def columns(self):
        """Get list of column names from the current dataframe."""
        if self._data is not None:
            return list(self._data.columns)
        return []

    # ── Folder helpers ────────────────────────────────────────────────────

    @staticmethod
    def _sanitize_name(name):
        """Clean a name for use in filenames (spaces->underscores, strip specials)."""
        name = name.replace(' ', '_')
        name = re.sub(r'[^\w\-]', '', name)
        return name

    def _originals_folder(self):
        return os.path.join(self.workspace_path, "data", "originals")

    def _copies_folder(self):
        return os.path.join(self.workspace_path, "data", "copies")

    def _ensure_data_folders(self):
        if self.workspace_path:
            os.makedirs(self._originals_folder(), exist_ok=True)
            os.makedirs(self._copies_folder(), exist_ok=True)

    def _resolve_data_path(self, relative_path):
        """Resolve a path relative to data/ into an absolute path."""
        return os.path.join(self.workspace_path, "data", relative_path.replace("/", os.sep))

    def _is_inside_workspace_data(self, file_path):
        """Check whether a file path is anywhere under the workspace data tree."""
        if not self.workspace_path:
            return False
        data_folder = os.path.normpath(os.path.abspath(os.path.join(self.workspace_path, "data")))
        abs_path = os.path.normpath(os.path.abspath(file_path))
        return abs_path.startswith(data_folder + os.sep) or abs_path.startswith(data_folder + "/")

    def _rel_path_for(self, abs_path):
        """Get the data-relative path (forward-slash separated) for an absolute path."""
        data_folder = os.path.abspath(os.path.join(self.workspace_path, "data"))
        return os.path.relpath(os.path.abspath(abs_path), data_folder).replace("\\", "/")

    # ── Migration ──────────────────────────────────────────────────────────

    def _migrate_flat_structure(self):
        """Migrate old flat data/ layout to data/originals/ + data/copies/."""
        if not self.workspace_path:
            return
        originals_dir = self._originals_folder()
        copies_dir = self._copies_folder()
        if os.path.isdir(originals_dir) and os.path.isdir(copies_dir):
            return  # already migrated
        self._ensure_data_folders()

        data_folder = os.path.join(self.workspace_path, "data")
        metadata_path = os.path.join(self.workspace_path, "metadata.json")
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

        originals_map = metadata.get('originals', {})
        active = metadata.get('active_working_copy')

        known_copies = set()
        known_originals = set()
        for orig_name, info in originals_map.items():
            known_originals.add(orig_name)
            for c in info.get('copies', []):
                # Strip any existing subfolder prefix (handles partial migrations)
                known_copies.add(os.path.basename(c))

        # Move known originals
        for orig_name in list(known_originals):
            src = os.path.join(data_folder, orig_name)
            dst = os.path.join(originals_dir, orig_name)
            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.move(src, dst)

        # Move known copies
        for copy_name in list(known_copies):
            src = os.path.join(data_folder, copy_name)
            dst = os.path.join(copies_dir, copy_name)
            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.move(src, dst)

        # Move active_working_copy if it wasn't in either set
        if active:
            base_active = os.path.basename(active)
            src = os.path.join(data_folder, base_active)
            if os.path.isfile(src):
                dst = os.path.join(copies_dir, base_active)
                if not os.path.exists(dst):
                    shutil.move(src, dst)

        # Rewrite metadata with relative paths
        new_originals = {}
        for orig_name, info in originals_map.items():
            new_copies = []
            for c in info.get('copies', []):
                basename = os.path.basename(c)
                new_copies.append(f"copies/{basename}")
            new_originals[orig_name] = {
                'path': f"originals/{orig_name}",
                'imported_at': info.get('imported_at', ''),
                'copies': new_copies,
            }
        metadata['originals'] = new_originals

        if active:
            base_active = os.path.basename(active)
            if base_active in known_originals:
                metadata['active_working_copy'] = f"originals/{base_active}"
            else:
                metadata['active_working_copy'] = f"copies/{base_active}"

        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
        except Exception:
            logger.exception("Failed to rewrite migrated metadata.json at %s", metadata_path)

    # ── Working-copy naming ────────────────────────────────────────────────

    def _generate_working_copy_name(self, original_filename):
        """Generate a unique working copy filename: {Workspace}_{OriginalBase}_{N}.csv."""
        self._ensure_data_folders()
        return get_next_copy_name(self.workspace_name, original_filename, self._copies_folder())

    # ── Metadata persistence ───────────────────────────────────────────────

    def _update_metadata(self):
        """Persist active_working_copy and originals map into metadata.json."""
        if not self.workspace_path:
            return
        metadata_path = os.path.join(self.workspace_path, "metadata.json")
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            if self._active_working_copy is not None:
                metadata['active_working_copy'] = self._active_working_copy
            metadata['originals'] = self._originals
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
        except Exception:
            logger.exception("Failed to update metadata.json at %s", metadata_path)

    def _load_originals_from_metadata(self):
        """Load the originals map from metadata.json."""
        if not self.workspace_path:
            return
        metadata_path = os.path.join(self.workspace_path, "metadata.json")
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self._originals = metadata.get('originals', {})
        except Exception:
            self._originals = {}

    def validate_metadata(self):
        """Reconcile metadata.json against the actual originals/ and copies/ folders.

        - Drops copy entries whose files no longer exist on disk.
        - Keeps original entries even when the file is missing (so the
          UI can render a warning indicator).
        - Auto-registers any CSV in originals/ that is not in metadata.
        - Auto-registers any CSV in copies/ that is not listed under
          any original by matching the filename pattern; copies that
          cannot be matched are exposed via ``get_unassigned_copies()``.
        """
        if not self.workspace_path:
            return

        self._ensure_data_folders()
        originals_dir = self._originals_folder()
        copies_dir = self._copies_folder()

        # 1. Drop missing copy entries from metadata.
        for orig_name, info in list(self._originals.items()):
            kept = []
            for copy_rel in info.get('copies', []):
                copy_abs = self._resolve_data_path(copy_rel)
                if os.path.isfile(copy_abs):
                    kept.append(copy_rel)
            info['copies'] = kept

        # 2. Register orphan originals (files in originals/ not in metadata).
        try:
            on_disk_originals = [
                f for f in os.listdir(originals_dir)
                if os.path.isfile(os.path.join(originals_dir, f)) and f.lower().endswith('.csv')
            ]
        except OSError:
            on_disk_originals = []

        from datetime import datetime
        for fname in on_disk_originals:
            if fname not in self._originals:
                ts = datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(originals_dir, fname))
                ).strftime('%Y-%m-%d %H:%M:%S')
                self._originals[fname] = {
                    'path': f"originals/{fname}",
                    'imported_at': ts,
                    'copies': [],
                }

        # 3. Match orphan copy files to a parent original by name pattern.
        try:
            on_disk_copies = [
                f for f in os.listdir(copies_dir)
                if os.path.isfile(os.path.join(copies_dir, f)) and f.lower().endswith('.csv')
            ]
        except OSError:
            on_disk_copies = []

        tracked = set()
        for info in self._originals.values():
            for copy_rel in info.get('copies', []):
                tracked.add(os.path.basename(copy_rel))

        ws_clean = sanitize_basename(self.workspace_name) if self.workspace_name else "workspace"
        unassigned = []
        for copy_basename in on_disk_copies:
            if copy_basename in tracked:
                continue

            parent = self._guess_parent_original(copy_basename, ws_clean)
            if parent is not None:
                copy_rel = f"copies/{copy_basename}"
                self._originals[parent].setdefault('copies', []).append(copy_rel)
                tracked.add(copy_basename)
            else:
                unassigned.append(f"copies/{copy_basename}")

        self._unassigned_copies = unassigned

        self._update_metadata()

    def _guess_parent_original(self, copy_basename, workspace_clean):
        """Try to determine which original a free-floating copy belongs to.

        Matches copies named ``{ws}_{file}_{N}.csv`` against each known
        original's sanitized basename. Returns the original filename or
        ``None`` if no match is found.
        """
        copy_root = sanitize_basename(copy_basename)
        prefix = f"{workspace_clean}_"
        if not copy_root.startswith(prefix):
            return None
        remainder = copy_root[len(prefix):]
        # Strip a trailing _<digits> if present.
        m = re.match(r'^(.*?)(?:_(\d+))?$', remainder)
        if not m:
            return None
        candidate_root = m.group(1)
        if not candidate_root:
            return None
        for orig_name in self._originals.keys():
            if sanitize_basename(orig_name) == candidate_root:
                return orig_name
        return None

    def get_unassigned_copies(self):
        """Return the list of orphan copy relative paths discovered on disk."""
        return list(self._unassigned_copies)

    # ── Query helpers ──────────────────────────────────────────────────────

    def get_originals(self):
        """Return the originals dict: {filename: {path, imported_at, copies}}."""
        return dict(self._originals)

    def get_copies_for_original(self, original_filename):
        """Return the list of working copy relative paths for an original."""
        entry = self._originals.get(original_filename, {})
        return list(entry.get('copies', []))

    def is_original(self, filename):
        """Check if a filename is a registered original."""
        return filename in self._originals

    def get_original_for_copy(self, copy_rel_path):
        """Find which original a working copy belongs to, or None."""
        for orig, info in self._originals.items():
            if copy_rel_path in info.get('copies', []):
                return orig
        return None

    def file_exists_on_disk(self, relative_path):
        """Check if a data-relative path exists on disk."""
        if not self.workspace_path or not relative_path:
            return False
        return os.path.isfile(self._resolve_data_path(relative_path))

    # ── Two-tier dataset operations ────────────────────────────────────────

    def import_original(self, file_path):
        """
        Import an external file as a Tier-1 original.

        Copies the file into data/originals/, registers it, creates a
        default working copy in data/copies/, and returns
        (original_filename, copy_relative_path).
        """
        if not self.workspace_path:
            return None, None

        self._ensure_data_folders()

        original_name = os.path.basename(file_path)
        dest_path = os.path.join(self._originals_folder(), original_name)

        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy2(file_path, dest_path)

        from datetime import datetime
        existing_copies = self._originals.get(original_name, {}).get('copies', [])
        self._originals[original_name] = {
            'path': f"originals/{original_name}",
            'imported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'copies': list(existing_copies),
        }

        # Create a default working copy
        working_basename = self._generate_working_copy_name(original_name)
        working_path = os.path.join(self._copies_folder(), working_basename)
        shutil.copy2(dest_path, working_path)

        copy_rel = f"copies/{working_basename}"
        self._originals[original_name]['copies'].append(copy_rel)

        self._update_metadata()
        return original_name, copy_rel

    def create_working_copy(self, original_filename):
        """
        Create a new working copy from an existing original.

        Returns the new copy relative path (copies/...), or None on error.
        """
        if not self.workspace_path:
            return None

        self._ensure_data_folders()
        original_path = os.path.join(self._originals_folder(), original_filename)
        if not os.path.exists(original_path):
            return None

        working_basename = self._generate_working_copy_name(original_filename)
        working_path = os.path.join(self._copies_folder(), working_basename)
        shutil.copy2(original_path, working_path)

        if original_filename not in self._originals:
            from datetime import datetime
            self._originals[original_filename] = {
                'path': f"originals/{original_filename}",
                'imported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'copies': [],
            }
        copy_rel = f"copies/{working_basename}"
        self._originals[original_filename]['copies'].append(copy_rel)

        self._update_metadata()
        return copy_rel

    def activate_dataset(self, relative_path):
        """Load a dataset from a data-relative path and set it as active."""
        if not self.workspace_path:
            return False
        abs_path = self._resolve_data_path(relative_path)
        if not os.path.exists(abs_path):
            return False

        try:
            self._data = pd.read_csv(abs_path, low_memory=False)
            self._active_working_copy = relative_path
            self._update_metadata()
            self.data_loaded.emit(self._data)
            return True
        except Exception as e:
            self.data_error.emit(f"Error loading dataset: {str(e)}")
            return False

    def delete_copy(self, copy_rel_path):
        """Delete a single working copy and remove from tracking."""
        if not self.workspace_path:
            return
        abs_path = self._resolve_data_path(copy_rel_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)

        for orig, info in self._originals.items():
            copies = info.get('copies', [])
            if copy_rel_path in copies:
                copies.remove(copy_rel_path)
                break

        if self._active_working_copy == copy_rel_path:
            self._active_working_copy = None

        self._update_metadata()

    def delete_original_with_copies(self, original_filename):
        """Delete an original and ALL its working copies."""
        if not self.workspace_path or original_filename not in self._originals:
            return []

        info = self._originals[original_filename]
        deleted_copies = list(info.get('copies', []))

        # Delete copy files
        for copy_rel in deleted_copies:
            abs_path = self._resolve_data_path(copy_rel)
            if os.path.exists(abs_path):
                os.remove(abs_path)

        # Delete original file
        orig_path = os.path.join(self._originals_folder(), original_filename)
        if os.path.exists(orig_path):
            os.remove(orig_path)

        # Clear active if it was one of the deleted
        if self._active_working_copy in deleted_copies:
            self._active_working_copy = None
        orig_rel = f"originals/{original_filename}"
        if self._active_working_copy == orig_rel:
            self._active_working_copy = None

        del self._originals[original_filename]
        self._update_metadata()
        return deleted_copies

    def rename_copy(self, old_rel, new_basename):
        """Rename a working copy on disk and update tracking."""
        if not self.workspace_path:
            return False
        old_abs = self._resolve_data_path(old_rel)
        new_rel = f"copies/{new_basename}"
        new_abs = self._resolve_data_path(new_rel)

        if not os.path.exists(old_abs) or os.path.exists(new_abs):
            return False

        os.rename(old_abs, new_abs)

        # Update tracking robustly:
        # - Some older metadata stored copy entries as bare basenames ("file_1.csv")
        #   instead of "copies/file_1.csv". Match by basename to preserve the parent
        #   original association across renames.
        old_basename = os.path.basename(old_rel)
        for _orig, info in self._originals.items():
            copies = info.get('copies', [])
            for i, entry in enumerate(list(copies)):
                if entry == old_rel or os.path.basename(entry) == old_basename:
                    copies[i] = new_rel
                    break

        if self._active_working_copy == old_rel:
            self._active_working_copy = new_rel

        self._update_metadata()
        return True

    def reset_workspace_data(self):
        """Delete ALL datasets (originals + copies), clear metadata."""
        if not self.workspace_path:
            return

        # Delete all files in originals/ and copies/
        for folder in (self._originals_folder(), self._copies_folder()):
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    fp = os.path.join(folder, f)
                    if os.path.isfile(fp):
                        os.remove(fp)

        self._originals = {}
        self._active_working_copy = None
        self._data = None
        self.history = []
        self.redo_stack = []

        # Update metadata to clean state
        metadata_path = os.path.join(self.workspace_path, "metadata.json")
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            from datetime import datetime
            metadata['active_working_copy'] = None
            metadata['originals'] = {}
            metadata['last_modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata['file_count'] = 0
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
        except Exception:
            logger.exception("Failed to reset metadata.json at %s", metadata_path)

        self.data_loaded.emit(pd.DataFrame())

    # ── Core data operations ───────────────────────────────────────────────

    def load_csv(self, file_path):
        """
        Load data from a CSV file.

        If the file is already inside the workspace data tree, it is
        activated directly.  Otherwise it is imported as an original with
        a working copy auto-created and activated.
        """
        try:
            self._data = pd.read_csv(file_path, low_memory=False)
            self.data_loaded.emit(self._data)

            if self.workspace_path:
                self._ensure_data_folders()

                if self._is_inside_workspace_data(file_path):
                    self._active_working_copy = self._rel_path_for(file_path)
                else:
                    original_name, copy_rel = self.import_original(file_path)
                    if copy_rel:
                        self._active_working_copy = copy_rel
                        QTimer.singleShot(0, self.save_workspace_data)

                QTimer.singleShot(0, self._update_metadata)

        except Exception as e:
            self.data_error.emit(f"Error loading CSV file: {str(e)}")

    def set_workspace_path(self, workspace_path):
        """Set the active workspace path."""
        self.workspace_path = workspace_path

    def set_workspace_name(self, name):
        """Set the active workspace name (used for working copy naming)."""
        self.workspace_name = name

    def get_workspace_data_path(self):
        """Get the data folder path for the active workspace."""
        if self.workspace_path:
            return os.path.join(self.workspace_path, "data")
        return None

    def get_column_data(self, column_name):
        """
        Get data for a specific column.

        Args:
            column_name (str): Name of the column to retrieve

        Returns:
            pd.Series: Column data if exists, None otherwise
        """
        if self._data is not None and column_name in self._data.columns:
            return self._data[column_name]
        return None

    def get_basic_stats(self, column_name):
        """
        Calculate basic statistics for a column.

        Args:
            column_name (str): Name of the column to analyze

        Returns:
            dict: Dictionary containing basic statistics
        """
        if self._data is None or column_name not in self._data.columns:
            return None

        column_data = self._data[column_name]

        # Basic statistics
        basic_stats = {
            'count': len(column_data),
            'non_null_count': column_data.count(),
            'null_count': column_data.isnull().sum(),
            'unique_count': column_data.nunique()
        }

        # Numeric statistics
        if pd.api.types.is_numeric_dtype(column_data):
            basic_stats.update({
                'mean': column_data.mean(),
                'median': column_data.median(),
                'std': column_data.std(),
                'min': column_data.min(),
                'max': column_data.max(),
                'q25': column_data.quantile(0.25),
                'q75': column_data.quantile(0.75)
            })

        return basic_stats

    def save_workspace_data(self):
        """Save current data to the active working copy."""
        if self.workspace_path and self._data is not None and self._active_working_copy:
            try:
                self._ensure_data_folders()
                path = self._resolve_data_path(self._active_working_copy)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                self._data.to_csv(path, index=False)
            except Exception as e:
                logger.exception("Failed to save workspace data to %s", self._active_working_copy)

    def load_workspace_data(self):
        """Load data from the workspace's active working copy.

        Runs flat-structure migration on first load, then reads
        ``active_working_copy`` from metadata.json.  Falls back to
        ``workspace_data.csv`` for backward compatibility.
        """
        if not self.workspace_path:
            return False

        # Migrate old flat data/ layout if needed
        self._migrate_flat_structure()

        # Load originals tracking from metadata
        self._load_originals_from_metadata()

        metadata_path = os.path.join(self.workspace_path, "metadata.json")
        target = None
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            target = metadata.get('active_working_copy')
        except Exception:
            logger.exception("Failed to read metadata.json at %s", metadata_path)

        # If metadata has an active copy, try to load it
        if target:
            path = self._resolve_data_path(target)
            if os.path.exists(path):
                try:
                    self._data = pd.read_csv(path, low_memory=False)
                    self._active_working_copy = target
                    self.data_loaded.emit(self._data)
                    return True
                except Exception as e:
                    self.data_error.emit(f"Error loading workspace data: {str(e)}")
                    return False

        # Backward compatibility: fall back to workspace_data.csv
        data_folder = os.path.join(self.workspace_path, "data")
        fallback = os.path.join(data_folder, "workspace_data.csv")
        if os.path.exists(fallback):
            try:
                self._data = pd.read_csv(fallback, low_memory=False)
                self._active_working_copy = "workspace_data.csv"
                self.data_loaded.emit(self._data)
                return True
            except Exception as e:
                self.data_error.emit(f"Error loading workspace data: {str(e)}")

        return False

    def get_correlation_analysis(self, column_name):
        """
        Calculate correlation coefficients between the selected column and other numeric columns.

        Args:
            column_name (str): Name of the column to analyze

        Returns:
            dict: Dictionary containing correlation coefficients
        """
        if self._data is None or column_name not in self._data.columns:
            return None

        series = self._data[column_name]

        # Only proceed if the column is numeric
        if not pd.api.types.is_numeric_dtype(series):
            return {'error': 'Correlation analysis requires numeric data'}

        # Get all numeric columns
        numeric_cols = self._data.select_dtypes(include=['number']).columns.tolist()

        # Calculate correlations
        correlations = {}
        for col in numeric_cols:
            if col != column_name and not self._data[col].isna().all():
                corr = self._data[column_name].corr(self._data[col])
                correlations[col] = corr

        # Sort by absolute correlation value (descending)
        correlations = {k: v for k, v in sorted(
            correlations.items(),
            key=lambda item: abs(item[1]),
            reverse=True
        )}

        return correlations

    def get_distribution_analysis(self, column_name):
        """
        Perform distribution analysis on a column.

        Args:
            column_name (str): Name of the column to analyze

        Returns:
            dict: Dictionary containing distribution metrics
        """
        if self._data is None or column_name not in self._data.columns:
            return None

        series = self._data[column_name].dropna()

        # Only proceed if the column is numeric
        if not pd.api.types.is_numeric_dtype(series):
            return {'error': 'Distribution analysis requires numeric data'}

        # Calculate distribution metrics
        try:
            skewness = stats.skew(series)
            kurtosis = stats.kurtosis(series)

            # Shapiro-Wilk test for normality (if sample size allows)
            if len(series) >= 3 and len(series) <= 5000:
                shapiro_test = stats.shapiro(series)
                normality_p_value = shapiro_test.pvalue
                is_normal = normality_p_value > 0.05
            else:
                normality_p_value = None
                is_normal = None

            # Percentiles
            percentiles = {
                '25%': np.percentile(series, 25),
                '50%': np.percentile(series, 50),
                '75%': np.percentile(series, 75),
                '90%': np.percentile(series, 90),
                '95%': np.percentile(series, 95),
                '99%': np.percentile(series, 99)
            }

            return {
                'skewness': skewness,
                'kurtosis': kurtosis,
                'normality_p_value': normality_p_value,
                'is_normal': is_normal,
                'percentiles': percentiles,
                'range': series.max() - series.min(),
                'iqr': stats.iqr(series)
            }
        except Exception as e:
            return {'error': f'Error in distribution analysis: {str(e)}'}

    def get_outlier_detection(self, column_name):
        """
        Detect outliers in a column using different methods.

        Args:
            column_name (str): Name of the column to analyze

        Returns:
            dict: Dictionary containing outlier detection results
        """
        if self._data is None or column_name not in self._data.columns:
            return None

        series = self._data[column_name].dropna()

        # Only proceed if the column is numeric
        if not pd.api.types.is_numeric_dtype(series):
            return {'error': 'Outlier detection requires numeric data'}

        # Z-Score method
        z_scores = np.abs(stats.zscore(series))
        z_outliers = np.where(z_scores > 3)[0]
        z_outlier_values = series.iloc[z_outliers].tolist()
        z_outlier_indices = series.iloc[z_outliers].index.tolist()

        # IQR method
        q1 = np.percentile(series, 25)
        q3 = np.percentile(series, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        iqr_outliers = series[(series < lower_bound) | (series > upper_bound)]
        iqr_outlier_values = iqr_outliers.tolist()
        iqr_outlier_indices = iqr_outliers.index.tolist()

        return {
            'z_score': {
                'outlier_count': len(z_outlier_values),
                'outlier_values': z_outlier_values[:10],  # Limit to first 10 values
                'outlier_indices': z_outlier_indices[:10],
                'threshold': 3
            },
            'iqr': {
                'outlier_count': len(iqr_outlier_values),
                'outlier_values': iqr_outlier_values[:10],  # Limit to first 10 values
                'outlier_indices': iqr_outlier_indices[:10],
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            }
        }

    def save_state(self):
        """Save current state to history for undo functionality."""
        if self._data is not None:
            self.history.append(self._data.copy())
            if len(self.history) > self.max_history:
                self.history.pop(0)
            self.redo_stack.clear()  # Clear redo stack when new action is performed

    def undo(self):
        """Undo the last operation."""
        if self.history:
            # Save current state to redo stack
            if self._data is not None:
                self.redo_stack.append(self._data.copy())

            # Restore previous state
            previous_state = self.history.pop()
            self._data = previous_state

            # Notify all components of the change
            self.data_loaded.emit(self._data)

    def redo(self):
        """Redo the last undone operation."""
        if self.redo_stack:
            # Save current state to history
            if self._data is not None:
                self.history.append(self._data.copy())

            # Restore redo state
            redo_state = self.redo_stack.pop()
            self._data = redo_state

            # Notify all components of the change
            self.data_loaded.emit(self._data)
