# Feetech Motor Control GUI

Feetech 서보 모터를 쉽게 제어할 수 있는 GUI 프로그램입니다.

## 📋 기능

- ✅ COM 포트 자동 검색 및 연결
- ✅ 최대 6개 모터 동시 제어
- ✅ 실시간 모터 위치 모니터링
- ✅ 직관적인 카드 기반 UI
- ✅ 목표 위치 입력 및 빠른 조정 (±10)
- ✅ 긴급 정지 기능
- ✅ 연결 상태 실시간 표시

## 🚀 설치 방법

### 1. Python 환경 설정 (개발자용)

```bash
# Python 3.8 이상 필요
python --version

# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 필수 패키지 설치
pip install PyQt5 pyserial

# lerobot 라이브러리 설치
git clone https://github.com/huggingface/lerobot.git
cd lerobot
pip install -e .
cd ..

# GUI 프로그램 다운로드
git clone https://github.com/roboseasy/CheckFeetechMotors.git
cd CheckFeetechMotors
```

### 2. 실행

```bash
python main.py
```

## 📦 .exe 파일로 패키징 (Phase 7에서 진행)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="FeetechMotorControl" main.py
```

## 🎮 사용 방법

### 1단계: 연결
1. 상단에서 COM 포트 선택
2. "연결" 버튼 클릭
3. 연결 상태 확인 (초록색 인디케이터)

### 2단계: 모터 추가
1. "+" 카드 클릭
2. 모터 ID 선택 (1~6)
3. 모터 카드 생성 확인

### 3단계: 모터 제어
1. 현재 위치를 실시간으로 확인
2. 목표 위치 입력
   - 직접 입력 또는
   - ▲▼ 버튼으로 10씩 조정
3. "이동 ➜" 버튼 클릭

### 긴급 정지
- 빨간색 "⛔ 긴급 정지" 버튼 클릭
- 모든 모터의 토크가 꺼집니다

## 🔧 지원 모터

- Feetech STS3215
- Feetech SCS 시리즈
- 기타 Feetech 호환 서보

## ⚠️ 주의사항

1. **전원 연결**: 모터 사용 전 외부 전원을 반드시 연결하세요
2. **포트 확인**: COM 포트가 올바른지 확인하세요
3. **ID 중복**: 각 모터는 고유한 ID를 가져야 합니다
4. **범위 제한**: 위치값은 0~4095 범위입니다

## 🐛 문제 해결

### 포트가 목록에 없어요
- USB 케이블 연결 확인
- 드라이버 설치 확인
- "🔄" 버튼으로 새로고침

### 연결이 안 돼요
- 올바른 COM 포트 선택 확인
- 다른 프로그램에서 포트 사용 중인지 확인
- 모터 전원 공급 확인

### 모터가 움직이지 않아요
- 토크가 켜져있는지 확인
- 목표 위치가 유효 범위인지 확인
- 긴급 정지 상태인지 확인

## 📞 지원

문제가 발생하면 이슈를 등록해주세요.

## 📝 라이선스

MIT License

## 👨‍💻 개발자

- RoboSeasy Team
