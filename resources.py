"""
리소스 경로 해석 헬퍼.
- 개발 모드: 프로젝트 루트의 `resource/` 폴더를 참조
- PyInstaller 번들(`--onefile` 포함): `sys._MEIPASS` 임시 추출 디렉토리 참조
  (spec의 datas에서 `'.'` (루트)로 번들하는 구조를 전제로 함)
"""
import os
import sys


def resource_path(relative: str) -> str:
    """리소스 파일(예: "logo.png")의 절대 경로를 반환.

    - PyInstaller 번들 실행 중이면 `sys._MEIPASS/<relative>`
    - 일반 개발 실행이면 `<project_root>/resource/<relative>`
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resource", relative)
