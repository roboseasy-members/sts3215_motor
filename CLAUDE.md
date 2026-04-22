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
├── main.py                 # 엔트리포인트. 로그인 게이트 + 모드 선택 루프
├── motor_controller.py     # ST3215 SDK 래퍼 (threading.Lock 기반 스레드 안전)
├── resources.py            # dev / PyInstaller 번들 양쪽 리소스 경로 해석
├── auth/
│   └── google_oauth.py     # Google OAuth Desktop flow + 토큰 영속화
├── ui/
│   ├── welcome_dialog.py      # 로그인 게이트(웰컴 + 구글 로그인)
│   ├── mode_select_dialog.py  # 모드 선택: ID 셋업 / 단일 / SO-ARM 101 / 로그아웃
│   ├── id_setup_wizard.py     # ID 순차 할당 마법사
│   ├── main_window.py         # 단일 모터 테스트
│   └── soarm101_window.py     # SO-ARM 101 전체 제어·모니터링
├── resource/               # logo.png, icon.png, icon.ico, oauth_client.json
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
- 런타임 의존성: `PyQt6`, `st3215`, `pyserial` (모터 제어) + `google-auth`, `google-auth-oauthlib`, `requests` (로그인).
- 함부로 `numpy`, `pandas` 등을 추가하지 말 것 — PyInstaller `excludes`에 명시되어 있음.
- 새 의존성은 `requirements.txt`와 `appbuild/*/build.*` 스크립트, `motor_check_gui.spec` 3곳 모두 반영해야 함.

### ⚠️ 반드시 해야 할 일 (TODO — 잊지 말 것)

- **Supabase users 테이블 접근을 B안으로 이관**: 현재(A안) 는 앱에 동봉된 anon key 로 PostgREST 에 직접 upsert 하고, RLS 정책이 `anon` 에 대해 `USING/WITH CHECK (true)` 로 완전 개방되어 있음. 이 키가 유출되면 누구나 임의의 `sub`/`email`/`name` 으로 row 를 오염/덮어쓸 수 있음. 규모가 커지거나 정식 릴리즈 전에는 반드시 B안(Supabase Edge Function 에서 Google ID token 검증 → 토큰의 `sub` 과 동일한 row 만 upsert)으로 이관할 것. 관련 파일: `auth/supabase_client.py`, Supabase 프로젝트 `public.users` 테이블의 RLS 정책 "anon can upsert users".

### 인증 / 로그인
- 로그인 게이트는 `main.py` 무한 루프 상단에서 처리. 저장된 refresh token(`load_saved_credentials`)이 있으면 자동 로그인, 없으면 `WelcomeDialog` 노출.
- `google_oauth.sign_in_with_google()` 은 **블로킹** (`run_local_server` 가 루프백 서버를 띄움) — 반드시 `QThread`에서 호출. 직접 호출 금지.
- 토큰 저장 경로는 플랫폼별 사용자 설정 디렉토리의 `Roboseasy/auth.json` (`_app_config_dir`). POSIX에선 `0o600` 으로 권한 제한.
- OAuth 클라이언트 시크릿은 `resource/oauth_client.json` — `resources.resource_path` 로 접근하며 양쪽 `.spec` 의 `datas` 에 포함되어야 함. **리포에 커밋하지 말 것** (`.gitignore` 확인).
- 스코프는 `openid / userinfo.email / userinfo.profile` 만 — 민감 스코프 추가 시 구글 앱 심사가 필요해지므로 신중히.
- 로그아웃은 `MODE_LOGOUT` → `sign_out()` (로컬 토큰만 삭제, 서버측 revoke 안 함) → 외부 루프가 `WelcomeDialog` 로 복귀.
- 로그인 직후 `auth.supabase_client.upsert_user(sub, email, name)` 로 Supabase `public.users` 에 프로필을 upsert. 실패해도 앱은 계속 실행(모터 기능은 오프라인에서도 동작해야 하므로). supabase-py 는 일부러 쓰지 않고 PostgREST REST 호출로 처리 — 번들 사이즈 절약.
- Supabase 설정은 `resource/supabase_config.json` (url + anon_key). `.gitignore` 대상, 양쪽 `.spec` 의 `datas` 에 포함. 파일이 없거나 anon key 가 비어 있으면 `upsert_user` 는 조용히 False 반환.
- **Supabase `public.users` 테이블은 PostgREST 의 upsert(ON CONFLICT DO UPDATE) 제약 때문에 INSERT/UPDATE 를 분리한 정책이 아닌 `FOR ALL` 단일 정책으로 둬야 함**. 분리 정책 + `resolution=merge-duplicates` 조합은 RLS 42501 로 거부됨. (A안 이관 시 이 제약은 사라짐.)

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
