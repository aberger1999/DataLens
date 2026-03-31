"""
Main entry point for the Data Analysis Application.
This module initializes the PyQt5 application and launches the main window.
Cross-platform support for Windows and macOS.
"""

import sys
import os
import warnings
import platform

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QLibraryInfo, Qt
from PyQt5.QtGui import QPalette, QColor, QIcon
from ui.main_window import MainWindow

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller.
    
    Args:
        relative_path: Path relative to the project root
        
    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Development mode - use the project root directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)

def main():
    """Initialize and run the application."""
    if platform.system() == 'Windows':
        try:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID('com.dataanalysis.app')
        except:
            pass

        # Fix DLL loading issue with Anaconda Python
        # Prioritize virtual environment's DLLs over Anaconda's base environment
        venv_scripts = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'venv', 'Scripts')
        if os.path.exists(venv_scripts):
            current_path = os.environ.get('PATH', '')
            if venv_scripts not in current_path:
                os.environ['PATH'] = venv_scripts + os.pathsep + current_path

    plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path

    app = QApplication(sys.argv)
    app.setApplicationName("Data Analysis Application")
    app.setOrganizationName("DataAnalysis")
    app.setOrganizationDomain("dataanalysis.app")

    icon_path = resource_path('icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Theme is applied by MainWindow via the centralized theme system
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main() 