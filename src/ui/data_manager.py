"""
Data manager for handling CSV file operations and data storage.
"""

import pandas as pd
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from scipy import stats

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

    def clear_data(self):
        """Clear the current data."""
        self._data = None
        self.history = []
        self.redo_stack = []
        self.data_loaded.emit(pd.DataFrame())

    @property
    def data(self):
        """Get the current dataframe."""
        return self._data
    
    @property
    def columns(self):
        """Get list of column names from the current dataframe."""
        if self._data is not None:
            return list(self._data.columns)
        return []
    
    def load_csv(self, file_path):
        """
        Load data from a CSV file.

        Args:
            file_path (str): Path to the CSV file

        Emits:
            data_loaded: When data is successfully loaded
            data_error: If an error occurs during loading
        """
        try:
            self._data = pd.read_csv(file_path, low_memory=False)
            self.data_loaded.emit(self._data)

            # Defer disk I/O so the UI updates first
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self.save_workspace_data)

            if self.workspace_path:
                import shutil
                import os
                data_folder = os.path.join(self.workspace_path, "data")
                filename = os.path.basename(file_path)
                dest_path = os.path.join(data_folder, filename)
                if file_path != dest_path:
                    QTimer.singleShot(0, lambda: shutil.copy2(file_path, dest_path))
        except Exception as e:
            self.data_error.emit(f"Error loading CSV file: {str(e)}")

    def set_workspace_path(self, workspace_path):
        """Set the active workspace path."""
        self.workspace_path = workspace_path

    def get_workspace_data_path(self):
        """Get the data folder path for the active workspace."""
        if self.workspace_path:
            import os
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
        stats = {
            'count': len(column_data),
            'non_null_count': column_data.count(),
            'null_count': column_data.isnull().sum(),
            'unique_count': column_data.nunique()
        }

        # Numeric statistics
        if pd.api.types.is_numeric_dtype(column_data):
            stats.update({
                'mean': column_data.mean(),
                'median': column_data.median(),
                'std': column_data.std(),
                'min': column_data.min(),
                'max': column_data.max(),
                'q25': column_data.quantile(0.25),
                'q75': column_data.quantile(0.75)
            })

        return stats

    def save_workspace_data(self):
        """Save current data to the workspace's persistent storage."""
        if self.workspace_path and self._data is not None:
            import os
            try:
                data_folder = os.path.join(self.workspace_path, "data")
                os.makedirs(data_folder, exist_ok=True)
                path = os.path.join(data_folder, "workspace_data.csv")
                self._data.to_csv(path, index=False)
            except Exception as e:
                print(f"Failed to autosave workspace data: {e}")

    def load_workspace_data(self):
        """Load data from the workspace's persistent storage if it exists."""
        if self.workspace_path:
            import os
            path = os.path.join(self.workspace_path, "data", "workspace_data.csv")
            if os.path.exists(path):
                try:
                    self._data = pd.read_csv(path, low_memory=False)
                    self.data_loaded.emit(self._data)
                    return True
                except Exception as e:
                    self.data_error.emit(f"Error loading workspace data: {str(e)}")
        return False

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
            
        series = self._data[column_name]
        
        # Handle numeric data
        if pd.api.types.is_numeric_dtype(series):
            return {
                'count': len(series),
                'mean': series.mean(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'median': series.median(),
                'missing': series.isna().sum()
            }
        
        # Handle categorical/text data
        return {
            'count': len(series),
            'unique_values': series.nunique(),
            'most_common': series.mode().iloc[0] if not series.empty else None,
            'missing': series.isna().sum()
        }
    
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