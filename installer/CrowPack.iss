#define MyAppName "CrowPack"
#define MyAppVersion "1.7"
#define MyAppDisplayVersion "v1.7"
#define MyAppPublisher "Crow Science Lab"
#define MyAppExeName "CrowPack.exe"

[Setup]
#ifdef ValidationBuild
AppId=CrowPack-Validation-150
Uninstallable=no
CreateUninstallRegKey=no
#else
AppId={{5E113A2E-C4E6-4B7B-9C59-08D6CBE5B95B}
#endif
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppDisplayVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion=1.7.0.0
VersionInfoCopyright=Copyright (c) 2026 Crow Science Lab
DefaultDirName={localappdata}\Programs\CrowPack
DefaultGroupName=CrowPack
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=CrowPack-v1.7-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\CrowPack.ico
CloseApplications=yes
SetupLogging=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\CrowPack\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
#ifndef ValidationBuild
Name: "{group}\CrowPack"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\CrowPack"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
#endif

[InstallDelete]
; Only obsolete shortcuts owned by this application, not user files.
Type: files; Name: "{autodesktop}\Crow Pack.lnk"
Type: files; Name: "{autoprograms}\Crow Pack\Crow Pack.lnk"

[Run]
#ifndef ValidationBuild
Filename: "{app}\{#MyAppExeName}"; Parameters: "--register"; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,CrowPack}"; Flags: nowait postinstall skipifsilent
#endif

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--unregister"; Flags: runhidden waituntilterminated; RunOnceId: "CrowPackUnregister"
