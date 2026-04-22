# BUILD.md

배포 빌드 관련 지식 — PyInstaller, AppImage, 아이콘, 흔한 함정.

---

## 1. 산출물

| 플랫폼 | 산출물 경로 | 이름 |
|--------|-------------|------|
| Linux  | `appbuild/linux/dist/Roboseasy` | `Roboseasy` |
| Linux (AppImage) | `appbuild/linux/dist/Roboseasy.AppImage` | `Roboseasy` |
| Linux (.deb) | `appbuild/linux/dist/roboseasy_<version>_<arch>.deb` | `roboseasy` (패키지명) |
| Windows | `appbuild\windows\dist\Roboseasy.exe` | `Roboseasy` |

> **이름을 바꿀 때**: `appbuild/linux/build.sh` 의 `APP_NAME`, `appbuild/linux/build-deb.sh` 의 `APP_NAME`/`PKG_NAME`, `appbuild/windows/build.bat` 의 `APP_NAME`, 양쪽 `motor_check_gui.spec` 의 `name=` 필드를 모두 맞춰야 한다.
>
> AppImage 파일명에는 `-<arch>` suffix 를 붙이지 않는 정책. 다중 아키텍처 동시 배포 시 충돌할 수 있으니 그 시점엔 다시 검토할 것. .deb 는 파일명에 `_<arch>` 가 포함됨 (Debian 관례).

---

## 2. 빌드 명령

### Linux

```bash
cd appbuild/linux
./build.sh              # 실행파일만
./build.sh --appimage   # 실행파일 + AppImage
./build-deb.sh          # 실행파일 + .deb (없으면 build.sh 자동 호출)
VERSION=1.2.0 ./build-deb.sh   # 버전 지정
```

첫 실행 시:
- `appbuild/linux/.venv/` 생성 (uv가 있으면 사용, 없으면 venv)
- 의존성 설치: `pyinstaller pyqt6 pyserial st3215`
- `--appimage` 옵션 시 `appimagetool` 자동 다운로드 (GitHub continuous 릴리스)

### Windows

```cmd
cd appbuild\windows
build.bat
```

첫 실행 시 `.venv\` 생성 후 동일 의존성 설치.

---

## 3. PyInstaller spec 구조

양 플랫폼 모두 `motor_check_gui.spec` 을 사용. 핵심 포인트:

### datas (번들에 포함될 리소스)

Linux spec 기준:
```python
datas=[
    (os.path.join(PROJECT_ROOT, 'resource', 'logo.png'), '.'),
    (os.path.join(PROJECT_ROOT, 'resource', 'icon.png'), '.'),
],
```

- 번들 루트(`.`)에 복사되므로 런타임에는 `sys._MEIPASS/logo.png` 로 접근
- → 이 때문에 `resources.resource_path()` 헬퍼가 필요
- **새 리소스 추가 시 양쪽 spec 모두 업데이트** (windows spec에는 `icon.ico` 도 포함돼야 함)

### hiddenimports

PyInstaller가 정적 분석으로 못 찾는 모듈을 명시:
```python
hiddenimports=[
    'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip',
    'serial', 'serial.tools', 'serial.tools.list_ports',
    'st3215',
],
```

새 서드파티 의존성 추가 시 여기에도 넣어야 할 수 있음.

### excludes (번들에서 제외)

```python
excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'IPython',
          'jupyter', 'notebook', 'cv2', 'numpy'],
```

- **삭제하지 말 것** — 삭제 시 번들 크기 수십~수백 MB 증가
- 새 의존성이 내부적으로 이들을 끌어들이지 않는지 빌드 후 확인

### EXE 옵션

- `console=False` (GUI 앱이므로 콘솔 창 숨김)
- `upx=True` (Linux, UPX 압축. 설치돼 있으면 사용)
- Windows spec 에는 `icon='../../resource/icon.ico'` 등의 아이콘 지정 필요

---

## 3.5 .deb 구조 (Linux)

`build-deb.sh` 가 생성하는 패키지 레이아웃:

```
roboseasy_<ver>_<arch>/
├── DEBIAN/
│   ├── control                              # 패키지 메타데이터
│   ├── postinst                             # 설치 후 아이콘/desktop 캐시 갱신
│   └── postrm                               # 제거 후 동일 갱신
├── opt/Roboseasy/Roboseasy                  # PyInstaller 바이너리 본체
└── usr/
    ├── bin/Roboseasy -> /opt/Roboseasy/Roboseasy   # PATH 노출용 심볼릭 링크
    └── share/
        ├── applications/Roboseasy.desktop           # 앱 런처 + StartupWMClass
        ├── icons/hicolor/256x256/apps/Roboseasy.png # 표준 아이콘 경로
        └── pixmaps/Roboseasy.png                    # 레거시 폴백
