"""
Feature engineering panel for creating and modifying dataset features.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QComboBox, QPushButton, QSpinBox,
    QGridLayout, QTabWidget, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QScrollArea, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from datetime import datetime

class FeatureEngineeringPanel(QWidget):
    """Panel for feature engineering operations."""

    feature_created = pyqtSignal()  # Signal when new feature is created
    data_modified = pyqtSignal()  # Signal when data is modified
    
    def __init__(self, data_manager):
        """Initialize the feature engineering panel."""
        super().__init__()
        self.data_manager = data_manager
        self.label_encoders = {}  # Store label encoders for each categorical column
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different feature engineering operations
        tabs = QTabWidget()
        
        # Numeric Operations Tab
        numeric_tab = QWidget()
        numeric_layout = QVBoxLayout(numeric_tab)
        
        # Column selection group
        numeric_col_group = QGroupBox("Select Columns")
        numeric_col_layout = QGridLayout(numeric_col_group)
        
        col_label = QLabel("Base Column:")
        self.numeric_col_combo = QComboBox()
        numeric_col_layout.addWidget(col_label, 0, 0)
        numeric_col_layout.addWidget(self.numeric_col_combo, 0, 1)
        
        # Optional second column for binary operations
        second_col_label = QLabel("Second Column:")
        self.second_col_combo = QComboBox()
        numeric_col_layout.addWidget(second_col_label, 1, 0)
        numeric_col_layout.addWidget(self.second_col_combo, 1, 1)
        
        numeric_layout.addWidget(numeric_col_group)
        
        # Operations group
        numeric_ops_group = QGroupBox("Numeric Operations")
        numeric_ops_layout = QGridLayout(numeric_ops_group)
        
        # Operation type selector
        op_label = QLabel("Operation:")
        self.numeric_op_combo = QComboBox()
        self.numeric_op_combo.addItems([
            "Square",
            "Cube",
            "Square Root",
            "Log Transform",
            "Add Columns",
            "Subtract Columns",
            "Multiply Columns",
            "Divide Columns",
            "Power",
            "Binning"
        ])
        numeric_ops_layout.addWidget(op_label, 0, 0)
        numeric_ops_layout.addWidget(self.numeric_op_combo, 0, 1)
        
        # Power value input
        power_label = QLabel("Power Value:")
        self.power_spin = QDoubleSpinBox()
        self.power_spin.setRange(-10, 10)
        self.power_spin.setValue(2)
        self.power_spin.setEnabled(False)
        numeric_ops_layout.addWidget(power_label, 1, 0)
        numeric_ops_layout.addWidget(self.power_spin, 1, 1)
        
        # Binning options
        bins_label = QLabel("Number of Bins:")
        self.bins_spin = QSpinBox()
        self.bins_spin.setRange(2, 100)
        self.bins_spin.setValue(5)
        self.bins_spin.setEnabled(False)
        numeric_ops_layout.addWidget(bins_label, 2, 0)
        numeric_ops_layout.addWidget(self.bins_spin, 2, 1)
        
        # New column name
        name_label = QLabel("New Column Name:")
        self.numeric_name_edit = QLineEdit()
        numeric_ops_layout.addWidget(name_label, 3, 0)
        numeric_ops_layout.addWidget(self.numeric_name_edit, 3, 1)
        
        # Apply button
        self.apply_numeric_btn = QPushButton("Create Feature")
        numeric_ops_layout.addWidget(self.apply_numeric_btn, 4, 0, 1, 2)
        
        numeric_layout.addWidget(numeric_ops_group)
        tabs.addTab(numeric_tab, "Numeric Features")
        
        # Categorical Operations Tab
        categorical_tab = QWidget()
        categorical_layout = QVBoxLayout(categorical_tab)
        
        # Column selection group
        cat_col_group = QGroupBox("Select Column")
        cat_col_layout = QGridLayout(cat_col_group)
        
        cat_label = QLabel("Categorical Column:")
        self.cat_col_combo = QComboBox()
        cat_col_layout.addWidget(cat_label, 0, 0)
        cat_col_layout.addWidget(self.cat_col_combo, 0, 1)
        
        categorical_layout.addWidget(cat_col_group)
        
        # Encoding options group
        encoding_group = QGroupBox("Encoding Options")
        encoding_layout = QGridLayout(encoding_group)
        
        # Encoding type selector
        encoding_label = QLabel("Encoding Method:")
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems([
            "Label Encoding",
            "One-Hot Encoding",
            "Binary Encoding",
            "Frequency Encoding",
            "Target Encoding"
        ])
        encoding_layout.addWidget(encoding_label, 0, 0)
        encoding_layout.addWidget(self.encoding_combo, 0, 1)
        
        # Target column for target encoding
        target_label = QLabel("Target Column:")
        self.target_col_combo = QComboBox()
        self.target_col_combo.setEnabled(False)
        encoding_layout.addWidget(target_label, 1, 0)
        encoding_layout.addWidget(self.target_col_combo, 1, 1)
        
        # Apply button
        self.apply_cat_btn = QPushButton("Apply Encoding")
        encoding_layout.addWidget(self.apply_cat_btn, 2, 0, 1, 2)
        
        categorical_layout.addWidget(encoding_group)
        tabs.addTab(categorical_tab, "Categorical Features")
        
        # DateTime Operations Tab
        datetime_tab = QWidget()
        datetime_layout = QVBoxLayout(datetime_tab)
        
        # Column selection group
        dt_col_group = QGroupBox("Select DateTime Column")
        dt_col_layout = QGridLayout(dt_col_group)
        
        dt_label = QLabel("DateTime Column:")
        self.dt_col_combo = QComboBox()
        dt_col_layout.addWidget(dt_label, 0, 0)
        dt_col_layout.addWidget(self.dt_col_combo, 0, 1)
        
        datetime_layout.addWidget(dt_col_group)
        
        # DateTime features group
        dt_features_group = QGroupBox("Extract Features")
        dt_features_layout = QGridLayout(dt_features_group)
        
        # Feature checkboxes
        self.year_check = QCheckBox("Year")
        self.month_check = QCheckBox("Month")
        self.day_check = QCheckBox("Day")
        self.weekday_check = QCheckBox("Day of Week")
        self.hour_check = QCheckBox("Hour")
        self.minute_check = QCheckBox("Minute")
        self.quarter_check = QCheckBox("Quarter")
        self.is_weekend_check = QCheckBox("Is Weekend")
        
        dt_features_layout.addWidget(self.year_check, 0, 0)
        dt_features_layout.addWidget(self.month_check, 0, 1)
        dt_features_layout.addWidget(self.day_check, 1, 0)
        dt_features_layout.addWidget(self.weekday_check, 1, 1)
        dt_features_layout.addWidget(self.hour_check, 2, 0)
        dt_features_layout.addWidget(self.minute_check, 2, 1)
        dt_features_layout.addWidget(self.quarter_check, 3, 0)
        dt_features_layout.addWidget(self.is_weekend_check, 3, 1)
        
        # Apply button
        self.apply_dt_btn = QPushButton("Extract Features")
        dt_features_layout.addWidget(self.apply_dt_btn, 4, 0, 1, 2)
        
        datetime_layout.addWidget(dt_features_group)
        tabs.addTab(datetime_tab, "DateTime Features")
        
        # Feature Combination Tab
        combination_tab = QWidget()
        combination_layout = QVBoxLayout(combination_tab)
        
        # Column selection group
        combine_col_group = QGroupBox("Select Columns to Combine")
        combine_col_layout = QVBoxLayout(combine_col_group)
        
        self.combine_columns_table = QTableWidget()
        self.combine_columns_table.setColumnCount(2)
        self.combine_columns_table.setHorizontalHeaderLabels(["Column", "Include"])
        combine_col_layout.addWidget(self.combine_columns_table)
        
        combination_layout.addWidget(combine_col_group)
        
        # Combination options group
        combine_options_group = QGroupBox("Combination Options")
        combine_options_layout = QGridLayout(combine_options_group)
        
        # Combination method selector
        combine_method_label = QLabel("Combination Method:")
        self.combine_method_combo = QComboBox()
        self.combine_method_combo.addItems([
            "Sum",
            "Mean",
            "Product",
            "Min",
            "Max",
            "Concatenate Strings"
        ])
        combine_options_layout.addWidget(combine_method_label, 0, 0)
        combine_options_layout.addWidget(self.combine_method_combo, 0, 1)
        
        # New column name
        combine_name_label = QLabel("New Column Name:")
        self.combine_name_edit = QLineEdit()
        combine_options_layout.addWidget(combine_name_label, 1, 0)
        combine_options_layout.addWidget(self.combine_name_edit, 1, 1)
        
        # Apply button
        self.apply_combine_btn = QPushButton("Create Combined Feature")
        combine_options_layout.addWidget(self.apply_combine_btn, 2, 0, 1, 2)
        
        combination_layout.addWidget(combine_options_group)
        tabs.addTab(combination_tab, "Feature Combinations")
        
        layout.addWidget(tabs)
        
    def setup_connections(self):
        """Setup signal connections."""
        self.data_manager.data_loaded.connect(self.on_data_loaded)
        self.numeric_op_combo.currentTextChanged.connect(self.on_numeric_op_changed)
        self.encoding_combo.currentTextChanged.connect(self.on_encoding_method_changed)
        self.apply_numeric_btn.clicked.connect(self.apply_numeric_operation)
        self.apply_cat_btn.clicked.connect(self.apply_categorical_encoding)
        self.apply_dt_btn.clicked.connect(self.extract_datetime_features)
        self.apply_combine_btn.clicked.connect(self.create_combined_feature)
        
    def on_data_loaded(self, df):
        """Handle when new data is loaded."""
        # Update numeric column selectors
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        self.numeric_col_combo.clear()
        self.second_col_combo.clear()
        self.numeric_col_combo.addItems(numeric_columns)
        self.second_col_combo.addItems(numeric_columns)
        
        # Update categorical column selector
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.cat_col_combo.clear()
        self.cat_col_combo.addItems(categorical_columns)
        
        # Update target column selector (for target encoding)
        self.target_col_combo.clear()
        self.target_col_combo.addItems(numeric_columns)
        
        # Update datetime column selector
        datetime_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
        self.dt_col_combo.clear()
        self.dt_col_combo.addItems(datetime_columns)
        
        # Update combination columns table
        self.update_combination_columns_table()
        
    def on_numeric_op_changed(self, operation):
        """Enable/disable relevant controls based on selected operation."""
        self.power_spin.setEnabled(operation == "Power")
        self.bins_spin.setEnabled(operation == "Binning")
        self.second_col_combo.setEnabled(operation in [
            "Add Columns", "Subtract Columns",
            "Multiply Columns", "Divide Columns"
        ])
        
    def on_encoding_method_changed(self, method):
        """Enable/disable target column selector based on encoding method."""
        self.target_col_combo.setEnabled(method == "Target Encoding")
        
    def apply_numeric_operation(self):
        """Apply the selected numeric operation to create a new feature."""
        if self.data_manager.data is None:
            return

        df = self.data_manager.data.copy()
        col = self.numeric_col_combo.currentText()
        operation = self.numeric_op_combo.currentText()
        new_name = self.numeric_name_edit.text()

        if not col:
            QMessageBox.warning(self, "Warning", "Please select a numeric column.")
            return
        if not new_name:
            QMessageBox.warning(self, "Warning", "Please specify a name for the new feature.")
            return
            
        try:
            if operation == "Square":
                df[new_name] = df[col] ** 2
            elif operation == "Cube":
                df[new_name] = df[col] ** 3
            elif operation == "Square Root":
                if (df[col] < 0).any():
                    raise ValueError("Cannot compute square root of negative values")
                df[new_name] = np.sqrt(df[col])
            elif operation == "Log Transform":
                if (df[col] <= 0).any():
                    raise ValueError("Cannot compute log of non-positive values")
                df[new_name] = np.log(df[col])
            elif operation == "Power":
                power = self.power_spin.value()
                df[new_name] = df[col] ** power
            elif operation == "Binning":
                bins = self.bins_spin.value()
                df[new_name] = pd.qcut(df[col], bins, labels=False)
            else:
                # Binary operations
                col2 = self.second_col_combo.currentText()
                if operation == "Add Columns":
                    df[new_name] = df[col] + df[col2]
                elif operation == "Subtract Columns":
                    df[new_name] = df[col] - df[col2]
                elif operation == "Multiply Columns":
                    df[new_name] = df[col] * df[col2]
                elif operation == "Divide Columns":
                    if (df[col2] == 0).any():
                        raise ValueError("Division by zero encountered")
                    df[new_name] = df[col] / df[col2]
                    
            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            QMessageBox.information(self, "Success", "New feature created successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating feature: {str(e)}")
            
    def apply_categorical_encoding(self):
        """Apply the selected encoding method to categorical features."""
        if self.data_manager.data is None:
            return

        df = self.data_manager.data.copy()
        col = self.cat_col_combo.currentText()
        method = self.encoding_combo.currentText()

        if not col:
            QMessageBox.warning(self, "Warning", "Please select a categorical column.")
            return

        try:
            if method == "Label Encoding":
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(df[col])

            elif method == "One-Hot Encoding":
                encoded = pd.get_dummies(df[col], prefix=col)
                df = pd.concat([df, encoded], axis=1)

            elif method == "Binary Encoding":
                # Create binary encoding manually
                unique_values = df[col].unique()
                n_values = len(unique_values)
                n_bits = int(np.ceil(np.log2(max(n_values, 2))))

                value_to_binary = {val: format(i, f'0{n_bits}b')
                                 for i, val in enumerate(unique_values)}

                for bit in range(n_bits):
                    # Use default arg to capture current bit value (avoids closure bug)
                    df[f"{col}_bin_{bit}"] = df[col].map(
                        lambda x, b=bit: int(value_to_binary[x][b]))

            elif method == "Frequency Encoding":
                frequency = df[col].value_counts(normalize=True)
                df[f"{col}_freq"] = df[col].map(frequency)

            elif method == "Target Encoding":
                target_col = self.target_col_combo.currentText()
                target_mean = df.groupby(col)[target_col].mean()
                df[f"{col}_target_encoded"] = df[col].map(target_mean)

            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            QMessageBox.information(self, "Success", "Categorical encoding applied successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying encoding: {str(e)}")
            
    def extract_datetime_features(self):
        """Extract selected features from datetime column."""
        if self.data_manager.data is None:
            return

        df = self.data_manager.data.copy()
        col = self.dt_col_combo.currentText()

        if not col:
            QMessageBox.warning(self, "Warning", "Please select a datetime column.")
            return

        try:
            if self.year_check.isChecked():
                df[f"{col}_year"] = pd.to_datetime(df[col]).dt.year
            if self.month_check.isChecked():
                df[f"{col}_month"] = pd.to_datetime(df[col]).dt.month
            if self.day_check.isChecked():
                df[f"{col}_day"] = pd.to_datetime(df[col]).dt.day
            if self.weekday_check.isChecked():
                df[f"{col}_weekday"] = pd.to_datetime(df[col]).dt.dayofweek
            if self.hour_check.isChecked():
                df[f"{col}_hour"] = pd.to_datetime(df[col]).dt.hour
            if self.minute_check.isChecked():
                df[f"{col}_minute"] = pd.to_datetime(df[col]).dt.minute
            if self.quarter_check.isChecked():
                df[f"{col}_quarter"] = pd.to_datetime(df[col]).dt.quarter
            if self.is_weekend_check.isChecked():
                df[f"{col}_is_weekend"] = pd.to_datetime(df[col]).dt.dayofweek.isin([5, 6]).astype(int)

            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            QMessageBox.information(self, "Success", "DateTime features extracted successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error extracting datetime features: {str(e)}")
            
    def update_combination_columns_table(self):
        """Update the combination columns table."""
        df = self.data_manager.data
        if df is None:
            return
            
        self.combine_columns_table.setRowCount(len(df.columns))
        
        for i, col in enumerate(df.columns):
            # Column name
            self.combine_columns_table.setItem(i, 0, QTableWidgetItem(col))
            
            # Checkbox for selection
            checkbox = QCheckBox()
            self.combine_columns_table.setCellWidget(i, 1, checkbox)
            
        self.combine_columns_table.resizeColumnsToContents()
        
    def create_combined_feature(self):
        """Create a new feature by combining selected columns."""
        if self.data_manager.data is None:
            return
            
        df = self.data_manager.data.copy()
        method = self.combine_method_combo.currentText()
        new_name = self.combine_name_edit.text()
        
        if not new_name:
            QMessageBox.warning(self, "Warning", "Please specify a name for the new feature.")
            return
            
        try:
            # Get selected columns
            selected_columns = []
            for i in range(self.combine_columns_table.rowCount()):
                checkbox = self.combine_columns_table.cellWidget(i, 1)
                if checkbox.isChecked():
                    column = self.combine_columns_table.item(i, 0).text()
                    selected_columns.append(column)
                    
            if len(selected_columns) < 2:
                QMessageBox.warning(self, "Warning", "Please select at least two columns to combine.")
                return
                
            if method == "Sum":
                df[new_name] = df[selected_columns].sum(axis=1)
            elif method == "Mean":
                df[new_name] = df[selected_columns].mean(axis=1)
            elif method == "Product":
                df[new_name] = df[selected_columns].prod(axis=1)
            elif method == "Min":
                df[new_name] = df[selected_columns].min(axis=1)
            elif method == "Max":
                df[new_name] = df[selected_columns].max(axis=1)
            elif method == "Concatenate Strings":
                df[new_name] = df[selected_columns].astype(str).agg(' '.join, axis=1)
                
            self.data_manager._data = df
            self.data_manager.data_loaded.emit(df)
            self.data_modified.emit()
            QMessageBox.information(self, "Success", "Combined feature created successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating combined feature: {str(e)}") 