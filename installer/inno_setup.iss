; Inno Setup Script for Data Analysis Application
; Download Inno Setup from: https://jrsoftware.org/isdl.php

#define MyAppName "Data Analysis Application"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Alex Berger"
#define MyAppExeName "data_analysis_app.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".daa"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
AppId={{12345678-1234-1234-1234-123456789012}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\installer\license.txt
OutputDir=..\installer_output
OutputBaseFilename=DataAnalysisApp-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\data_analysis_app\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\data_analysis_app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Flags: nowait postinstall skipifsilent; Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"
