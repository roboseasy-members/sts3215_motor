#!/usr/bin/env bash
#
# Roboseasy — Debian/Ubuntu .deb 패키지 빌드 스크립트
#
# PyInstaller 로 만든 단일 실행파일을 .deb 로 감싸서
# `sudo dpkg -i` / `sudo apt install ./파일.deb` 로 설치 가능하게 만든다.
#
# 사용법: (appbuild/linux/ 디렉토리에서)
#   ./build-deb.sh                    # 기본 버전(1.0.0)
#   VERSION=1.2.0 ./build-deb.sh      # 버전 지정
#
# 설치/제거:
#   sudo dpkg -i dist/roboseasy_1.0.0_amd64.deb
#   sudo apt install -f                # 의존성 자동 해결 (필요 시)
#   sudo apt remove roboseasy
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

APP_NAME="Roboseasy"                 # 파일/디렉토리/WMClass 에 사용
PKG_NAME="roboseasy"                 # Debian 패키지명은 소문자 관례
APP_DISPLAY_NAME="Roboseasy Motor Setup"
VERSION="${VERSION:-1.0.0}"
ARCH="$(dpkg --print-architecture)"
MAINTAINER="RoboSEasy <khw11044@gmail.com>"

BUILD_DIR="${SCRIPT_DIR}/build/deb"
DIST_DIR="${SCRIPT_DIR}/dist"
RESOURCE_DIR="${PROJECT_ROOT}/resource"
EXECUTABLE="${DIST_DIR}/${APP_NAME}"

echo "========================================="
echo " Building ${APP_NAME} .deb"
echo "   Version: ${VERSION}"
echo "   Arch:    ${ARCH}"
echo "========================================="

# ---- 1. 사전 확인 --------------------------------------------------------
if ! command -v dpkg-deb &>/dev/null; then
    echo "ERROR: dpkg-deb 를 찾을 수 없습니다. Debian/Ubuntu 계열에서 실행하세요."
    exit 1
fi

if [ ! -f "${EXECUTABLE}" ]; then
    echo "[1/4] dist/${APP_NAME} 가 없어 build.sh 를 먼저 실행합니다."
    "${SCRIPT_DIR}/build.sh"
else
    echo "[1/4] 기존 실행파일 재사용: ${EXECUTABLE}"
    echo "      (소스 변경이 있었다면 먼저 ./build.sh 로 재빌드하세요)"
fi

# ---- 2. 패키지 디렉토리 구조 생성 ----------------------------------------
echo "[2/4] 패키지 구조 생성..."
PKG_DIR="${BUILD_DIR}/${PKG_NAME}_${VERSION}_${ARCH}"
rm -rf "${PKG_DIR}"
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/opt/${APP_NAME}"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_DIR}/usr/share/pixmaps"

# 실행파일: /opt/Roboseasy/Roboseasy
cp "${EXECUTABLE}" "${PKG_DIR}/opt/${APP_NAME}/${APP_NAME}"
chmod 755 "${PKG_DIR}/opt/${APP_NAME}/${APP_NAME}"

# /usr/bin/Roboseasy -> /opt/Roboseasy/Roboseasy (PATH 노출)
ln -sf "/opt/${APP_NAME}/${APP_NAME}" "${PKG_DIR}/usr/bin/${APP_NAME}"

# 아이콘: 표준 경로 + 레거시 pixmaps 폴백
cp "${RESOURCE_DIR}/icon.png" "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
cp "${RESOURCE_DIR}/icon.png" "${PKG_DIR}/usr/share/pixmaps/${APP_NAME}.png"

# .desktop — StartupWMClass 로 실행 창과 매칭
cat > "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Exec=${APP_NAME}
Icon=${APP_NAME}
Categories=Utility;
Comment=STS3215 Servo Motor Test and Configuration Tool
Terminal=false
StartupWMClass=${APP_NAME}
StartupNotify=true
DESKTOP

# ---- 3. DEBIAN 메타데이터 -----------------------------------------------
echo "[3/4] DEBIAN 메타데이터 작성..."

# Installed-Size (KB 단위, control 파일 제외)
INSTALLED_SIZE=$(du -sk --exclude=DEBIAN "${PKG_DIR}" | awk '{print $1}')

cat > "${PKG_DIR}/DEBIAN/control" <<CONTROL
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: libc6, libxcb-cursor0
Description: STS3215 Servo Motor Test and Configuration Tool
 GUI application for setting up Feetech STS3215 servo motors and
 configuring SO-ARM 101 robot arms. Includes a motor ID assignment
 wizard, single-motor control panel, and full SO-ARM 101 monitoring
 with collision detection.
CONTROL

# postinst — 설치 후 아이콘/런처 캐시 갱신
cat > "${PKG_DIR}/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true
fi
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi
exit 0
POSTINST
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

# postrm — 제거 후 캐시 갱신
cat > "${PKG_DIR}/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    if [ -x /usr/bin/gtk-update-icon-cache ]; then
        gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true
    fi
    if [ -x /usr/bin/update-desktop-database ]; then
        update-desktop-database /usr/share/applications/ 2>/dev/null || true
    fi
fi
exit 0
POSTRM
chmod 755 "${PKG_DIR}/DEBIAN/postrm"

# ---- 4. .deb 빌드 --------------------------------------------------------
echo "[4/4] dpkg-deb 실행..."
DEB_OUT="${DIST_DIR}/${PKG_NAME}_${VERSION}_${ARCH}.deb"
# --root-owner-group : 빌드한 사용자와 무관하게 파일 소유자를 root:root 로
dpkg-deb --root-owner-group --build "${PKG_DIR}" "${DEB_OUT}"

echo ""
echo "========================================="
echo " 빌드 완료"
echo "========================================="
ls -lh "${DEB_OUT}"
echo ""
echo "설치:  sudo dpkg -i ${DEB_OUT}"
echo "       (의존성 누락 시: sudo apt install -f)"
echo "실행:  Roboseasy  (PATH 에 등록됨)"
echo "제거:  sudo apt remove ${PKG_NAME}"
