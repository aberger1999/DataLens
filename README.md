# DataLens

A modern desktop data analysis application built with PyQt5. Features a workspace-based project system, dark and light themes, and comprehensive data analysis tools including visualization, statistical analysis, machine learning, and report generation.

## Features

- **Workspace Management**: Create and manage multiple project workspaces from a home screen
- **Data Import/Export**: Support for CSV, Excel, and other common data formats
- **Dataset Manager**: Import, load, rename, and delete datasets within a workspace
- **Data Preprocessing**: Clean and transform data with built-in tools
- **Feature Engineering**: Create new features, encode categoricals, and extract datetime components
- **Data Visualization**: Interactive charts and plots using Matplotlib and Seaborn
- **Statistical Analysis**: Comprehensive statistical tools powered by SciPy
- **Machine Learning**: Built-in ML capabilities using scikit-learn
- **Report Generation**: Generate PDF and HTML reports from your analysis
- **Dark & Light Themes**: Modern UI with theme switching support
- **Unsaved Changes Protection**: Confirmation dialogs prevent accidental data loss

## System Requirements

- **Windows**: Windows 10 or later

## Installation

### For End Users

1. Download `DataLens_1.0_Setup.exe` from the [releases page](../../releases)
2. Double-click the installer and follow the setup wizard
3. Launch the app from:
   - Start Menu > DataLens
   - Desktop shortcut (if selected during installation)

**Uninstalling**
- Go to Settings > Apps > Apps & features
- Find "DataLens" and click Uninstall

### For Developers

1. Clone the repository:
```bash
git clone <repository-url>
cd Data-Analysis-Application
```

2. Create a virtual environment:
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python src/main.py
```

## Building from Source

### Prerequisites
- Python 3.8 or later
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (for creating the installer)

### Build Steps

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Build the executable with PyInstaller:
```bash
pyinstaller DataLens.spec --clean --noconfirm
```

3. Create the Windows installer:
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

4. The installer will be created at `installer_output/DataLens_1.0_Setup.exe`

### Portable Version (No Installer)

After running the PyInstaller step above, the portable app is available in `dist/DataLens/`. Run `DataLens.exe` directly from that folder.

## Project Structure

```
Data-Analysis-Application/
├── src/
│   ├── main.py                          # Application entry point
│   └── ui/
│       ├── main_window.py               # Main application window
│       ├── theme.py                     # Centralized theme system
│       ├── data_manager.py              # Data loading and management
│       ├── dwm_helper.py               # Windows DWM integration
│       └── components/
│           ├── home_screen.py           # Home screen and workspace tiles
│           ├── workspace_view.py        # Workspace layout and data view
│           ├── dataset_manager_panel.py # Dataset management dialog
│           ├── preprocessing_panel.py   # Data preprocessing tools
│           ├── feature_engineering_panel.py # Feature engineering tools
│           ├── visualization_panel.py   # Chart and plot creation
│           ├── analysis_panel.py        # Statistical analysis
│           ├── machine_learning_panel.py # ML model training
│           ├── report_generator_panel.py # Report generation
│           ├── data_preview.py          # Data table preview
│           ├── modal.py                 # Reusable modal dialogs
│           └── workspace_manager_panel.py # Workspace management
├── assets/                              # Application icons and logos
├── templates/
│   └── report_template.html             # HTML report template
├── requirements.txt                     # Python dependencies
├── DataLens.spec               # PyInstaller configuration
├── version_info.txt                     # Windows version metadata
├── installer.iss                        # Inno Setup installer script
├── qt_runtime_hook.py                   # Qt runtime path configuration
└── README.md                            # This file
```

## Dependencies

- **PyQt5**: Qt5 bindings for Python (UI framework)
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib**: Data visualization
- **seaborn**: Statistical data visualization
- **scipy**: Scientific computing
- **scikit-learn**: Machine learning
- **openpyxl**: Excel file read/write support
- **xlrd**: Legacy Excel file support
- **jinja2**: HTML report templating
- **pillow**: Image processing (icon generation)
- **PyInstaller**: Application packaging

## Troubleshooting

**Application doesn't start**
- Make sure you have the Visual C++ Redistributable installed
- Try running as administrator

**Installer won't run**
- Right-click the installer and select "Run as administrator"
- If Windows SmartScreen blocks it, click "More info" then "Run anyway"

**High DPI scaling issues**
- The application handles high DPI displays automatically
- If issues persist, try adjusting Windows display scaling settings

## License

Licensed under the Open Software License version 3.0

## Version History

### Version 1.0
- Workspace-based project management with home screen
- Dark and light theme support
- Data import/export (CSV, Excel)
- Dataset manager with import, rename, and delete
- Data preprocessing and feature engineering
- Interactive data visualization
- Statistical analysis tools
- Machine learning model training
- PDF and HTML report generation
- Unsaved changes tracking with save confirmation dialogs
- Professional Windows installer
