#define AppName "FREE HOUSE BAR & RESTAURANT POS"
#define AppVersion "1.0.0"
#define AppPublisher "FREE HOUSE BAR & RESTAURANT"

[Setup]
AppId={{F873C971-BCBA-4434-83D7-2478649244A4}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\FREE HOUSE POS
DefaultGroupName={#AppName}
OutputDir=..\..\dist
OutputBaseFilename=FREE-HOUSE-POS-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
Uninstallable=yes

[Files]
Source: "..\..\dist\ChiwasLiquorPOS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\ChiwasLiquorPOS.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\ChiwasLiquorPOS.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\ChiwasLiquorPOS.exe"; Description: "Launch {#AppName}"; Flags: postinstall nowait skipifsilent
