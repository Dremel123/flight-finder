; Windows installer for Flight Finder, compiled by build.py with Inno Setup 6.
; Installs for the current user only (no admin rights). Uninstalling keeps results in %APPDATA%\Flight Finder.
#ifndef Version
  #define Version "1.0.0"
#endif

[Setup]
AppId={{6F0C2B7E-3D4A-4E59-9C1B-2A8F5D7E1C34}
AppName=Flight Finder
AppVersion={#Version}
AppPublisher=Flight Finder
DefaultDirName={localappdata}\Programs\Flight Finder
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#Out}
OutputBaseFilename=FlightFinder-Setup
SetupIconFile=icons\icon.ico
UninstallDisplayIcon={app}\flight-finder.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#Src}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Flight Finder"; Filename: "{app}\flight-finder.exe"
Name: "{autodesktop}\Flight Finder"; Filename: "{app}\flight-finder.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\flight-finder.exe"; Description: "Open Flight Finder"; Flags: nowait postinstall skipifsilent
