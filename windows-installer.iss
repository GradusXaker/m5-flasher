#define MyAppName "Gradus Flasher"
#define MyAppVersion "0.1.4"
#define MyAppPublisher "GradusXaker"
#define MyAppURL "https://github.com/GradusXaker/m5-flasher"
#define MyAppExeName "GradusFlasher.exe"

[Setup]
AppId={{5D12C457-1AA9-4E22-9D7B-21C81F33A902}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=dist
OutputBaseFilename=GradusFlasher-Setup-v0.1.4
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "portablemode"; Description: "Создать portable.ini рядом с приложением"; Flags: unchecked

[Files]
Source: "dist\GradusFlasher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  PortableFile: string;
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('portablemode') then
    begin
      PortableFile := ExpandConstant('{app}\portable.ini');
      SaveStringToFile(PortableFile, '[portable]' + #13#10 + 'enabled=true' + #13#10, False);
    end;
  end;
end;
