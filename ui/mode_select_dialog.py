import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

STYLESHEET = """
QDialog {
    background-color: #F5F3F8;
}
QFrame#headerBar {
    background-color: #3B1D6B;
    border: none;
}
QLabel#headerTitle {
    color: rgba(255,255,255,0.95);
    font-size: 16px;
    font-weight: bold;
}
QLabel#headerSubtitle {
    color: rgba(255,255,255,0.55);
    font-size: 11px;
}
QLabel#sectionLabel {
    color: #2D2640;
    font-size: 14px;
    font-weight: 600;
}
QLabel#promptLabel {
    color: #2D2640;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#setupBtn {
    background-color: #E8833A;
    color: rgba(255,255,255,0.95);
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
    padding: 18px 32px;
    min-width: 300px;
    min-height: 50px;
}
QPushButton#setupBtn:hover {
    background-color: #F09A55;
}
QPushButton#setupBtn:pressed {
    background-color: #C06A28;
}
QPushButton#modeBtn {
    background-color: #7C5CBF;
    color: rgba(255,255,255,0.95);
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
    padding: 24px 32px;
    min-width: 220px;
    min-height: 80px;
}
QPushButton#modeBtn:hover {
    background-color: #9578D3;
}
QPushButton#modeBtn:pressed {
    background-color: #3B1D6B;
}
QFrame#divider {
    background-color: #E8E3F0;
    border: none;
}
QPushButton#quitBtn {
    background-color: #E04848;
    color: rgba(255,255,255,0.92);
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    padding: 7px 18px;
}
QPushButton#quitBtn:hover {
    background-color: #C53030;
}
"""

MODE_ID_SETUP = "id_setup"
MODE_SINGLE = "single"
MODE_SOARM101 = "soarm101"


class ModeSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motor Test — RoboSEasy")
        self.setFixedSize(760, 480)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )

        self.selected_mode: str | None = None

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_header())
        root.addLayout(self._build_body())

    # ── Header ──

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(52)
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(10)

        from resources import resource_path
        logo_path = resource_path("logo.png")
        if os.path.isfile(logo_path):
            logo_label = QLabel()
            pix = QPixmap(logo_path).scaledToHeight(
                28, Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(pix)
        else:
            logo_label = QLabel("LOGO")
            logo_label.setFixedSize(60, 28)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setStyleSheet(
                "background-color: rgba(255,255,255,0.12); border-radius: 6px;"
                "color: rgba(255,255,255,0.7); font-size: 11px; font-weight: bold;"
            )
        h.addWidget(logo_label)

        sep = QFrame()
        sep.setFixedSize(1, 20)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.2);")
        h.addWidget(sep)

        title = QLabel("Motor Test & ID Setup")
        title.setObjectName("headerTitle")
        h.addWidget(title)

        h.addStretch()

        subtitle = QLabel("STS3215 Servo Motor — RoboSEasy")
        subtitle.setObjectName("headerSubtitle")
        h.addWidget(subtitle)

        return header

    # ── Body ──

    def _build_body(self) -> QVBoxLayout:
        body = QVBoxLayout()
        body.setSpacing(16)
        body.setContentsMargins(40, 24, 40, 20)

        # ── Section 1: 모터 ID 셋업 ──
        setup_label = QLabel("모터 ID를 셋업하세요")
        setup_label.setObjectName("sectionLabel")
        setup_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(setup_label)

        setup_btn = QPushButton("모터 ID 셋업")
        setup_btn.setObjectName("setupBtn")
        setup_btn.clicked.connect(self._select_id_setup)
        setup_row = QHBoxLayout()
        setup_row.addStretch()
        setup_row.addWidget(setup_btn)
        setup_row.addStretch()
        body.addLayout(setup_row)

        # ── Divider ──
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        body.addWidget(divider)

        body.addSpacing(4)

        # ── Section 2: 테스트 모드 선택 ──
        prompt = QLabel("테스트 모드를 선택하세요")
        prompt.setObjectName("promptLabel")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(prompt)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        single_btn = QPushButton("단일 모터 테스트")
        single_btn.setObjectName("modeBtn")
        single_btn.clicked.connect(self._select_single)
        btn_row.addWidget(single_btn)

        soarm_btn = QPushButton("SO-ARM 101\n전체 모터 테스트")
        soarm_btn.setObjectName("modeBtn")
        soarm_btn.clicked.connect(self._select_soarm101)
        btn_row.addWidget(soarm_btn)

        body.addLayout(btn_row)

        quit_row = QHBoxLayout()
        quit_row.addStretch()
        quit_btn = QPushButton("종료")
        quit_btn.setObjectName("quitBtn")
        quit_btn.clicked.connect(self.reject)
        quit_row.addWidget(quit_btn)
        body.addLayout(quit_row)

        return body

    # ── Slots ──

    def _select_id_setup(self):
        self.selected_mode = MODE_ID_SETUP
        self.accept()

    def _select_single(self):
        self.selected_mode = MODE_SINGLE
        self.accept()

    def _select_soarm101(self):
        self.selected_mode = MODE_SOARM101
        self.accept()
