#!/usr/bin/env bash
#
# Roboseasy — Linux 로컬 통합 스크립트
#
# 빌드된 AppImage를 현재 사용자 시스템에 통합한다:
#   - 앱 런처(메뉴/Activities)에 "Roboseasy" 등록
#   - 아이콘을 사용자 아이콘 테마에 설치
#   - 작업표시줄/Dock에서 올바른 아이콘 표시
#
# 사용법: (appbuild/linux/ 디렉토리에서)
#   ./integrate.sh            # 통합 설치
#   ./integrate.sh --remove   # 통합 제거
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP_NAME="Roboseasy"
APP_DISPLAY_NAME="Roboseasy Motor Setup"
APPIMAGE_PATH="${SCRIPT_DIR}/dist/${APP_NAME}.AppImage"
ICON_SRC="${PROJECT_ROOT}/resource/icon.png"

DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
DESKTOP_FILE="${DESKTOP_DIR}/${APP_NAME}.desktop"
ICON_FILE="${ICON_DIR}/${APP_NAME}.png"

if [ "${1:-}" = "--remove" ]; then
    echo "Roboseasy 통합 제거 중..."
    rm -f "${DESKTOP_FILE}" "${ICON_FILE}"
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
    gtk-update-icon-cache -f "${HOME}/.local/share/icons/hicolor/" 2>/dev/null || true
    echo "제거 완료."
    exit 0
fi

# 사전 확인
if [ ! -f "${APPIMAGE_PATH}" ]; then
    echo "ERROR: AppImage를 찾을 수 없습니다: ${APPIMAGE_PATH}"
    echo "       먼저 ./build.sh --appimage 로 빌드하세요."
    exit 1
fi
if [ ! -f "${ICON_SRC}" ]; then
    echo "ERROR: 아이콘을 찾을 수 없습니다: ${ICON_SRC}"
    exit 1
fi

# 실행권한 보장
chmod +x "${APPIMAGE_PATH}"

# 디렉토리 생성
mkdir -p "${DESKTOP_DIR}" "${ICON_DIR}"

# 아이콘 설치
cp "${ICON_SRC}" "${ICON_FILE}"

# .desktop 설치 — StartupWMClass 로 실행 창을 매칭해 올바른 아이콘을 표시
cat > "${DESKTOP_FILE}" <<DESKTOP
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Exec=${APPIMAGE_PATH}
Icon=${APP_NAME}
Categories=Utility;Development;
Comment=STS3215 Servo Motor Test and Configuration Tool
Terminal=false
StartupWMClass=${APP_NAME}
StartupNotify=true
DESKTOP

# 캐시 갱신
update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
gtk-update-icon-cache -f "${HOME}/.local/share/icons/hicolor/" 2>/dev/null || true

echo "========================================="
echo " 통합 완료!"
echo "========================================="
echo "  .desktop : ${DESKTOP_FILE}"
echo "  아이콘   : ${ICON_FILE}"
echo "  AppImage : ${APPIMAGE_PATH}"
echo ""
echo "이제 Super 키 → 'Roboseasy' 로 검색해 실행할 수 있습니다."
echo "제거하려면: ./integrate.sh --remove"
