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

## 2026-04-22 — 구글 OAuth 로그인 게이트 도입 + Supabase MCP 연결

**무엇을**:
- `auth/google_oauth.py` 신규 — Google OAuth 2.0 Desktop flow(`InstalledAppFlow.run_local_server` loopback) 래퍼. 토큰을 플랫폼별 사용자 설정 디렉토리의 `Roboseasy/auth.json` 에 저장, 만료 시 refresh, revoke 감지 시 자동 삭제.
- `ui/welcome_dialog.py` 신규 — 웰컴 화면에서 `QThread` 로 로그인 실행(블로킹 호출이라 UI 스레드에서 돌리면 안 됨).
- `main.py` 에 외부 루프 추가 — 자동 로그인 → 실패 시 `WelcomeDialog` → 모드 선택 루프. `MODE_LOGOUT` 시 `sign_out()` 후 외부 루프가 웰컴 화면을 재표시.
- `ui/mode_select_dialog.py` 에 `MODE_LOGOUT` 상수 추가.
- `requirements.txt` 에 `google-auth`, `google-auth-oauthlib`, `requests` 추가.
- 프로젝트 scope `.mcp.json` 에 Supabase MCP 서버 추가(project_ref `mjorszvxiihuvcueyqil`), OAuth 인증 완료. 향후 회원가입/유저 관리/구독 DB 연동 후보.

**왜**: 사용자별 사용 이력/라이선스/구독 상태 추적 기반을 마련하기 위해 로그인 게이트가 필요. 구글 OAuth 는 (1) 민감 스코프를 쓰지 않으면 앱 심사가 불필요하고 (2) Desktop flow 가 사용자에게 친숙한 브라우저 로그인을 제공해 일반 사용자 대상 앱에 적합. 백엔드 데이터는 Supabase 로 갈 가능성이 커서 MCP 를 먼저 붙여둠.

**영향 범위**:
- 런타임: 앱 실행 시 네트워크(구글 OAuth) 필수 — 오프라인 모드 없음. 첫 실행 때만 브라우저 오픈, 이후엔 refresh token 으로 조용히 자동 로그인.
- 빌드: `resource/oauth_client.json` 이 번들에 포함되어야 로그인 가능 → 양쪽 `.spec` 의 `datas` 에 추가 필요. 이 파일은 **커밋 금지**(.gitignore 확인).
- 배포: OAuth 클라이언트의 redirect_uri 는 loopback 이라 공개된 "설치형 앱" 시크릿이므로 앱 바이너리에 동봉해도 되지만, 유출 시 로그인 도용 시도에 악용될 수 있어 퍼블릭 리포엔 넣지 말 것.

**주의**:
- `run_local_server` 는 중간 취소가 어려워 `timeout_seconds=300` 경과 전엔 스레드가 살아있음 — `WelcomeDialog._stop_worker` 는 `quit()` 만 호출하고 조인하지 않음(UI 블로킹 방지). 창 닫아도 백그라운드에서 타임아웃까지 대기.
- 스코프 추가 시 구글 앱 심사가 필요해질 수 있음. 현재 스코프 유지 권장.
- Supabase 연동은 아직 코드 없음 — MCP 만 붙은 상태. 회원가입 구현 시 Google OAuth 의 `sub`(user ID) 를 Supabase `users` 테이블 키로 매핑하는 설계가 자연스러움.

---

## 2026-04-22 — Supabase `public.users` 테이블 + 로그인 시 upsert (A안)

**무엇을**:
- Supabase 프로젝트(`mjorszvxiihuvcueyqil`) 에 `public.users(sub PK, email, name, created_at, updated_at)` 테이블 생성. `updated_at` 자동 갱신 트리거(`public.set_updated_at`, search_path='' + `pg_catalog.now()` 로 lint 경고 회피).
- RLS 활성화, 정책 1개: `FOR ALL TO anon USING(true) WITH CHECK(true)` ("anon can upsert users"). anon 에게 `grant select, insert, update on public.users`.
- `auth/supabase_client.py` 신규 — `requests` 기반 경량 PostgREST upsert. supabase-py 는 일부러 의존성 추가하지 않음(번들 절약).
- `resource/supabase_config.json` (url + anon_key) 추가, `.gitignore` 및 양쪽 `.spec` `datas` 반영.
- `main.py` 로그인 직후 `upsert_user(sub, email, name)` 호출. 실패해도 앱은 계속 실행.

**왜**: 사용자(이름·이메일) 기본 정보를 중앙 저장. "회원가입"은 별도 플로우 없이 구글 최초 로그인 = 자동 가입으로 단순화. supabase-py 대신 PostgREST 직접 호출한 이유는 번들 사이즈 + 의존성 최소화 + 이 앱이 gotrue/storage/realtime 등 필요 없기 때문.

**영향 범위**:
- 런타임: 로그인 성공 후 최대 10초 HTTP POST 1회 추가(비동기 아니고 UI 스레드 — 실패 시 10초 블로킹 가능). 향후 필요 시 `QThread` 로 이관 검토.
- 빌드: `resource/supabase_config.json` 미배치 시 `upsert_user` 는 조용히 False 반환. 빌드 자체는 성공.
- DB: `public.users` 테이블·트리거·정책 전부 신규. 기존 데이터 영향 없음.

**주의**:
- ⚠️ **A안 (anon key + 완전 개방 RLS) 은 임시** — 규모 커지기 전에 B안(Edge Function + Google ID token 검증) 으로 이관 필수. CLAUDE.md 상단 "반드시 해야 할 일" 섹션에 기록됨.
- PostgREST 의 upsert(`resolution=merge-duplicates`) 는 INSERT/UPDATE 분리 정책 + `USING/WITH CHECK (true)` 조합에서도 42501 로 거부됨(재현 확인). 단일 `FOR ALL` 정책이어야 동작. B안 이관 시엔 이 제약 자체가 사라짐.
- PostgREST upsert 는 `SELECT` 권한도 필요(충돌 검사용). RLS 로 조회는 여전히 막혀 있으나 `grant select to anon` 은 필수.
- 트리거 함수 search_path='' 이면 `now()` 가 해석 안 되므로 `pg_catalog.now()` 로 스키마 한정 필요.
- 새 publishable key(`sb_publishable_...`) 는 `anon` 역할로 매핑되지 않는 것으로 확인됨. 레거시 JWT anon key 를 사용해야 `TO anon` 정책이 매칭됨.

---

<!-- 새 엔트리는 이 위에 추가 (시간 역순) -->
