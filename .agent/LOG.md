# LOG.md

중요한 작업 로그를 시간 역순으로 기록. Claude 와 사용자가 **왜** 그 변경을 했는지 빠르게 되짚기 위한 문서.

> 일반 git log 로 충분한 사소한 변경은 여기 기록하지 않는다.
> 아키텍처 변경, 이름/규약 변경, 빌드 설정 변경, 버그의 근본 원인 규명 등을 기록.

---

## 템플릿

각 엔트리 형식:

```
## YYYY-MM-DD — 한 줄 제목

**무엇을**: 변경 사항 요약
**왜**: 동기/배경 (필수 — 나중에 되짚을 때 가장 중요)
**영향 범위**: 어떤 파일/동작이 바뀌는가
**주의**: 향후 작업 시 주의할 점 (있다면)
```

---

## 2026-04-22 — `.agent/` 문서 체계 도입

**무엇을**: 루트에 `CLAUDE.md`, `.agent/` 폴더에 `ARCHITECTURE.md` / `CONVENTIONS.md` / `BUILD.md` / `LOG.md` 를 생성.
**왜**: Claude Code 와 협업 시 매번 같은 구조·규약·빌드 함정을 재설명하는 비용을 줄이기 위해. `README.md` 는 최종 사용자용이므로 개발자/AI 용 문서를 분리.
**영향 범위**: 문서만 추가 — 런타임 동작 변화 없음.
**주의**: 새 규약/함정/아키텍처 변경 시 이 폴더의 문서를 최신으로 유지해야 함. 구식 문서는 없는 것보다 나쁠 수 있음.

---

## 2026-04-22 — 빌드 산출물 이름을 `Roboseasy` 로 통일

**무엇을**: 플랫폼별로 달랐던 빌드 산출물 이름을 `Roboseasy` 로 통일.
- Linux 실행파일: `sts3215-motor-test` → `Roboseasy`
- Linux AppImage: `sts3215-motor-test-<arch>.AppImage` → `Roboseasy.AppImage` (arch suffix 제거)
- Windows EXE: `Roboseasy-motorsetup.exe` → `Roboseasy.exe`

**왜**: 브랜딩 일관성. 사용자가 플랫폼에 관계없이 같은 이름의 바이너리를 받도록.

**영향 범위**:
- `appbuild/linux/build.sh` — `APP_NAME`, AppImage 출력 경로, AppRun heredoc (single-quote → escaped double-quote 로 바꿔 변수 확장 허용)
- `appbuild/windows/build.bat` — `APP_NAME`
- `appbuild/linux/motor_check_gui.spec` — `name=`
- `appbuild/windows/motor_check_gui.spec` — `name=`

**주의**:
- AppImage 파일명에서 `-<arch>` suffix 를 뺐으므로, 향후 x86_64/aarch64 를 동시에 배포하려면 수동으로 arch 를 붙여 구분해야 함.
- AppRun 이 과거엔 이름을 하드코딩했으나 이제 `${APP_NAME}` 을 heredoc 에서 확장한다 — heredoc 의 shell 변수(`$SELF`, `$HERE`, `$0`, `$@`)는 `\$` 로 이스케이프되어 런타임에 평가됨.

---

## 2026-04-22 — Linux 아이콘 표시 수정 (StartupWMClass + Qt setDesktopFileName)

**무엇을**:
- `main.py` 에 `app.setApplicationName("Roboseasy")` + `app.setDesktopFileName("Roboseasy")` 추가
- `appbuild/linux/build.sh` 의 AppImage 내부 `.desktop` 에 `StartupWMClass=Roboseasy`, `Terminal=false`, `StartupNotify=true` 추가
- `appbuild/linux/integrate.sh` 신규 — `~/.local/share/applications` + `~/.local/share/icons/hicolor/256x256/apps` 에 `.desktop`/아이콘 설치하는 헬퍼. `--remove` 옵션 지원.

**왜**: AppImage 실행 시 GNOME Shell/Ubuntu Dock 이 창을 `.desktop` 파일과 매칭하지 못해 타스크바에 기본 톱니바퀴 아이콘이 표시됐음. 원인은 (1) `.desktop` 에 `StartupWMClass` 없음, (2) Qt 창 메타데이터에 desktop file ID 가 안 박힘. AppImageLauncher 를 설치해 우회하려 했으나 해당 PPA 는 2024년에 deprecated 되어 사용 불가 (Ubuntu 24.04 noble 에 Release 파일 없음, `E: The repository ... does not have a Release file`).

**영향 범위**:
- 런타임: `main.py` 의 app 초기화 2 줄 추가 (Windows 동작엔 영향 없음 — setDesktopFileName 은 해당 플랫폼에서만 효과)
- 빌드: AppImage 내부 `.desktop` 에 3 필드 추가 — 기존 산출물과 호환
- 개발 워크플로우: `integrate.sh` 로 로컬 테스트 편의성 ↑, 사용자 배포 시 별도 도구(AppImageLauncher) 의존 ↓

**주의**:
- `setDesktopFileName` 인자("Roboseasy"), `.desktop` 파일명, `StartupWMClass` 값 **세 가지가 모두 일치**해야 함. 앱 이름을 바꾸면 `main.py` + `build.sh` + 빌드 산출물명까지 동기화 필요.
- `integrate.sh` 는 현재 사용자 홈(`~/.local/...`)에만 설치 — system-wide 설치는 의도적으로 범위 밖.
- AppImageLauncher PPA (`ppa:appimagelauncher-team/stable`) 는 앞으로 쓰지 말 것. 공식 discussion: https://github.com/TheAssassin/AppImageLauncher/discussions/706

---

## 2026-04-22 — .deb 패키지 빌드 추가

**무엇을**: `appbuild/linux/build-deb.sh` 신규 — 기존 `build.sh` 산출물(`dist/Roboseasy`)을 `dpkg-deb --build` 로 감싸 `roboseasy_<ver>_<arch>.deb` 생성. AppImage 는 그대로 유지.

**왜**: 사용자가 VSCode/Slack 처럼 `sudo dpkg -i` 로 시스템 전역 설치하고 앱 런처에 자동 등록되는 배포 형태를 요청. AppImage 는 "받아서 바로 실행" 용, .deb 는 "시스템 앱으로 설치" 용으로 공존.

**영향 범위**:
- 신규: `appbuild/linux/build-deb.sh`
- 문서: `CLAUDE.md`(빌드 명령·이름 동기화 목록), `.agent/BUILD.md`(산출물 표·구조·체크리스트)
- 런타임/기존 빌드 영향 없음 — 완전 독립 스크립트

**주의**:
- **패키지 이름은 소문자(`roboseasy`)**, 바이너리/WMClass 는 PascalCase(`Roboseasy`). Debian 정책.
- 설치 위치는 `/opt/Roboseasy/Roboseasy` + `/usr/bin/Roboseasy` 심링크. Slack/VSCode 관례 따름.
- `Depends: libc6, libxcb-cursor0` — Qt 번들은 PyInstaller 가 포함하지만 시스템 xcb-cursor 는 필수. 너무 많이 명시하면 대상 환경에서 설치 거부됨.
- **이름 변경 시 체크리스트가 5곳으로 늘어남** (이전 4곳 + `build-deb.sh`의 `APP_NAME`/`PKG_NAME`).
- 버전은 `VERSION=1.2.0 ./build-deb.sh` 로 override. 기본값은 `1.0.0`. 추후 `git describe --tags` 로 자동화 검토 가능.

---

<!-- 새 엔트리는 이 위에 추가 (시간 역순) -->
