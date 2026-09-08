#define MyAppName "Crow Pack"
#define MyAppVersion "1.5.0"
#define MyAppDisplayVersion "v1.5.0"
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
DefaultDirName={localappdata}\Programs\Crow Pack
DefaultGroupName=Crow Pack
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=CrowPack-v1.5.0-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\crow_pack.ico
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
#ifndef ValidationBuild
Name: "{group}\Crow Pack"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Crow Pack"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
#endif

[Run]
#ifndef ValidationBuild
Filename: "{app}\{#MyAppExeName}"; Parameters: "--register"; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Parameters: "--default-apps"; Description: "압축파일 연결 설정 열기"; Flags: postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Description: "Crow Pack 실행"; Flags: nowait postinstall skipifsilent
#endif

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--unregister"; Flags: runhidden waituntilterminated; RunOnceId: "CrowPackUnregister"
