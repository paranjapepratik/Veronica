; Veronica Windows Installer Script
; Built with NSIS (Nullsoft Scriptable Install System)
; Install NSIS from: https://nsis.sourceforge.io/

!define APP_NAME      "Veronica"
!define APP_VERSION   "3.0"
!define APP_PUBLISHER "Pratik Paranjape"
!define APP_URL       "https://github.com/paranjapepratik/Veronica"
!define APP_EXE       "Veronica.exe"
!define INSTALL_DIR   "$PROGRAMFILES64\Veronica"

;--------------------------------
; General settings
Name "${APP_NAME} ${APP_VERSION}"
OutFile "Veronica_Setup_v${APP_VERSION}.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin
BrandingText "${APP_NAME} v${APP_VERSION} by ${APP_PUBLISHER}"

;--------------------------------
; Pages shown during install
Page license
Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------
; License page
LicenseData "LICENSE.txt"

;--------------------------------
; Components
InstType "Full Install"

;--------------------------------
; Main section
Section "Veronica Application (required)" SecMain
    SectionIn RO       ; Required, cannot be deselected

    SetOutPath "$INSTDIR"

    ; Copy main executable
    File "dist\Veronica.exe"

    ; Copy icon
    File "veronica_icon.ico"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Write registry for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                     "DisplayVersion" "${APP_VERSION}"

    ; Store install path in registry
    WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"

SectionEnd

;--------------------------------
; Desktop shortcut (optional)
Section "Desktop Shortcut" SecDesktop
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" \
                   "$INSTDIR\${APP_EXE}" "" \
                   "$INSTDIR\veronica_icon.ico"
SectionEnd

;--------------------------------
; Start Menu shortcut (optional)
Section "Start Menu Shortcut" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
                    "$INSTDIR\${APP_EXE}" "" \
                    "$INSTDIR\veronica_icon.ico"
    CreateShortcut  "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" \
                    "$INSTDIR\Uninstall.exe"
SectionEnd

;--------------------------------
; Uninstaller
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\veronica_icon.ico"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir  "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir  "$SMPROGRAMS\${APP_NAME}"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"

    MessageBox MB_OK "Veronica has been uninstalled successfully."
SectionEnd

;--------------------------------
; Descriptions shown on components page
LangString DESC_SecMain      ${LANG_ENGLISH} "Veronica application (required)"
LangString DESC_SecDesktop   ${LANG_ENGLISH} "Add a shortcut to your Desktop"
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Add Veronica to your Start Menu"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain}      $(DESC_SecMain)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop}   $(DESC_SecDesktop)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
