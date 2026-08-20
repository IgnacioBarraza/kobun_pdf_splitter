; Instalador de Windows para Kobun, hecho con Inno Setup.
;
; Requiere el ejecutable ya construido en dist\kobun.exe:
;
;     python scripts/build_app.py
;     iscc packaging\kobun.iss
;
; Se compila en Windows: Inno Setup no corre en Linux. La salida queda en
; dist\installer\.
;
; Lo que agrega sobre el .exe suelto: acceso directo en el menú Inicio,
; asociación con archivos PDF, entrada de desinstalación en el panel de
; control, y elección del directorio de instalación.

#define MiNombre "Kobun"
#define MiVersion "0.2.0"
#define MiAutor "Ignacio Barraza"
#define MiEjecutable "kobun.exe"

[Setup]
; El AppId identifica al programa entre versiones: cambiarlo haría que una
; actualización se instale al lado en vez de reemplazar a la anterior.
AppId={{8F3A5C7E-2B94-4D61-9E48-1A7C6B0D3F52}
AppName={#MiNombre}
AppVersion={#MiVersion}
AppPublisher={#MiAutor}
DefaultDirName={autopf}\{#MiNombre}
DefaultGroupName={#MiNombre}
OutputDir=..\dist\installer
OutputBaseFilename=kobun-{#MiVersion}-windows-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Sin privilegios de administrador: instala para el usuario actual, así no
; aparece el diálogo de UAC.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\kobun\shared\icons\kobun.ico
UninstallDisplayIcon={app}\{#MiEjecutable}
LicenseFile=..\LICENSE

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "pdfassoc"; Description: "Abrir archivos PDF con {#MiNombre}"; GroupDescription: "Asociaciones:"; Flags: unchecked

[Files]
Source: "..\dist\{#MiEjecutable}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MiNombre}"; Filename: "{app}\{#MiEjecutable}"
Name: "{group}\Desinstalar {#MiNombre}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MiNombre}"; Filename: "{app}\{#MiEjecutable}"; Tasks: desktopicon

[Registry]
; Kobun se ofrece como opción para PDFs sin robarle la asociación por defecto
; al visor que el usuario ya tenga: se registra en OpenWithProgids y en el menú
; contextual, no como handler principal.
Root: HKCU; Subkey: "Software\Classes\Kobun.pdf"; ValueType: string; ValueName: ""; ValueData: "Documento PDF"; Flags: uninsdeletekey; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\Kobun.pdf\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MiEjecutable},0"; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\Kobun.pdf\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MiEjecutable}"" ""%1"""; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "Kobun.pdf"; ValueData: ""; Flags: uninsdeletevalue; Tasks: pdfassoc

[Run]
Filename: "{app}\{#MiEjecutable}"; Description: "{cm:LaunchProgram,{#MiNombre}}"; Flags: nowait postinstall skipifsilent
