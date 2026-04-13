import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.mode_select_dialog import MODE_SINGLE, MODE_SOARM101, ModeSelectDialog
from ui.soarm101_window import SoArm101Window


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    while True:
        dialog = ModeSelectDialog()
        if dialog.exec() != ModeSelectDialog.DialogCode.Accepted:
            sys.exit(0)

        mode = dialog.selected_mode

        if mode == MODE_SINGLE:
            window = MainWindow(mode=MODE_SINGLE)
        elif mode == MODE_SOARM101:
            window = SoArm101Window()
        else:
            sys.exit(0)

        window.show()

        # 뒤로가기 시그널이 발생하면 윈도우를 닫고 루프를 계속
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
