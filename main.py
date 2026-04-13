#!/usr/bin/env python3
"""
Feetech Motor Control GUI
메인 진입점
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 어플리케이션 설정
    app.setApplicationName("Feetech Motor Control")
    app.setOrganizationName("RoboSeasy")
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 이벤트 루프 실행
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