```

**주요 설계 결정:**

- **바이너리는 `/opt/Roboseasy/`** 에 배치. `/usr/bin/` 은 심링크만. 이유: 번들 앱의 관례(Slack, VSCode, Chrome 모두 유사).
- **Package 이름(`roboseasy`) 은 소문자**, 바이너리/WMClass 이름(`Roboseasy`) 은 PascalCase. Debian 정책상 패키지명은 소문자여야 함.
- **Depends: `libc6, libxcb-cursor0`** — PyInstaller 가 Qt 를 번들하지만 시스템 xcb-cursor 는 필요. 너무 많이 명시하면 설치가 불가능해지므로 최소만.
- **Installed-Size** 는 KB 단위로 계산해 `control` 에 포함 (dpkg 요구).
- **`--root-owner-group`** 플래그로 빌드 사용자와 무관하게 root:root 소유로 패키징.

**설치 흐름:**
```bash
sudo dpkg -i roboseasy_1.0.0_amd64.deb
# 의존성 누락 시 자동 해결:
sudo apt install -f
```

**제거:**
```bash
sudo apt remove roboseasy
```

---

## 4. AppImage 구조 (Linux)

`build.sh --appimage` 가 자동으로 만드는 `AppDir`:

```
Roboseasy.AppDir/
├── AppRun                     # 실행 스크립트
├── Roboseasy.desktop          # Desktop Entry
├── Roboseasy.png              # 아이콘 (루트)
└── usr/
    ├── bin/Roboseasy          # PyInstaller 산출물 복사본
    └── share/icons/hicolor/256x256/apps/Roboseasy.png
```

`AppRun` 은 `usr/bin/Roboseasy` 를 exec 하는 단순 래퍼. `build.sh` 에서 `APP_NAME` 변수가 확장되어 heredoc 에 주입됨.

`.desktop` Categories 는 현재 `Utility;Development;`.

---

## 5. 아이콘

| 파일 | 용도 |
|------|------|
| `resource/icon.ico` | Windows EXE/타이틀바 (고품질) |
| `resource/icon.png` | Linux AppImage 및 런타임 폴백 |
| `resource/logo.png` | 앱 내부 헤더 로고 |

`main.py` 가 `.ico` 를 우선 시도하고 없으면 `.png` 로 폴백 (`os.path.isfile` 체크).

Windows 작업표시줄에서 python.exe 와 분리하여 고유 아이콘으로 표시하려면 `SetCurrentProcessExplicitAppUserModelID` 호출이 필요 — `main.py:_set_windows_app_id()` 가 담당. 이 함수의 `app_id` 문자열(`"RoboSEasy.STS3215MotorTest.1.0"`) 을 바꾸면 Windows 가 새 아이콘으로 인식(캐시 리프레시).

---

## 6. 자주 발생하는 빌드 문제

### Linux

- **`libxcb-*.so` 누락**: PyQt6 가 Qt 플러그인을 찾지 못함. `sudo apt install libxcb-cursor0 libxcb-xinerama0` 등 런타임 라이브러리 설치 필요. AppImage 는 이를 포함하지 않으므로 타겟 배포판에서 테스트 권장.
- **AppImage FUSE 에러**: 최신 Ubuntu 에서 `fuse2` 필요 (`sudo apt install libfuse2`).

### Windows

- **`PermissionError(13)` on port**: 이전 실행의 핸들이 남아있음. `MotorController.disconnect()` 의 gc/close 로직이 이걸 방지 — 절대 단순화하지 말 것.
- **아이콘이 안 바뀜**: Windows 아이콘 캐시 때문. `app_id` 버전 숫자를 올리거나 `ie4uinit.exe -show` 로 캐시 갱신.
- **Antivirus 경고**: PyInstaller 번들은 종종 오탐. 코드 서명 없이는 우회 불가.

### 공통

- **st3215 버전 충돌**: 패키지 업데이트 시 `PingServo` 등 API 시그니처 변경 가능 — `motor_controller.py` 의 호출부 확인.
- **번들 크기 비대화**: `excludes` 에서 무언가 빠졌거나 hiddenimport 가 전이 의존성을 끌고 왔는지 확인 (`pyinstaller --log-level=INFO` 로그 참조).

---

## 7. 릴리스 체크리스트

- [ ] `requirements.txt` 와 spec `hiddenimports` 가 일치하는지 확인
- [ ] Linux 빌드 → 개발 머신과 **다른** 배포판(가능하면 LTS)에서 실행 확인
- [ ] Windows 빌드 → `Roboseasy.exe` 실행, 작업표시줄 아이콘 정상 표시 확인
- [ ] 두 모드 (ID 셋업 / 단일 / SO-ARM 101) 모두 진입 및 뒤로가기 동작
- [ ] USB 모터 연결 → 스캔 → ID 변경 → 재스캔 사이클 실동작
- [ ] 번들 크기 확인 (대략 60~90MB가 정상 범위)
- [ ] `.deb` 설치 → `Roboseasy` 커맨드 실행, 앱 런처 아이콘 확인 → `sudo apt remove roboseasy` 로 깨끗이 제거되는지
