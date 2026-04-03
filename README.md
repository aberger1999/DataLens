# Data Analysis Application

A modern, cross-platform desktop application for data analysis built with PyQt6. Features a dark theme UI and comprehensive data analysis tools including visualization, statistical analysis, and machine learning capabilities.

## Features

- **Data Import/Export**: Support for CSV, Excel, and other common data formats
- **Data Visualization**: Interactive charts and plots using Matplotlib and Seaborn
- **Statistical Analysis**: Comprehensive statistical tools powered by SciPy
- **Machine Learning**: Built-in ML capabilities using scikit-learn
- **Modern UI**: Dark theme with intuitive interface
- **Cross-Platform**: Runs on both Windows and macOS

## System Requirements

- **Windows**: Windows 10 or later
- **macOS**: macOS 10.14 (Mojave) or later
- **Python**: 3.8 or later (for development only)

## Installation

### For End Users

#### Windows (Recommended - Installer)

**Option 1: Using the Installer (Easiest)**
1. Download `DataAnalysisApp-Setup-1.0.0.exe` from the [releases page](../../releases)
2. Double-click the installer and follow the setup wizard
3. Launch the app from:
   - Start Menu → Data Analysis Application
   - Desktop shortcut (if selected during installation)

**Option 2: Portable Version**
1. Download `DataAnalysisApp-Portable-Windows.zip` from the [releases page](../../releases)
2. Extract the ZIP file to any location
3. Run `data_analysis_app.exe` from the extracted folder

**Uninstalling**
- Go to Settings → Apps → Apps & features
- Find "Data Analysis Application" and click Uninstall

#### macOS
1. Download the latest release from the [releases page](../../releases)
2. Open the DMG file
3. Drag `DataAnalysisApp.app` to your Applications folder
4. Run the application from Applications

**First Launch on macOS**
- Right-click the app and select "Open" the first time
- If you see "App is damaged", run: `xattr -cr /Applications/DataAnalysisApp.app`

### For Developers

1. Clone the repository:
```bash
git clone <repository-url>
cd Data-Analysis-Application
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
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

### Windows Installer

**Prerequisites:**
- Python 3.8 or later
- [Inno Setup](https://jrsoftware.org/isdl.php) (for creating installer)

**Build Steps:**

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

2. Run the build script:
```powershell
.\build_installer.ps1
```

Or using Command Prompt:
```cmd
build_installer.bat
```

3. The installer will be created in `installer/DataAnalysisApp-Setup-1.0.0.exe`

**What the build script does:**
- Bundles the application with PyInstaller
- Fixes Qt DLL paths automatically
- Creates a professional Windows installer with Inno Setup

**Alternative Build Methods:**
- See `INSTALLER_SOLUTION.md` for the complete guide
- See `MSI_INSTALLER_GUIDE.md` for WiX Toolset MSI creation

### Windows Portable (No Installer)

```bash
# Build with PyInstaller
pyinstaller data_analysis_app.spec --noconfirm

# Fix Qt DLLs
Copy-Item "dist\data_analysis_app\_internal\Qt6*.dll" "dist\data_analysis_app\" -Force

# The portable app is now in dist/data_analysis_app/
```

### macOS

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Make the build script executable and run it:
```bash
chmod +x build_mac.sh
./build_mac.sh
```

3. The application bundle will be created in `dist/DataAnalysisApp.app`

4. (Optional) Create a DMG installer:
```bash
hdiutil create -volname DataAnalysisApp -srcfolder dist/DataAnalysisApp.app -ov -format UDZO dist/DataAnalysisApp.dmg
```

## Project Structure

```
Data-Analysis-Application/
├── src/
│   ├── main.py              # Application entry point
│   └── ui/                  # UI components
│       ├── main_window.py   # Main application window
│       └── components/      # Reusable UI components
├── installer/               # Installer configuration files
│   ├── inno_setup.iss      # Inno Setup script
│   ├── wix_config.wxs      # WiX Toolset configuration
│   └── README.md           # Installer quick reference
├── assets/                  # Application icons and resources
├── requirements.txt         # Python dependencies
├── data_analysis_app.spec   # PyInstaller configuration
├── build_installer.ps1      # Windows installer build script
├── build_installer.bat      # Windows installer build script (CMD)
├── build_mac.sh            # macOS build script
├── INSTALLER_SOLUTION.md   # Complete installer guide
└── README.md               # This file
```

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document functions and classes with docstrings

### Adding New Features
1. Create a new branch for your feature
2. Implement the feature in the appropriate module
3. Test thoroughly on both Windows and macOS if possible
4. Submit a pull request

### Building Installers for Distribution

**For Windows:**
1. Update version in `installer/inno_setup.iss` (line 5)
2. Run `.\build_installer.ps1`
3. Test the installer on a clean Windows machine
4. Upload to releases

**For macOS:**
1. Run `./build_mac.sh`
2. Create DMG with `hdiutil create`
3. Test on a clean macOS machine
4. Upload to releases

## Dependencies

- **PyQt6**: Modern Qt6 bindings for Python
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib**: Data visualization
- **seaborn**: Statistical data visualization
- **scipy**: Scientific computing
- **scikit-learn**: Machine learning
- **openpyxl**: Excel file support
- **PyInstaller**: Application packaging

## Troubleshooting

### Windows

**Issue**: Application doesn't start
- Make sure you have the Visual C++ Redistributable installed
- Try running as administrator
- If using portable version, ensure all files are extracted

**Issue**: "DLL load failed" error
- This is fixed in the latest build
- If building from source, make sure to run the build script (not just PyInstaller)

**Issue**: High DPI scaling issues
- The application should automatically handle high DPI displays
- If issues persist, try adjusting Windows display scaling settings

**Issue**: Installer won't run
- Right-click the installer and select "Run as administrator"
- Check Windows SmartScreen settings

### macOS

**Issue**: "App is damaged and can't be opened"
- This is a Gatekeeper issue. Run: `xattr -cr /path/to/DataAnalysisApp.app`

**Issue**: Application won't open
- Right-click the app and select "Open" the first time
- Check System Preferences > Security & Privacy

## Documentation

- **`INSTALLER_SOLUTION.md`** - Complete guide to the Windows installer setup
- **`MSI_INSTALLER_GUIDE.md`** - Alternative MSI creation methods (WiX, cx_Freeze)
- **`DISTRIBUTION.md`** - Distribution and packaging guidelines
- **`DEVELOPMENT.md`** - Development setup and guidelines
- **`installer/README.md`** - Quick reference for building installers

## License

Licensed under the Open Software License version 3.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.

## Version History

### Version 1.0.0
- Initial release
- Cross-platform support for Windows and macOS
- Modern dark theme UI
- Core data analysis features
- Professional Windows installer with Inno Setup
- Portable Windows version available
