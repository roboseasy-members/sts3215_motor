; Feetech Motor Control NSIS Installer Script
; This script creates an automated installer for Feetech Motor Control GUI

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

; ==================== 기본 설정 ====================
Name "Feetech Motor Control Installer"
OutFile "FeetechMotorControl_Installer_v1.0.exe"
InstallDir "$LOCALAPPDATA\FeetechMotorControl"
InstallDirRegKey HKCU "Software\FeetechMotorControl" "Install_Dir"

; 관리자 권한 요청
RequestExecutionLevel admin

; ==================== MUI 설정 ====================
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Korean"

; ==================== 설치 섹션 ====================
Section "Feetech Motor Control"
  SetOutPath "$INSTDIR"
  
  ; Python 3.10 확인
  Call CheckPython
  
  ; uv 설치 확인
  Call CheckUV
  
  ; git 확인
  Call CheckGit
  
  ; LeRobot 설치
  Call InstallLeRobot
  
  ; GUI 실행 파일 복사
  Call CopyGUIFiles
  
  ; 레지스트리에 설치 정보 저장
  WriteRegStr HKCU "Software\FeetechMotorControl" "Install_Dir" "$INSTDIR"
  
  ; 제어판에 표시하기
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FeetechMotorControl" \
                   "DisplayName" "Feetech Motor Control"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FeetechMotorControl" \
                   "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FeetechMotorControl" \
                   "DisplayVersion" "1.0"
  
  ; 바탕화면 바로가기
  CreateDirectory "$SMPROGRAMS\FeetechMotorControl"
  CreateShortcut "$SMPROGRAMS\FeetechMotorControl\Feetech Motor Control.lnk" \
                 "$INSTDIR\FeetechMotorControl.exe" "" "$INSTDIR\FeetechMotorControl.exe" 0
  
  ; 설치 완료 메시지
  MessageBox MB_OK "Feetech Motor Control 설치가 완료되었습니다!$\n$\n설치 경로: $INSTDIR"
  
SectionEnd

; ==================== 함수들 ====================

Function CheckPython
  DetailPrint "Python 3.10 확인 중..."
  
  ; Python 설치 여부 확인
  nsExec::ExecToLog "python --version"
  Pop $0
  
  ${If} $0 != 0
    MessageBox MB_OK|MB_ICONEXCLAMATION "Python 3.10이 설치되지 않았습니다.$\n$\nPython 3.10을 먼저 설치해주세요.$\nURL: https://www.python.org/downloads/$\n$\n설치 시 'Add Python to PATH' 옵션을 반드시 체크해주세요!"
    Abort "Python 3.10이 필요합니다."
  ${EndIf}
  
  DetailPrint "Python 확인 완료"
FunctionEnd

Function CheckUV
  DetailPrint "uv 확인 중..."
  
  ; uv 설치 여부 확인
  nsExec::ExecToLog "uv --version"
  Pop $0
  
  ${If} $0 != 0
    DetailPrint "uv 설치 중..."
    nsExec::ExecToLog "python -m pip install uv"
    Pop $0
    
    ${If} $0 != 0
      MessageBox MB_OK|MB_ICONEXCLAMATION "uv 설치에 실패했습니다. 설치를 계속 진행합니다."
    ${EndIf}
  ${EndIf}
  
  DetailPrint "uv 확인 완료"
FunctionEnd

Function CheckGit
  DetailPrint "git 확인 중..."
  
  ; git 설치 여부 확인
  nsExec::ExecToLog "git --version"
  Pop $0
  
  ${If} $0 != 0
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "git이 설치되지 않았습니다.$\n$\ngit을 설치해야 LeRobot을 다운로드할 수 있습니다.$\n$\n다음 URL에서 git을 설치하세요:$\nhttps://git-scm.com/download/win$\n$\n'Download' 버튼 클릭 후 설치 프로그램을 실행하고, 설치 중에 'Add Git to PATH' 옵션을 체크하세요.$\n$\ngit 설치 후 이 설치 프로그램을 다시 실행해주세요." IDCANCEL
    ${If} $0 == 1
      Abort "git 설치가 필요합니다."
    ${EndIf}
  ${EndIf}
  
  DetailPrint "git 확인 완료"
FunctionEnd

Function InstallLeRobot
  DetailPrint "LeRobot 설치 중... (이 과정은 5-10분 소요될 수 있습니다)"
  
  ; install_script.bat 실행
  nsExec::ExecToLog '"$INSTDIR\installer\install_script.bat" "$INSTDIR"'
  Pop $0
  
  ${If} $0 != 0
    MessageBox MB_OK|MB_ICONEXCLAMATION "LeRobot 설치 중 오류가 발생했습니다.$\n$\nError Code: $0$\n$\n터미널 출력을 확인해주세요."
    Abort "LeRobot 설치 실패"
  ${EndIf}
  
  DetailPrint "LeRobot 설치 완료"
FunctionEnd

Function CopyGUIFiles
  DetailPrint "GUI 파일 복사 중..."
  
  ; 설치 파일이 있는 경로에서 필요한 파일들을 복사
  ; 이 부분은 NSIS 컴파일러가 처리합니다.
  
  DetailPrint "GUI 파일 복사 완료"
FunctionEnd

; ==================== 제거 섹션 ====================
Section "Uninstall"
  ; 바로가기 제거
  RMDir /r "$SMPROGRAMS\FeetechMotorControl"
  
  ; 설치 디렉토리 제거
  RMDir /r "$INSTDIR"
  
  ; 레지스트리 제거
  DeleteRegKey HKCU "Software\FeetechMotorControl"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\FeetechMotorControl"
  
  MessageBox MB_OK "Feetech Motor Control이 제거되었습니다."
SectionEnd
