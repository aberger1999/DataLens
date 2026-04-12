# Building the DataLens Windows Installer

## Quick Start

### Using PyInstaller + Inno Setup

1. **Build the application:**
   ```bash
   pyinstaller data_analysis_app.spec --clean --noconfirm
   ```

2. **Create the installer:**
   ```bash
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

3. **Done!** The installer will be at `installer_output/DataLens_1.0_Setup.exe`

### Prerequisites

- Python 3.8+
- [Inno Setup 6](https://jrsoftware.org/isdl.php)

## What the Installer Includes

- DataLens application (DataLens.exe)
- All required dependencies bundled
- Start Menu shortcuts
- Optional desktop shortcut
- Uninstaller (via Add/Remove Programs)

## Updating the Version

1. Update version in `installer.iss` (AppVersion line)
2. Update version in `version_info.txt` (filevers and prodvers)
3. Rebuild with PyInstaller and Inno Setup

## Distribution

Share `DataLens_1.0_Setup.exe` with users. They double-click to install and the setup wizard handles the rest.
