# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 자동으로 읽는 컨텍스트 문서입니다.
더 깊은 내용은 `.agent/` 폴더의 문서를 참조하세요.

---

## 프로젝트 한 줄 요약

Feetech **STS3215** 서보 모터의 **ID 셋업**과 LeRobot **SO-ARM 101** 로봇팔을
쉽게 세팅·테스트하기 위한 PyQt6 GUI 도구. 최종 산출물은 **Windows EXE**와
**Linux AppImage**로 배포된다.

## 목적과 목표

- **목적**: 엔드 유저(일반적으로 로봇 개발자·연구자·학생)가 복잡한 CLI 없이
  STS3215 모터의 ID를 할당하고 SO-ARM 101을 검증할 수 있도록 돕는 것.
- **목표**:
  1. USB-시리얼 연결만으로 모터를 스캔·핑·ID 변경 가능
  2. SO-ARM 101(6 모터) 전체 모니터링·제어 + 충돌 감지로 하드웨어 보호
  3. ID 셋업 마법사로 한 대씩 연결하며 ID 6→5→4→3→2→1 순차 할당 자동화
  4. Windows `.exe` / Linux `.AppImage` 단일 파일 배포

## 대상 사용자

- Python/개발 환경을 몰라도 되는 **로봇 운영자**
- 따라서 에러 메시지는 한국어, 버튼/안내 문구도 한국어 우선

---

## 프로젝트 구조 (요점만)

```
sts3215_motor/
├── main.py                 # 엔트리포인트. 모드 선택 다이얼로그 루프
├── motor_controller.py     # ST3215 SDK 래퍼 (threading.Lock 기반 스레드 안전)
├── resources.py            # dev / PyInstaller 번들 양쪽 리소스 경로 해석
├── ui/
│   ├── mode_select_dialog.py  # 시작 화면: ID 셋업 / 단일 / SO-ARM 101
│   ├── id_setup_wizard.py     # ID 순차 할당 마법사
│   ├── main_window.py         # 단일 모터 테스트
│   └── soarm101_window.py     # SO-ARM 101 전체 제어·모니터링
├── resource/               # logo.png, icon.png, icon.ico
├── appbuild/
│   ├── linux/   (build.sh, motor_check_gui.spec)
│   └── windows/ (build.bat, motor_check_gui.spec)
└── .agent/                 # Claude용 상세 문서
```

자세한 아키텍처는 [.agent/ARCHITECTURE.md](.agent/ARCHITECTURE.md) 참고.

---

## 개발/실행

```bash
# 개발 실행
pip install -r requirements.txt
python main.py

# Linux 빌드
cd appbuild/linux && ./build.sh             # 실행파일
cd appbuild/linux && ./build.sh --appimage  # AppImage
cd appbuild/linux && ./build-deb.sh         # .deb (시스템 전역 설치용)

# Windows 빌드
cd appbuild\windows && build.bat
```

빌드 디테일은 [.agent/BUILD.md](.agent/BUILD.md) 참고.

---

## Claude가 지켜야 할 규칙

### 언어
- UI 문자열·사용자 메시지·주석은 **한국어** 우선. 변수/함수명은 영어 snake_case.
- 커밋 메시지는 `FIX:`, `ADD:`, `DELETE:`, `UPDATE:`, `REFACTOR:` 등 영문 prefix + 한국어 설명. (기존 git log 스타일을 따를 것.)

### 의존성
- 런타임 의존성은 `PyQt6`, `st3215`, `pyserial` 3개뿐. 함부로 `numpy`, `pandas` 등을 추가하지 말 것 — PyInstaller `excludes`에 명시되어 있음.
- 새 의존성은 `requirements.txt`와 `appbuild/*/build.*` 스크립트, `motor_check_gui.spec` 3곳 모두 반영해야 함.

