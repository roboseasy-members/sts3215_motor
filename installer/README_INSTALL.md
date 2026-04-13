# Feetech Motor Control - 설치 가이드

## 📋 설치 요구사항

### Windows PC에 필수 설치
1. **Python 3.10** - [python.org에서 다운로드](https://www.python.org/downloads/)
2. **git** - [git-scm.com에서 다운로드](https://git-scm.com/download/win)

### 설치 시 주의사항
- Python 설치 시 **반드시 "Add Python to PATH" 체크**
- git 설치 시 **반드시 "Add Git to PATH" 체크**

---

## 🚀 설치 방법 (자동)

### 방법 1: NSIS 설치 프로그램 사용 (권장)

```
1. FeetechMotorControl_Installer_v1.0.exe 다운로드
2. 더블클릭으로 실행
3. "다음" 버튼만 계속 클릭
4. 자동으로 설치 진행 (약 2-3분)
5. 설치 완료 후 자동으로 GUI 시작
```

**설치 흐름:**
- Python 3.10 확인 (자동 설치 아님)
- uv 설치 (자동)
- git 확인 (이미 설치되어 있어야 함)
- LeRobot 자동 클론
- Feetech 라이브러리 자동 설치
- GUI 실행

---

## 🛠️ 설치 방법 (수동)

### 방법 2: 수동 설치 (고급)

만약 자동 설치가 실패하는 경우, 다음을 직접 실행하세요:

```batch
REM 1. Python 3.10 설치 확인
python --version

REM 2. uv 설치
python -m pip install uv

REM 3. git 설치 확인
git --version

REM 4. 설치 디렉토리로 이동
cd C:\Users\YOUR_USERNAME\AppData\Local\FeetechMotorControl

REM 5. LeRobot 클론
git clone https://github.com/huggingface/lerobot.git
cd lerobot

REM 6. 가상환경 생성
uv venv --python 3.10

REM 7. 가상환경 활성화
.venv\Scripts\activate.bat

REM 8. Feetech 라이브러리 설치
uv pip install -e ".[feetech]"

REM 9. GUI 실행
cd ..\feetech_motor_gui
python main.py
```

---

## ✅ 설치 확인

설치가 정상적으로 완료되었는지 확인하려면:

```batch
python -c "import lerobot; print('LeRobot 설치 완료')"
```

---

## ⚙️ 설치 경로

기본 설치 경로:
```
C:\Users\YOUR_USERNAME\AppData\Local\FeetechMotorControl
```

폴더 구조:
```
FeetechMotorControl/
├── lerobot/                    # LeRobot 라이브러리
│   └── .venv/                 # Python 가상환경
├── feetech_motor_gui/          # 모터 제어 GUI
├── FeetechMotorControl.exe    # GUI 실행 파일
└── installer/                  # 설치 스크립트
```

---

## 🚨 문제 해결

### 1. Python을 찾을 수 없음
**원인:** Python 설치 후 PATH 업데이트 필요
**해결:**
- Python 재설치
- 설치 시 "Add Python to PATH" 반드시 체크
- PC 재부팅

### 2. git을 찾을 수 없음
**원인:** git 설치 후 PATH 업데이트 필요
**해결:**
- git 재설치: https://git-scm.com/download/win
- 설치 시 "Add Git to PATH" 반드시 체크
- PC 재부팅

### 3. LeRobot 설치 실패
**원인:** 인터넷 연결 끊김 또는 권한 부족
**해결:**
- 인터넷 연결 확인
- 관리자 권한으로 설치 프로그램 실행
- 방화벽/안티바이러스 확인

### 4. uv 설치 실패
**원인:** pip 오류
**해결:**
```batch
python -m pip install --upgrade pip
python -m pip install uv
```

### 5. GUI 실행되지 않음
**원인:** GUI 파일 손상 또는 의존성 누락
**해결:**
```batch
cd C:\Users\YOUR_USERNAME\AppData\Local\FeetechMotorControl\feetech_motor_gui
python main.py
```

---

## 💻 GUI 사용하기

### 포트 연결
1. 모터가 연결된 COM 포트 선택 (예: COM7)
2. "연결" 버튼 클릭
3. 연결 성공 메시지 확인

### 모터 추가
1. "+" 버튼 클릭
2. 모터 ID 선택 (1~6)
3. 모터 카드 추가

### 모터 제어
1. 목표값 입력 또는 ▲▼ 버튼으로 조정
2. "이동" 버튼 클릭
3. 현재 위치 실시간 업데이트 확인

### 긴급 정지
- "⛔ 긴급 정지" 버튼 클릭
- 모든 모터 토크 즉시 OFF

---

## 📊 시스템 요구사항

| 항목 | 요구사항 |
|------|--------|
| OS | Windows 10, 11 (64비트) |
| Python | 3.10 이상 |
| 메모리 | 최소 2GB |
| 저장공간 | 최소 2GB |
| 인터넷 | 설치 중 필수 (LeRobot 다운로드) |

---

## 📞 지원

문제 발생 시:
1. 위의 "문제 해결" 섹션 확인
2. 터미널 출력 메시지 확인
3. GitHub Issues에 보고

---

## 📝 설치 로그

설치 중 문제가 발생하면, 다음 경로의 로그를 확인하세요:
```
C:\Users\YOUR_USERNAME\AppData\Local\FeetechMotorControl\install.log
```

---

**설치 완료 후:** 아버지와 함께 첫 번째 모터 연결 테스트를 진행하세요! 🎉
