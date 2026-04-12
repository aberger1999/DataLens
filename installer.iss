[Setup]
AppName=DataLens
AppVersion=1.0
AppPublisher=DataLens
DefaultDirName={autopf}\DataLens
DefaultGroupName=DataLens
OutputDir=installer_output
OutputBaseFilename=DataLens_1.0_Setup
SetupIconFile=assets\DataLens_Logo.ico
UninstallDisplayIcon={app}\DataLens.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\DataLens\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DataLens"; Filename: "{app}\DataLens.exe"; IconFilename: "{app}\DataLens.exe"
Name: "{group}\Uninstall DataLens"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DataLens"; Filename: "{app}\DataLens.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DataLens.exe"; Description: "Launch DataLens"; Flags: nowait postinstall skipifsilent
