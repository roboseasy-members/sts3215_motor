import sys

from PyQt6.QtWidgets import QApplication

from ui.id_setup_wizard import IdSetupWizard
from ui.main_window import MainWindow
from ui.mode_select_dialog import (
    MODE_ID_SETUP,
    MODE_SINGLE,
    MODE_SOARM101,
    ModeSelectDialog,
)
from ui.soarm101_window import SoArm101Window


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

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