### 하드웨어 / 시리얼
- 시리얼 포트 접근은 모두 `MotorController`(스레드 안전 래퍼)를 통해서만. `st3215.ST3215`를 UI 코드에서 직접 쓰지 말 것.
- **Windows의 `PermissionError(13)`**: 재연결 시 자주 발생 → `disconnect()`가 portHandler를 강제 close + `gc.collect()` 하는 로직을 유지할 것. 재시도 로직도 제거 금지.
- **브로드캐스트 ID 변경(0xFE)** 은 버스에 모터가 **1대뿐일 때만** 사용. 안전 가드를 반드시 유지.
- 스캔 기본 범위는 **ID 1~7** (SO-ARM 101 기준으로 최적화). 함부로 범위를 넓혀 스캔을 느리게 하지 말 것.

### 리소스/빌드
- 이미지를 읽을 때는 반드시 `resources.resource_path("...")` 사용. 하드코딩된 `os.path.join("resource", ...)` 금지 — PyInstaller 번들에서 깨짐.
- 새 리소스 파일을 추가하면 `appbuild/linux/motor_check_gui.spec`과 `appbuild/windows/motor_check_gui.spec` 둘 다의 `datas`에 추가해야 함.

### UI
- 테마 색상은 `mode_select_dialog.py` 및 `id_setup_wizard.py` 상단의 색상 상수 를 따른다 (`#3B1D6B` 헤더, `#7C5CBF` 액센트, `#E8833A` 셋업 버튼 등).
- "뒤로가기"를 지원하는 창은 `back_to_menu` 시그널을 발행해야 함 — `main.py`의 루프가 이걸 보고 모드 선택으로 복귀.

### 이름·배포
- 빌드 산출물 이름은 양 플랫폼 모두 `Roboseasy` 로 통일:
  - Linux 실행파일: `appbuild/linux/dist/Roboseasy`
  - Linux AppImage: `appbuild/linux/dist/Roboseasy.AppImage`
  - Linux .deb: `appbuild/linux/dist/roboseasy_<ver>_<arch>.deb` (패키지명만 소문자 — Debian 관례)
  - Windows EXE: `appbuild\windows\dist\Roboseasy.exe`
- 이름 변경 시 다섯 곳을 모두 맞춰야 함: `appbuild/linux/build.sh` (`APP_NAME`), `appbuild/linux/build-deb.sh` (`APP_NAME`, `PKG_NAME`), `appbuild/windows/build.bat` (`APP_NAME`), `appbuild/linux/motor_check_gui.spec` (`name=`), `appbuild/windows/motor_check_gui.spec` (`name=`).
- `main.py` 의 `app.setDesktopFileName("Roboseasy")` / `app.setApplicationName("Roboseasy")` 와 `.desktop` 파일의 `StartupWMClass=Roboseasy` 값도 동일해야 GNOME 타스크바에 올바른 아이콘이 뜸.

---

## 자주 하는 실수 / 금지

- ❌ UI 스레드에서 블로킹 시리얼 호출 직접 수행 (QThread/QTimer로 오프로드)
- ❌ `ReadPosition` 실패 시 0 반환 → `motor_controller.read_position`은 예외를 던짐. 0을 "정상 위치"로 해석하지 말 것.
- ❌ `.spec` 파일의 `excludes` 항목 삭제 (번들 사이즈 급증)
- ❌ 한국어 메시지를 영어로 바꾸기 (엔드 유저 대상이 한국어권 중심)

---

## 추가 문서

- [.agent/ARCHITECTURE.md](.agent/ARCHITECTURE.md) — 모듈 관계, 데이터 흐름, 스레딩 모델
- [.agent/CONVENTIONS.md](.agent/CONVENTIONS.md) — 코딩 스타일, 네이밍, PyQt6 패턴
- [.agent/BUILD.md](.agent/BUILD.md) — PyInstaller spec, AppImage, 서명, 아이콘
- [.agent/LOG.md](.agent/LOG.md) — 작업 로그 (큰 변경 시 추가)
