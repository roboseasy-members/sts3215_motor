@echo off
REM ============================================
REM Feetech Motor Control - 자동 설치 스크립트
REM ============================================
REM 이 스크립트는 NSIS에서 호출되어 LeRobot을 자동으로 설치합니다.

setlocal enabledelayedexpansion

REM 색상 설정 (Windows 10/11에서 지원)
color 0A

echo.
echo ============================================
echo  Feetech Motor Control 설치 시작
echo ============================================
echo.

REM 작업 디렉토리 설정
set INSTALL_DIR=%1
if "%INSTALL_DIR%"=="" (
    set INSTALL_DIR=%LOCALAPPDATA%\FeetechMotorControl
)

echo [단계 1/5] 설치 디렉토리 확인: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo 설치 디렉토리 생성 완료
)

REM Python 확인
echo.
echo [단계 2/5] Python 3.10 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python이 설치되지 않았습니다!
    echo Python 3.10을 먼저 설치하세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

REM uv 설치 확인
echo.
echo [단계 3/5] uv 설치 확인 중...
uv --version >nul 2>&1
if errorlevel 1 (
    echo uv가 설치되지 않았습니다. 설치 중...
    python -m pip install uv
    if errorlevel 1 (
        echo ERROR: uv 설치 실패!
        pause
        exit /b 1
    )
)
uv --version

REM git 확인
echo.
echo [단계 4/5] git 확인 중...
git --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: git이 설치되지 않았습니다!
    echo 다음 주소에서 git을 설치하세요:
    echo https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)
git --version

REM LeRobot 클론 및 설치
echo.
echo [단계 5/5] LeRobot 설치 중... (이 과정은 5-10분 소요될 수 있습니다)
cd /d "%INSTALL_DIR%"

REM LeRobot이 이미 있는지 확인
if exist "lerobot" (
    echo LeRobot이 이미 설치되어 있습니다.
    echo 업데이트를 진행합니다...
    cd lerobot
    git pull origin main
    if errorlevel 1 (
        echo.
        echo WARNING: LeRobot 업데이트 중 오류가 발생했습니다.
        echo 설치를 계속 진행합니다...
    )
) else (
    echo LeRobot을 클론하는 중...
    git clone https://github.com/huggingface/lerobot.git
    if errorlevel 1 (
        echo ERROR: LeRobot 클론 실패!
        echo 인터넷 연결을 확인하세요.
        pause
        exit /b 1
    )
    cd lerobot
)

REM 가상환경 생성 (이미 있으면 스킵)
if not exist ".venv" (
    echo 가상환경을 생성하는 중...
    uv venv --python 3.10
    if errorlevel 1 (
        echo ERROR: 가상환경 생성 실패!
        pause
        exit /b 1
    )
)

REM 가상환경 활성화
echo 가상환경을 활성화하는 중...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: 가상환경 활성화 실패!
    pause
    exit /b 1
)

REM LeRobot feetech 모듈 설치
echo Feetech 모터 라이브러리 설치 중...
uv pip install -e ".[feetech]"
if errorlevel 1 (
    echo ERROR: LeRobot feetech 설치 실패!
    echo 설치 로그를 확인하세요.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  설치 완료! ✅
echo ============================================
echo.
echo LeRobot이 %INSTALL_DIR%\lerobot에 설치되었습니다.
echo.
echo 다음 단계:
echo 1. feetech_motor_gui 폴더 확인
echo 2. FeetechMotorControl.exe 실행
echo.

REM 설치 완료
endlocal
exit /b 0
