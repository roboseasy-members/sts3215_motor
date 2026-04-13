#!/usr/bin/env python3
"""
PyInstaller 빌드 스크립트
.exe 파일 생성을 위한 설정
"""

import PyInstaller.__main__
import sys
import os

def build_exe():
    """PyInstaller로 .exe 파일 생성"""

    # 현재 디렉토리
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # OS별 add-data 구분자 (Windows: ';', Linux/Mac: ':')
    sep = ';' if sys.platform == 'win32' else ':'

    # PyInstaller 인자
    args = [
        'main.py',                           # 메인 진입점
        '--onefile',                         # 단일 .exe 파일로 생성
        '--windowed',                        # 콘솔 창 없음
        '--name=FeetechMotorControl',        # .exe 파일명
        '--icon=NONE',                       # 아이콘 (없으면 기본값)
        f'--add-data=gui{sep}gui',           # GUI 패키지 포함
        f'--add-data=motor{sep}motor',       # motor 패키지 포함
        f'--add-data=utils{sep}utils',       # utils 패키지 포함
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=serial',
        '--hidden-import=serial.tools',
        '--hidden-import=serial.tools.miniterm',
        '--hidden-import=serial.tools.list_ports',
        '--hidden-import=lerobot',
        '--hidden-import=lerobot.motors.feetech',
        '--hidden-import=lerobot.motors.motors_bus',
        '-y',                                # 기존 빌드 덮어쓰기
    ]
    
    # PyInstaller 실행
    print("PyInstaller로 .exe 파일을 생성하는 중...")
    print(f"명령어: pyinstaller {' '.join(args)}")
    
    PyInstaller.__main__.run(args)
    
    print("\n✅ 빌드 완료!")
    print(f"생성된 .exe 파일: {current_dir}/dist/FeetechMotorControl.exe")
    print("\n사용 방법:")
    print("1. 다른 PC에 .exe 파일을 복사")
    print("2. .exe 파일을 더블클릭하여 실행")
    print("3. 모터 제어 GUI가 실행됩니다")

if __name__ == "__main__":
    build_exe()
