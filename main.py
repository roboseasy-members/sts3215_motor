import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from resources import resource_path
from ui.id_setup_wizard import IdSetupWizard
from ui.main_window import MainWindow
from ui.mode_select_dialog import (
    MODE_ID_SETUP,
    MODE_SINGLE,
    MODE_SOARM101,
    ModeSelectDialog,
)
from ui.soarm101_window import SoArm101Window


def _set_windows_app_id():
    """Windows 작업표시줄에서 이 앱을 python.exe와 분리해 고유 아이콘으로 표시하도록 설정.
    AppUserModelID를 지정하지 않으면 Windows가 Python 호스트로 그룹화해 기본 아이콘이 표시됨."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        app_id = "RoboSEasy.STS3215MotorTest.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        # 실패해도 기능에는 영향 없음
        pass


def main():
    _set_windows_app_id()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 작업표시줄/타이틀바 아이콘 설정 — 가능한 경우 .ico 우선 (Windows 표시 품질 우수), 아니면 .png
    icon_ico = resource_path("icon.ico")
    icon_png = resource_path("icon.png")
    icon_path = icon_ico if os.path.isfile(icon_ico) else icon_png
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    while True:
        dialog = ModeSelectDialog()
        if dialog.exec() != ModeSelectDialog.DialogCode.Accepted:
            sys.exit(0)

        mode = dialog.selected_mode

        if mode == MODE_ID_SETUP:
            window = IdSetupWizard()
        elif mode == MODE_SINGLE:
            window = MainWindow(mode=MODE_SINGLE)
        elif mode == MODE_SOARM101:
            window = SoArm101Window()
        else:
            sys.exit(0)

        window.show()

        back_requested = False

        def on_back():
            nonlocal back_requested
            back_requested = True
            window.close()

        window.back_to_menu.connect(on_back)
        app.exec()

        if not back_requested:
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
