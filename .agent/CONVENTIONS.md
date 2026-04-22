# CONVENTIONS.md

코딩 스타일과 네이밍 규약. 기존 코드의 패턴을 유지하는 것이 1순위.

---

## 언어

- **식별자(변수/함수/클래스/파일명)**: 영어
  - 함수·변수: `snake_case` (`read_position`, `motor_id`)
  - 클래스: `PascalCase` (`MotorController`, `SoArm101Window`)
  - 상수: `UPPER_SNAKE_CASE` (`MODE_ID_SETUP`, `COLOR_HEADER`)
- **문자열 리터럴**:
  - 엔드 유저에게 보이는 UI 문자열·에러 메시지·주석 → **한국어**
  - 로그 prefix, 프로그래머용 예외 메시지는 한/영 혼용 OK (기존 스타일 그대로)
- **주석**: 기본은 한국어. 단 “왜"를 설명하는 주석만 작성하고, 자명한 코드에는 달지 않는다.

---

## 파일 레이아웃

- 진입점: `main.py` 한 개만. UI 창은 전부 `ui/` 하위.
- 시리얼 접근은 무조건 `motor_controller.MotorController` 경유.
- `st3215.ST3215`를 UI 파일에서 직접 임포트 금지 (한 곳만 — `motor_controller.py`).

---

## PyQt6 패턴

### 임포트 정렬

기존 코드 스타일 유지:

```python
import os
import sys                       # stdlib

import serial.tools.list_ports   # 외부

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from motor_controller import MotorController    # 내부 모듈
```

### 스타일시트

- 창별로 파일 상단에 `STYLESHEET = """..."""` 상수로 정의.
- 색상은 파일 상단 `COLOR_*` 상수로 추출하여 문자열에 사용.
- 공통 색상 팔레트 (바꿀 때 전 창 일괄 변경):
  - `#3B1D6B` — 헤더 배경 (짙은 보라)
  - `#7C5CBF` — 액센트 / 버튼 기본
  - `#E8833A` — 셋업/강조 버튼 (주황)
  - `#E04848` — 위험/종료/에러
  - `#5BAD7A` — 성공
  - `#F5F3F8` — 앱 배경
  - `#2D2640` — 텍스트

### 시그널 컨벤션

- 뒤로가기가 필요한 창은 `back_to_menu = pyqtSignal()` 을 반드시 노출.
- 시그널 이름은 `snake_case` + 동사형 (`back_to_menu`, `scan_finished`).

### 스레드 사용

- 반복 폴링: `QTimer` (100ms 기본 주기)
- 1회성 장시간 작업 (스캔, 브로드캐스트 ID 변경 후 검증 등): `QThread` 서브클래스
- UI 업데이트는 반드시 메인 스레드에서 — 워커 스레드는 `pyqtSignal.emit` 만, 슬롯이 UI 업데이트.

### 다이얼로그

- 확인용: `QMessageBox.question / warning / critical`
- 진행률: `QProgressDialog`
- 커스텀 단순 선택: `QDialog` 서브클래스 (`ModeSelectDialog` 참조)

---

## 에러/예외

- `MotorController` 메서드는 **예외로 실패를 알림**. UI에서 try/except로 잡아 `QMessageBox` 나 로그 창에 표시.
- 예외를 먹고 넘어가는 `except Exception: pass` 는 제한적으로만 — 현재 허용된 곳:
  - `disconnect()` 내부의 portHandler 정리 (이미 닫혔을 수 있음)
  - `scan_motors` 루프 안 개별 Ping 실패 (스캔은 계속되어야 함)
  - `_set_windows_app_id()` 의 ctypes 실패 (기능에 영향 없음)
- 그 외 새로운 `pass` 는 추가하지 말 것.

---

## 커밋 메시지

기존 git log 스타일:

```
FIX: 프로그램 파일 이름 수정
DELETE: ID 셋업 마법사 속도 부분은 제거
ADD: 윈도우 작업표시줄 아이콘 설정
```

- prefix (영문 대문자):
  - `FIX:` 버그 수정
  - `ADD:` 새 기능/파일
  - `DELETE:` 제거
  - `UPDATE:` 기존 기능 개선
  - `REFACTOR:` 동작 변화 없는 내부 개선
- 본문: 한국어. 한 줄 요약 우선, 필요 시 빈 줄 후 상세.

---

## 새 파일 생성 체크리스트

새 UI 창을 만들 때:

- [ ] `ui/` 폴더 안에 생성
- [ ] `back_to_menu = pyqtSignal()` 노출 (뒤로가기 필요 시)
- [ ] 파일 상단에 `COLOR_*` 상수 + `STYLESHEET` 정의
- [ ] 시리얼 접근은 `MotorController` 경유
- [ ] 반복 I/O 는 QTimer/QThread 로 오프로드
- [ ] 리소스 파일은 `resource_path()` 로 접근
- [ ] `main.py` 의 모드 분기에 등록
- [ ] `mode_select_dialog.py` 에 버튼 추가

---

## 금지 / 주의

- ❌ UI 코드에서 직접 `ST3215(port)` 생성
- ❌ UI 스레드에서 `scan_motors` 등 수 초 걸리는 호출 직접 실행
- ❌ 리소스 파일 경로를 `"resource/xxx.png"` 로 하드코딩
- ❌ `except Exception: pass` 남발
- ❌ 플랫폼별 분기 없이 `win32` 전용 API 호출 (항상 `sys.platform` 체크)
- ❌ 한국어 UI 문자열을 임의로 영어로 교체
