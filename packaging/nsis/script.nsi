; pyFastPlot NSIS Setup Script
!define PRODUCT_NAME "pyFastPlot"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "pyFastPlot contributors"
!define PRODUCT_WEB_SITE "https://github.com/winsccssvly/pyFastPlot"
!define PRODUCT_EXE "pyFastPlot.exe"
!define PRODUCT_ICON "pyfastplot_icon_1_0_0.ico"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_EXE}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

RequestExecutionLevel admin
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!include "x64.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "..\..\assets\pyfastplot_icon.ico"
!define MUI_UNICON "..\..\assets\pyfastplot_icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Korean"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "pyFastPlot_v${PRODUCT_VERSION}_Win64_Setup.exe"
InstallDir "$PROGRAMFILES64\pyFastPlot"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
BrandingText " "
ShowInstDetails show
ShowUnInstDetails show

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "pyFastPlot requires 64-bit Windows."
    Abort
  ${EndIf}
  SetRegView 64
FunctionEnd

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer

  ; Includes the entire Nuitka standalone distribution folder recursively.
  File /r "..\..\build\main.dist\*"
  File /oname=${PRODUCT_ICON} "..\..\assets\pyfastplot_icon.ico"

  CreateDirectory "$SMPROGRAMS\pyFastPlot"
  Delete "$SMPROGRAMS\pyFastPlot\pyFastPlot.lnk"
  Delete "$DESKTOP\pyFastPlot.lnk"
  CreateShortCut "$SMPROGRAMS\pyFastPlot\pyFastPlot.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_ICON}" 0
  CreateShortCut "$DESKTOP\pyFastPlot.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_ICON}" 0
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${PRODUCT_EXE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_ICON}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section Uninstall
  RMDir /r "$INSTDIR"

  Delete "$DESKTOP\pyFastPlot.lnk"
  Delete "$SMPROGRAMS\pyFastPlot\pyFastPlot.lnk"
  RMDir "$SMPROGRAMS\pyFastPlot"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd

Function un.onInit
  SetRegView 64
FunctionEnd
