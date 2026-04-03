import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.mode_select_dialog import MODE_SINGLE, MODE_SOARM101, ModeSelectDialog


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dialog = ModeSelectDialog()
    if dialog.exec() != ModeSelectDialog.DialogCode.Accepted:
        sys.exit(0)

    mode = dialog.selected_mode

    if mode == MODE_SINGLE:
        window = MainWindow(mode=MODE_SINGLE)
        window.show()
    elif mode == MODE_SOARM101:
        window = MainWindow(mode=MODE_SOARM101)
        window.show()
    else:
        sys.exit(0)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
