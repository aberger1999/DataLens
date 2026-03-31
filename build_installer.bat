@echo off
REM Build script for creating installer using PyInstaller + Inno Setup
REM For PyQt5 Data Analysis Application

echo ========================================
echo Data Analysis Application Installer Builder
echo Using PyInstaller + Inno Setup
echo ========================================
echo.

REM Step 1: Build with PyInstaller
echo [1/2] Building application with PyInstaller...
pyinstaller data_analysis_app.spec --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed!
    exit /b 1
)
echo Application built successfully!
echo.

REM Step 2: Check if Inno Setup is installed
echo [2/2] Creating installer with Inno Setup...

set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not exist "%INNO_PATH%" (
    echo.
    echo ========================================
    echo Inno Setup Not Found
    echo ========================================
    echo.
    echo Your application has been built successfully in the 'dist' folder!
    echo.
    echo To create an installer, please:
    echo 1. Download Inno Setup from: https://jrsoftware.org/isdl.php
    echo 2. Install Inno Setup
    echo 3. Run this script again
    echo.
    echo OR manually:
    echo 1. Open Inno Setup
    echo 2. Open the file: installer\inno_setup.iss
    echo 3. Click Build ^> Compile
    echo.
    echo For now, you can distribute the entire 'dist\data_analysis_app' folder
    echo.
    goto :end
)

"%INNO_PATH%" "installer\inno_setup.iss"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Inno Setup compilation failed!
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo Installer location: installer_output\DataAnalysisApp-Setup-1.0.0.exe
echo.
echo You can now distribute this installer to users!
echo.

:end
pause
