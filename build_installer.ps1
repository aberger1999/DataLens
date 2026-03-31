# PowerShell script to build installer using PyInstaller + Inno Setup
# For PyQt5 Data Analysis Application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Data Analysis Application Installer Builder" -ForegroundColor Cyan
Write-Host "Using PyInstaller + Inno Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build with PyInstaller
Write-Host "[1/2] Building application with PyInstaller..." -ForegroundColor Yellow
pyinstaller data_analysis_app.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Application built successfully!" -ForegroundColor Green
Write-Host ""

# Step 2: Check if Inno Setup is installed
Write-Host "[2/2] Creating installer with Inno Setup..." -ForegroundColor Yellow

$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Inno Setup Not Found" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Your application has been built successfully in the 'dist' folder!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To create an installer, please:" -ForegroundColor White
    Write-Host "1. Download Inno Setup from: https://jrsoftware.org/isdl.php" -ForegroundColor Cyan
    Write-Host "2. Install Inno Setup" -ForegroundColor Cyan
    Write-Host "3. Run this script again" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OR manually:" -ForegroundColor White
    Write-Host "1. Open Inno Setup" -ForegroundColor Cyan
    Write-Host "2. Open the file: installer\inno_setup.iss" -ForegroundColor Cyan
    Write-Host "3. Click Build > Compile" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "For now, you can distribute the entire 'dist\data_analysis_app' folder" -ForegroundColor Yellow
    Write-Host ""
} else {
    & $innoSetupPath "installer\inno_setup.iss"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Inno Setup compilation failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "BUILD COMPLETE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    $installerFile = Get-ChildItem -Path "installer_output" -Filter "DataAnalysisApp-Setup-*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($installerFile) {
        Write-Host "Installer location: $($installerFile.FullName)" -ForegroundColor Cyan
    } else {
        Write-Host "Installer location: installer_output\DataAnalysisApp-Setup-1.0.0.exe" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "You can now distribute this installer to users!" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
