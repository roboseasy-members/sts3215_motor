# ARCHITECTURE.md

애플리케이션 내부 구조 — Claude가 기능을 변경하기 전에 먼저 읽을 문서.

---

## 1. 레이어 개요

```
┌──────────────────────────────────────────────────────┐
│ UI Layer — PyQt6                                     │
│   ui/mode_select_dialog.py   (엔트리 다이얼로그)       │
│   ui/id_setup_wizard.py      (ID 셋업 마법사)          │
│   ui/main_window.py          (단일 모터 테스트)        │
│   ui/soarm101_window.py      (SO-ARM 101 전체)        │
└───────────────┬──────────────────────────────────────┘
                │ (호출)
┌───────────────▼──────────────────────────────────────┐
│ Controller Layer                                     │
│   motor_controller.py — MotorController              │
│     - threading.Lock()으로 시리얼 접근 직렬화           │
│     - connect/disconnect/ping/scan/move/read/change_id│
└───────────────┬──────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────┐
│ SDK Layer                                            │
│   st3215 (외부 패키지) → Feetech scservo_sdk          │
│   pyserial (USB-시리얼 포트)                          │
└──────────────────────────────────────────────────────┘
```

리소스 경로는 `resources.py`의 `resource_path()`가 레이어 독립적으로 해석 (dev vs PyInstaller 번들).

---

## 2. 실행 흐름

### 2.1 엔트리포인트 (main.py)

1. `_set_windows_app_id()` — Windows 작업표시줄에서 python.exe와 분리되도록 AppUserModelID 설정
2. `QApplication` 생성, Fusion 스타일 적용
3. 앱 아이콘 설정 (`.ico` 우선, 없으면 `.png`)
4. **무한 루프**:
   - `ModeSelectDialog.exec()` 로 모드 선택
   - 선택된 모드에 해당하는 윈도우 인스턴스화 후 `show()`
   - 윈도우의 `back_to_menu` 시그널을 기다림
   - 뒤로가기가 발생하면 루프 재진입, 아니면 종료

이 루프 구조 덕분에 각 윈도우에서 "뒤로" 버튼을 누르면 모드 선택 화면으로 자연스럽게 돌아감.

### 2.2 모드별 플로우

| 모드 | 창 | 주요 기능 |
|------|-----|---------|
| `MODE_ID_SETUP` | `IdSetupWizard` | 모터 1대씩 연결 → 브로드캐스트로 순차 ID 할당(6→1) → 중앙값(2048) 이동 |
| `MODE_SINGLE` | `MainWindow` | 포트 연결, 스캔, 개별 제어·모니터링·ID 변경 |
| `MODE_SOARM101` | `SoArm101Window` | 6 모터 동시 모니터링, 충돌 감지, 개별 슬라이더 제어 |

---

## 3. 모터 제어 레이어 (motor_controller.py)

### 3.1 설계 원칙

- 모든 공개 메서드는 `self._lock` 안에서 `self._servo`(ST3215 인스턴스)에 접근 → **UI 스레드와 모니터링 스레드가 동시에 호출해도 안전**.
- 실패 시 **예외를 던짐** (None/0 반환 ❌). 호출자는 `try/except`로 처리.

### 3.2 주요 메서드

| 메서드 | 용도 | 주의 |
|------|------|------|
| `connect(port, retries=2)` | 시리얼 연결. `PermissionError` 등 일시적 실패 시 재시도 | Windows에서 재연결 직후 자주 실패 — 재시도 로직 필수 |
| `disconnect()` | portHandler·ser 를 명시적으로 close + `gc.collect()` | Windows의 핸들 누수 방지 목적. 간소화 ❌ |
| `scan_motors(id_range)` | 기본 `range(1, 30)` 이지만 UI는 1~7 사용 | 브로드캐스트 아님 — 개별 Ping 루프 |
| `ping(motor_id)` | 단일 핑 | |
| `move_to(id, pos, speed=700, acc=50)` | SetSpeed → SetAcceleration → MoveTo 3콜 | |
| `read_position(id)` | 시리얼 1회 (빠름) | 실패 시 `RuntimeError` |
| `read_status(id)` | 7회 시리얼 (느림, 모니터링용) | MotorStatus dataclass 반환 |
| `change_id(current, new)` | 특정 ID → 새 ID (일반 변경) | |
| `change_id_broadcast(new)` | 브로드캐스트 0xFE 로 ID 변경 | ⚠️ 버스에 **1대만** 연결 시 사용 |

### 3.3 브로드캐스트 ID 변경 시퀀스

```python
STS_LOCK = 55   # EPROM 잠금 레지스터
STS_ID   = 5    # ID 레지스터
BROADCAST_ID = 0xFE

write1ByteTxOnly(BROADCAST, STS_LOCK, 0)   # 잠금 해제
write1ByteTxOnly(BROADCAST, STS_ID, new_id)
write1ByteTxOnly(BROADCAST, STS_LOCK, 1)   # 재잠금
```

이 순서를 바꾸면 EPROM이 잠긴 상태에서 쓰기 시도 → 실패. 순서 유지 필수.

---

## 4. UI 스레딩 모델

### 4.1 원칙

- **시리얼 I/O는 UI 스레드에서 직접 실행하지 않는다.**
- 짧은 단발 호출(ping 1회, change_id)은 UI 스레드에서도 허용 — 수백 ms 블로킹.
- 반복/장시간 작업은 `QThread` 또는 `QTimer` + 주기적 폴링 패턴 사용.

### 4.2 실제 패턴

- `MainWindow` / `SoArm101Window`: `QTimer`로 100ms 주기 폴링하여 `read_position`/`read_status` 호출
- `IdSetupWizard`: 스캔/ID 변경은 `QThread` 서브클래스에 위임, 완료 시그널을 UI가 받음
- `scan_motors`는 최대 수 초 걸릴 수 있으므로 진행률 다이얼로그와 함께 스레드에서 실행

### 4.3 충돌 감지 (SoArm101Window)

- 매 폴링마다 `load` / `current` 를 임계값(기본 load 1300, current 800mA)과 비교
- 초과 시: `set_torque(id, False)` + UI 상태를 "충돌 감지" 로 표시
- 슬라이더를 움직이면 상태 해제 + 토크 재활성화

---

## 5. 리소스 번들링

`resources.resource_path(name)` 한 곳에서만 경로 결정:

- **개발**: `<repo>/resource/<name>`
- **PyInstaller 번들**: `sys._MEIPASS/<name>` (spec의 `datas`에서 `'.'`로 복사됨)

새 이미지/파일을 추가하면 양쪽 `.spec` 의 `datas` 에도 추가해야 한다.

---

## 6. 시그널 연결 규약

- 뒤로가기가 필요한 창은 반드시 `back_to_menu = pyqtSignal()` 을 노출한다.
- `main.py` 의 루프가 이 시그널을 잡아 다이얼로그를 재표시 → 이 컨벤션을 깨면 "뒤로" 가 동작하지 않는다.

---

## 7. 확장 지점

새 모드 추가 시:
1. `ui/<new_mode>.py` 작성, `back_to_menu` 시그널 제공
2. `ui/mode_select_dialog.py` 에 `MODE_<NAME>` 상수 + 버튼 + 슬롯 추가
3. `main.py` 의 `if mode == ...` 분기에 새 창 추가

새 모터 연산 추가 시:
1. `MotorController` 에 `_lock` 안에서 `self._servo` 접근하는 메서드 추가
2. 실패는 예외로 전달 (None/0 반환 금지)
3. UI는 스레드/타이머 뒤로 숨겨서 호출
