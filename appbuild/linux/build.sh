#!/usr/bin/env bash
#
# STS3215 Motor Test — Linux 실행파일/AppImage 빌드 스크립트
#
# 실행 위치: appbuild/linux/ 디렉토리에서
# 사용법:
#   ./build.sh              # Standalone 실행파일만 빌드
#   ./build.sh --appimage   # 실행파일 + AppImage 빌드
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP_NAME="sts3215-motor-test"
APP_DISPLAY_NAME="STS3215 Motor Test"
DIST_DIR="${SCRIPT_DIR}/dist"
BUILD_DIR="${SCRIPT_DIR}/build"
RESOURCE_DIR="${PROJECT_ROOT}/resource"

echo "========================================="
echo " Building ${APP_DISPLAY_NAME} (Linux)"
echo "========================================="

# ---- 1. Python 확인 -------------------------------------------------------
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 가 설치되어 있지 않습니다. Python 3.10+ 를 설치하세요."
    exit 1
fi

echo "[1/4] 가상환경 및 의존성 설치..."
VENV_DIR="${SCRIPT_DIR}/.venv"
if [ ! -d "${VENV_DIR}" ]; then
    if command -v uv &>/dev/null; then
        uv venv "${VENV_DIR}"
    else
        python3 -m venv "${VENV_DIR}"
    fi
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

if command -v uv &>/dev/null; then
    UV_HTTP_TIMEOUT=300 uv pip install pyinstaller pyqt6 pyserial st3215 --quiet
else
    python3 -m pip install --upgrade pip --quiet
    python3 -m pip install pyinstaller pyqt6 pyserial st3215 --quiet
fi

# ---- 2. PyInstaller 실행 --------------------------------------------------
echo "[2/4] PyInstaller 실행..."
cd "${SCRIPT_DIR}"
pyinstaller --clean --noconfirm motor_check_gui.spec

EXECUTABLE="${DIST_DIR}/${APP_NAME}"
if [ ! -f "${EXECUTABLE}" ]; then
    echo "ERROR: 빌드 실패 — ${EXECUTABLE} 를 찾을 수 없음"
    exit 1
fi

echo "    실행파일 생성: ${EXECUTABLE}"
ls -lh "${EXECUTABLE}"

# ---- 3. AppImage 옵션 ----------------------------------------------------
if [ "${1:-}" = "--appimage" ]; then
    echo "[3/4] AppImage 빌드..."

    APPDIR="${BUILD_DIR}/${APP_NAME}.AppDir"
    rm -rf "${APPDIR}"
    mkdir -p "${APPDIR}/usr/bin"
    mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

    cp "${EXECUTABLE}" "${APPDIR}/usr/bin/${APP_NAME}"
    chmod +x "${APPDIR}/usr/bin/${APP_NAME}"

    if [ -f "${RESOURCE_DIR}/icon.png" ]; then
        cp "${RESOURCE_DIR}/icon.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
        cp "${RESOURCE_DIR}/icon.png" "${APPDIR}/${APP_NAME}.png"
    fi

    cat > "${APPDIR}/${APP_NAME}.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Exec=${APP_NAME}
Icon=${APP_NAME}
Categories=Utility;Development;
Comment=STS3215 Servo Motor Test and Configuration Tool
DESKTOP

    cat > "${APPDIR}/AppRun" <<'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/sts3215-motor-test" "$@"
APPRUN
    chmod +x "${APPDIR}/AppRun"

    APPIMAGETOOL="${BUILD_DIR}/appimagetool"
    if [ ! -f "${APPIMAGETOOL}" ]; then
        echo "    appimagetool 다운로드 중..."
        ARCH=$(uname -m)
        curl -fsSL -o "${APPIMAGETOOL}" \
            "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
        chmod +x "${APPIMAGETOOL}"
    fi

    APPIMAGE_OUT="${DIST_DIR}/${APP_NAME}-$(uname -m).AppImage"
    ARCH=$(uname -m) "${APPIMAGETOOL}" "${APPDIR}" "${APPIMAGE_OUT}"

    echo "    AppImage 생성: ${APPIMAGE_OUT}"
    ls -lh "${APPIMAGE_OUT}"
else
    echo "[3/4] AppImage 빌드 건너뜀 (--appimage 플래그로 활성화)"
fi

# ---- 4. 완료 -------------------------------------------------------------
echo "[4/4] 빌드 완료!"
echo ""
echo "결과물:"
echo "  실행파일: ${EXECUTABLE}"
if [ "${1:-}" = "--appimage" ]; then
    echo "  AppImage: ${DIST_DIR}/${APP_NAME}-$(uname -m).AppImage"
fi
echo ""
echo "실행: ${EXECUTABLE}"
