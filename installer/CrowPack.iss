#define MyAppName "Crow Pack"
#define MyAppVersion "1.0.11"
#define MyAppDisplayVersion "v1.0K"
#define MyAppPublisher "Crow Science Lab"
#define MyAppExeName "CrowPack.exe"

[Setup]
AppId={{5E113A2E-C4E6-4B7B-9C59-08D6CBE5B95B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppDisplayVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Crow Pack
DefaultGroupName=Crow Pack
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=CrowPack-v1.0K-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
SetupLogging=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕 화면 바로가기 만들기"; GroupDescription: "추가 바로가기:"; Flags: unchecked

[Files]
Source: "..\dist\CrowPack\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Crow Pack"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Crow Pack"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Crow Pack 실행"; Flags: nowait postinstall skipifsilent
