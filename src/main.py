"""
Main entry point for the DataLens application.
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
from ui.resource_utils import resource_path
from ui.logging_utils import init_logging, get_logger


logger = get_logger(__name__)


def _ensure_ico(assets_dir):
    """
    Generate a proper multi-size .ico from DataLens_Logo.png.
    Always regenerates to ensure the correct logo is used.
    Returns the path to the .ico file.
    """
    ico_path = os.path.join(assets_dir, 'DataLens_Logo.ico')
    source_png = os.path.join(assets_dir, 'DataLens_Logo.png')

    if not os.path.exists(source_png):
        return ico_path if os.path.exists(ico_path) else None

    try:
        from PIL import Image
        img = Image.open(source_png).convert('RGBA')
        # Pad to square for proper icon rendering
        w, h = img.size
        size = max(w, h)
        square = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        square.paste(img, ((size - w) // 2, (size - h) // 2))
        square.save(ico_path, format='ICO',
                    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    except Exception:
        logger.exception("Failed to generate .ico at %s", ico_path)

    return ico_path if os.path.exists(ico_path) else None


def _ensure_cropped_logo(assets_dir):
    """
    Crop DataLens_Logo.png to its tight content bounding box and save
    as DataLens_Logo_cropped.png.  Always regenerates to stay in sync.
    """
    src = os.path.join(assets_dir, 'DataLens_Logo.png')
    dst = os.path.join(assets_dir, 'DataLens_Logo_cropped.png')

    if not os.path.exists(src):
        return

    try:
        from PIL import Image
        img = Image.open(src).convert('RGBA')
        bbox = img.getbbox()
        if bbox:
            cropped = img.crop(bbox)
            padded_size = (cropped.width + 8, cropped.height + 8)
            padded = Image.new('RGBA', padded_size, (0, 0, 0, 0))
            padded.paste(cropped, (4, 4))
            padded.save(dst)
    except Exception:
        logger.exception("Failed to generate cropped logo at %s", dst)


def main():
    """Initialize and run the application."""
    log_path = init_logging()
    logger.info("Starting DataLens (log: %s)", log_path)
    # Step 1: Set AppUserModelID BEFORE QApplication (critical for Windows taskbar icon)
    if platform.system() == 'Windows':
        try:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID('DataLens.App.1.0')
        except Exception:
            logger.exception("Failed to set AppUserModelID")

        # Fix DLL loading issue with Anaconda Python
        venv_scripts = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'venv', 'Scripts')
        if os.path.exists(venv_scripts):
            current_path = os.environ.get('PATH', '')
            if venv_scripts not in current_path:
                os.environ['PATH'] = venv_scripts + os.pathsep + current_path

    plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path

    # Step 2: Locate the packaged icon.
    # NOTE: Desktop/start-menu icons come from the EXE's embedded icon
    # (set by PyInstaller at build time). Runtime regeneration does not
    # affect shortcut icons, and frozen builds cannot reliably write into
    # the PyInstaller extraction directory (sys._MEIPASS).
    ico_path = resource_path("assets", "DataLens_Logo.ico")

    # In development only, regenerate derived assets to keep them in sync.
    if not getattr(sys, "frozen", False):
        assets_dir = resource_path("assets")
        generated_ico = _ensure_ico(assets_dir)
        if generated_ico:
            ico_path = generated_ico
        _ensure_cropped_logo(assets_dir)
    elif not os.path.exists(ico_path):
        logger.warning("Bundled icon not found at %s", ico_path)

    # Step 3: Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("DataLens")
    app.setOrganizationName("DataAnalysis")
    app.setOrganizationDomain("dataanalysis.app")

    # Step 4: Set icon on QApplication (all windows inherit this)
    if ico_path and os.path.exists(ico_path):
        app_icon = QIcon(ico_path)
        app.setWindowIcon(app_icon)

    # Theme is applied by MainWindow via the centralized theme system
    app.setStyle('Fusion')

    # Step 5: Create and show window (icon also set on MainWindow in its init)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main() 