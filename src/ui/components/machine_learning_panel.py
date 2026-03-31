"""
Machine learning panel for model training, evaluation, and predictions.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QSpinBox,
    QGridLayout, QTabWidget, QLineEdit, QCheckBox,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDoubleSpinBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
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

class MachineLearningPanel(QWidget):
    """Panel for machine learning operations."""
    
    model_trained = pyqtSignal()  # Signal when model is trained
    
    def __init__(self, data_manager):
        """Initialize the machine learning panel."""
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
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different ML operations
        tabs = QTabWidget()
        
        # Model Training Tab
        training_tab = QWidget()
        training_layout = QVBoxLayout(training_tab)
        
        # Data Configuration Group
        data_config_group = QGroupBox("Data Configuration")
        data_config_layout = QGridLayout(data_config_group)
        
        # Target column selection
        target_label = QLabel("Target Column:")
        self.target_combo = QComboBox()
        data_config_layout.addWidget(target_label, 0, 0)
        data_config_layout.addWidget(self.target_combo, 0, 1)
        
        # Feature selection
        features_label = QLabel("Features:")
        self.features_table = QTableWidget()
        self.features_table.setColumnCount(2)
        self.features_table.setHorizontalHeaderLabels(["Column", "Include"])
        data_config_layout.addWidget(features_label, 1, 0)
        data_config_layout.addWidget(self.features_table, 1, 1)
        
        # Problem type selection
        problem_label = QLabel("Problem Type:")
        self.problem_combo = QComboBox()
        self.problem_combo.addItems(["Classification", "Regression"])
        data_config_layout.addWidget(problem_label, 2, 0)
        data_config_layout.addWidget(self.problem_combo, 2, 1)
        
        training_layout.addWidget(data_config_group)
        
        # Model Configuration Group
        model_config_group = QGroupBox("Model Configuration")
        model_config_layout = QGridLayout(model_config_group)
        
        # Model selection
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.update_model_list()  # Will be populated based on problem type
        model_config_layout.addWidget(model_label, 0, 0)
        model_config_layout.addWidget(self.model_combo, 0, 1)
        
        # Test size selection
        test_size_label = QLabel("Test Size:")
        self.test_size_spin = QDoubleSpinBox()
        self.test_size_spin.setRange(0.1, 0.5)
        self.test_size_spin.setValue(0.2)
        self.test_size_spin.setSingleStep(0.05)
        model_config_layout.addWidget(test_size_label, 1, 0)
        model_config_layout.addWidget(self.test_size_spin, 1, 1)
        
        # Cross-validation folds
        cv_label = QLabel("CV Folds:")
        self.cv_spin = QSpinBox()
        self.cv_spin.setRange(2, 10)
        self.cv_spin.setValue(5)
        model_config_layout.addWidget(cv_label, 2, 0)
        model_config_layout.addWidget(self.cv_spin, 2, 1)
        
        # Scaling method
        scaling_label = QLabel("Feature Scaling:")
        self.scaling_combo = QComboBox()
        self.scaling_combo.addItems(["None", "StandardScaler", "MinMaxScaler"])
        model_config_layout.addWidget(scaling_label, 3, 0)
        model_config_layout.addWidget(self.scaling_combo, 3, 1)
        
        training_layout.addWidget(model_config_group)
        
        # Training buttons
        button_layout = QHBoxLayout()
        self.train_btn = QPushButton("Train Model")
        self.evaluate_btn = QPushButton("Evaluate Model")
        self.evaluate_btn.setEnabled(False)
        button_layout.addWidget(self.train_btn)
        button_layout.addWidget(self.evaluate_btn)
        training_layout.addLayout(button_layout)
        
        tabs.addTab(training_tab, "Model Training")
        
        # Model Evaluation Tab
        evaluation_tab = QWidget()
        evaluation_layout = QVBoxLayout(evaluation_tab)
        
        # Metrics group
        metrics_group = QGroupBox("Model Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # Create labels for metrics
        self.metrics_labels = {}
        metrics = ["Accuracy/R²", "Precision/MAE", "Recall/MSE", "F1/RMSE"]
        for i, metric in enumerate(metrics):
            label = QLabel(f"{metric}:")
            value = QLabel("N/A")
            metrics_layout.addWidget(label, i, 0)
            metrics_layout.addWidget(value, i, 1)
            self.metrics_labels[metric] = value
            
        evaluation_layout.addWidget(metrics_group)
        
        # Cross-validation results
        cv_group = QGroupBox("Cross-Validation Results")
        cv_layout = QVBoxLayout(cv_group)
        self.cv_table = QTableWidget()
        cv_layout.addWidget(self.cv_table)
        evaluation_layout.addWidget(cv_group)
        
        # Feature importance plot
        importance_group = QGroupBox("Feature Importance")
        importance_layout = QVBoxLayout(importance_group)
        self.importance_figure = plt.figure()
        self.importance_canvas = FigureCanvas(self.importance_figure)
        importance_layout.addWidget(self.importance_canvas)
        evaluation_layout.addWidget(importance_group)
        
        tabs.addTab(evaluation_tab, "Model Evaluation")
        
        # Predictions Tab
        predictions_tab = QWidget()
        predictions_layout = QVBoxLayout(predictions_tab)
        
        # Prediction options
        pred_options_group = QGroupBox("Prediction Options")
        pred_options_layout = QGridLayout(pred_options_group)
        
        # Prediction method
        pred_method_label = QLabel("Prediction Method:")
        self.pred_method_combo = QComboBox()
        self.pred_method_combo.addItems(["Test Set", "New Data", "Current Data"])
        pred_options_layout.addWidget(pred_method_label, 0, 0)
        pred_options_layout.addWidget(self.pred_method_combo, 0, 1)
        
        predictions_layout.addWidget(pred_options_group)
        
        # Prediction results
        results_group = QGroupBox("Prediction Results")
        results_layout = QVBoxLayout(results_group)
        self.results_table = QTableWidget()
        results_layout.addWidget(self.results_table)
        predictions_layout.addWidget(results_group)
        
        # Prediction buttons
        pred_button_layout = QHBoxLayout()
        self.predict_btn = QPushButton("Make Predictions")
        self.predict_btn.setEnabled(False)
        self.export_btn = QPushButton("Export Predictions")
        self.export_btn.setEnabled(False)
        pred_button_layout.addWidget(self.predict_btn)
        pred_button_layout.addWidget(self.export_btn)
        predictions_layout.addLayout(pred_button_layout)
        
        tabs.addTab(predictions_tab, "Predictions")
        
        layout.addWidget(tabs)
        
    def setup_connections(self):
        """Setup signal connections."""
        self.data_manager.data_loaded.connect(self.on_data_loaded)
        self.problem_combo.currentTextChanged.connect(self.update_model_list)
        self.train_btn.clicked.connect(self.train_model)
        self.evaluate_btn.clicked.connect(self.evaluate_model)
        self.predict_btn.clicked.connect(self.make_predictions)
        self.export_btn.clicked.connect(self.export_predictions)
        
    def on_data_loaded(self, df):
        """Handle when new data is loaded."""
        if df is None:
            return
            
        # Update column selectors
        columns = df.columns.tolist()
        
        # Update target column selector
        self.target_combo.clear()
        self.target_combo.addItems(columns)
        
        # Update features table
        self.features_table.setRowCount(len(columns))
        for i, col in enumerate(columns):
            # Column name
            self.features_table.setItem(i, 0, QTableWidgetItem(col))
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # Default to selected
            self.features_table.setCellWidget(i, 1, checkbox)
        
        header = self.features_table.horizontalHeader()
        header.setStretchLastSection(True)
        
    def update_model_list(self):
        """Update the model list based on problem type."""
        self.model_combo.clear()
        if self.problem_combo.currentText() == "Classification":
            self.model_combo.addItems([
                "Logistic Regression",
                "Decision Tree",
                "Random Forest",
                "Gradient Boosting",
                "SVM"
            ])
        else:  # Regression
            self.model_combo.addItems([
                "Linear Regression",
                "Ridge Regression",
                "Lasso Regression",
                "Decision Tree",
                "Random Forest",
                "Gradient Boosting",
                "SVR"
            ])
            
    def get_selected_features(self):
        """Get list of selected feature columns."""
        selected = []
        for i in range(self.features_table.rowCount()):
            checkbox = self.features_table.cellWidget(i, 1)
            if checkbox.isChecked():
                column = self.features_table.item(i, 0).text()
                if column != self.target_combo.currentText():
                    selected.append(column)
        return selected
        
    def prepare_data(self):
        """Prepare data for model training."""
        df = self.data_manager.data
        if df is None:
            return False
            
        # Get target and features
        target_col = self.target_combo.currentText()
        self.feature_columns = self.get_selected_features()
        
        if not self.feature_columns:
            QMessageBox.warning(self, "Warning", "Please select at least one feature.")
            return False
            
        # Validate that feature columns are numeric
        non_numeric = [c for c in self.feature_columns
                       if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            QMessageBox.warning(
                self, "Warning",
                f"Non-numeric feature columns detected: {', '.join(non_numeric)}.\n"
                "Please encode categorical features first (Feature Engineering tab)."
            )
            return False

        X = df[self.feature_columns].copy()
        y = df[target_col].copy()

        # Apply scaling if selected
        scaling_method = self.scaling_combo.currentText()
        if scaling_method != "None":
            if scaling_method == "StandardScaler":
                self.scaler = StandardScaler()
            else:  # MinMaxScaler
                self.scaler = MinMaxScaler()
            X = pd.DataFrame(self.scaler.fit_transform(X), columns=X.columns)
            
        # Split data
        test_size = self.test_size_spin.value()
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        return True
        
    def get_model_instance(self):
        """Get a new instance of the selected model."""
        model_name = self.model_combo.currentText()
        problem_type = self.problem_combo.currentText()
        
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
            # Get and train model
            self.model = self.get_model_instance()
            self.model.fit(self.X_train, self.y_train)
            
            # Enable evaluation and prediction
            self.evaluate_btn.setEnabled(True)
            self.predict_btn.setEnabled(True)
            
            QMessageBox.information(self, "Success", "Model trained successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error training model: {str(e)}")
            
    def evaluate_model(self):
        """Evaluate the trained model."""
        if self.model is None:
            return
            
        try:
            # Make predictions on test set
            y_pred = self.model.predict(self.X_test)
            
            # Calculate metrics based on problem type
            if self.problem_combo.currentText() == "Classification":
                metrics = {
                    "Accuracy/R²": ("Accuracy", accuracy_score(self.y_test, y_pred)),
                    "Precision/MAE": ("Precision", precision_score(self.y_test, y_pred, average='weighted')),
                    "Recall/MSE": ("Recall", recall_score(self.y_test, y_pred, average='weighted')),
                    "F1/RMSE": ("F1 Score", f1_score(self.y_test, y_pred, average='weighted'))
                }
            else:  # Regression
                metrics = {
                    "Accuracy/R²": ("R²", r2_score(self.y_test, y_pred)),
                    "Precision/MAE": ("MAE", mean_absolute_error(self.y_test, y_pred)),
                    "Recall/MSE": ("MSE", mean_squared_error(self.y_test, y_pred)),
                    "F1/RMSE": ("RMSE", np.sqrt(mean_squared_error(self.y_test, y_pred)))
                }
                
            # Update metrics labels with descriptive names
            for key, (label_text, value) in metrics.items():
                self.metrics_labels[key].setText(f"{label_text}: {value:.4f}")
                
            # Perform cross-validation on training data only (avoid data leakage)
            cv_model = self.get_model_instance()
            cv_scores = cross_val_score(
                cv_model,
                self.X_train,
                self.y_train,
                cv=min(self.cv_spin.value(), len(self.X_train))
            )
            
            # Update CV table
            self.cv_table.setRowCount(len(cv_scores))
            self.cv_table.setColumnCount(2)
            self.cv_table.setHorizontalHeaderLabels(["Fold", "Score"])
            
            for i, score in enumerate(cv_scores):
                self.cv_table.setItem(i, 0, QTableWidgetItem(f"Fold {i+1}"))
                self.cv_table.setItem(i, 1, QTableWidgetItem(f"{score:.4f}"))
                
            # Plot feature importance if available
            self.plot_feature_importance()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error evaluating model: {str(e)}")
            
    def plot_feature_importance(self):
        """Plot feature importance if the model supports it."""
        try:
            # Clear the previous plot
            self.importance_figure.clear()
            
            # Check if model has feature importance
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_)
                if importances.ndim > 1:
                    importances = importances.mean(axis=0)
            else:
                return
                
            # Create plot
            ax = self.importance_figure.add_subplot(111)
            y_pos = np.arange(len(self.feature_columns))
            ax.barh(y_pos, importances)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(self.feature_columns)
            ax.set_xlabel('Importance')
            ax.set_title('Feature Importance')
            
            self.importance_figure.tight_layout()
            self.importance_canvas.draw()
            
        except Exception as e:
            print(f"Error plotting feature importance: {str(e)}")
            
    def make_predictions(self):
        """Make predictions using the trained model."""
        if self.model is None:
            return
            
        try:
            method = self.pred_method_combo.currentText()
            
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
                y_true = df[self.target_combo.currentText()]
            else:  # New Data
                QMessageBox.information(
                    self,
                    "Info",
                    "Feature not implemented yet. Please use Test Set or Current Data."
                )
                return
                
            # Make predictions
            y_pred = self.model.predict(X)
            
            # Display results
            self.results_table.setRowCount(len(y_pred))
            self.results_table.setColumnCount(3)
            self.results_table.setHorizontalHeaderLabels(
                ["Index", "Actual", "Predicted"]
            )
            
            for i in range(len(y_pred)):
                self.results_table.setItem(
                    i, 0, QTableWidgetItem(str(i))
                )
                self.results_table.setItem(
                    i, 1, QTableWidgetItem(str(y_true.iloc[i]))
                )
                self.results_table.setItem(
                    i, 2, QTableWidgetItem(str(y_pred[i]))
                )
                
            self.export_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error making predictions: {str(e)}")
            
    def export_predictions(self):
        """Export predictions to a CSV file."""
        try:
            # Get predictions from results table
            rows = self.results_table.rowCount()
            predictions = []
            
            for i in range(rows):
                predictions.append({
                    'Index': self.results_table.item(i, 0).text(),
                    'Actual': self.results_table.item(i, 1).text(),
                    'Predicted': self.results_table.item(i, 2).text()
                })
                
            # Create DataFrame and export via file dialog
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Predictions", "predictions.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            if not file_path:
                return

            pred_df = pd.DataFrame(predictions)
            pred_df.to_csv(file_path, index=False)

            QMessageBox.information(
                self,
                "Success",
                f"Predictions exported to '{file_path}'"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error exporting predictions: {str(e)}"
            ) 