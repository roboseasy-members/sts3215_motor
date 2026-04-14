@echo off
REM =================================================================
REM  STS3215 Motor Test - Windows EXE Build Script
REM  Run from: appbuild\windows directory
REM =================================================================
setlocal enabledelayedexpansion
chcp 65001 >nul

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..
set APP_NAME=sts3215-motor-test

echo =========================================
echo  Building STS3215 Motor Test (Windows)
echo =========================================

REM ---- 1. Check Python ---------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    echo        Please install Python 3.10+ and try again.
    exit /b 1
)

REM ---- 2. Setup venv and install deps ------------------------------
echo [1/3] Setting up virtual environment and installing dependencies...
if not exist "%SCRIPT_DIR%.venv" (
    python -m venv "%SCRIPT_DIR%.venv"
)
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"

python -m pip install --upgrade pip --quiet
python -m pip install pyinstaller pyqt6 pyserial st3215 --quiet

REM ---- 3. Run PyInstaller ------------------------------------------
echo [2/3] Running PyInstaller...
cd /d "%SCRIPT_DIR%"
pyinstaller --clean --noconfirm motor_check_gui.spec

if not exist "%SCRIPT_DIR%dist\%APP_NAME%.exe" (
    echo ERROR: Build failed - %SCRIPT_DIR%dist\%APP_NAME%.exe not found
    exit /b 1
)

REM ---- 4. Done -----------------------------------------------------
echo [3/3] Build complete!
echo.
echo Output file:
echo   %SCRIPT_DIR%dist\%APP_NAME%.exe
echo.
echo Double-click the exe above to run the app.

endlocal
