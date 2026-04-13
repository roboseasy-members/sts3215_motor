"""
모터 ID 셋업 마법사
모터를 한 대씩 연결하면서 순차적으로 ID를 할당하는 반자동 워크플로우
"""
import os
import serial.tools.list_ports

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from motor_controller import MotorController

# SO-ARM 101 기본 모터 구성 (ID: 이름)
SOARM101_MOTORS = {
    1: "Base (회전)",
    2: "Shoulder (어깨)",
    3: "Elbow (팔꿈치)",
    4: "Wrist Flex (손목 상하)",
    5: "Wrist Roll (손목 회전)",
    6: "Gripper (그리퍼)",
}

COLOR_HEADER = "#3B1D6B"
COLOR_BG = "#F5F3F8"
COLOR_CARD = "#FFFFFF"
COLOR_BORDER = "#E8E3F0"
COLOR_ACCENT = "#7C5CBF"
COLOR_SUCCESS = "#5BAD7A"
COLOR_DANGER = "#E04848"
COLOR_ORANGE = "#E8833A"
COLOR_WAITING = "#A99BBF"
COLOR_TEXT = "#2D2640"

STYLESHEET = """
QMainWindow { background-color: #F5F3F8; }
QWidget#centralWidget { background-color: #F5F3F8; }

QFrame#headerBar {
    background-color: #3B1D6B;
    border: none;
    min-height: 48px;
}
QLabel#headerTitle {
    color: rgba(255,255,255,0.95);
    font-size: 16px;
    font-weight: bold;
}
QLabel#headerSubtitle {
    color: rgba(255,255,255,0.50);
    font-size: 11px;
}

QLabel { color: #2D2640; font-size: 12px; }

QPushButton {
    background-color: #7C5CBF;
    color: rgba(255,255,255,0.92);
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton:hover { background-color: #9578D3; }
QPushButton:pressed { background-color: #3B1D6B; }
QPushButton:disabled { background-color: #E8E3F0; color: #A99BBF; }

QPushButton#assignBtn {
    background-color: #E8833A;
    font-size: 14px;
    font-weight: 700;
    padding: 14px 32px;
    border-radius: 8px;
    min-width: 260px;
}
QPushButton#assignBtn:hover { background-color: #F09A55; }
QPushButton#assignBtn:pressed { background-color: #C06A28; }
QPushButton#assignBtn:disabled { background-color: #E8E3F0; color: #A99BBF; }

QPushButton#backBtn {
    background-color: transparent;
    color: #7C5CBF;
    border: 1px solid #7C5CBF;
    font-size: 11px;
    padding: 5px 14px;
}
QPushButton#backBtn:hover { background-color: rgba(124,92,191,0.08); }

QPushButton#refreshBtn {
    background-color: transparent;
    color: #7C5CBF;
    border: 1px solid #E8E3F0;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    min-width: 32px;
}
QPushButton#refreshBtn:hover { background-color: rgba(124,92,191,0.08); }

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #E8E3F0;
    border-radius: 6px;
    padding: 6px 10px;
    color: #2D2640;
    font-size: 12px;
    min-width: 180px;
}
QComboBox:hover { border-color: #7C5CBF; }
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E8E3F0;
    color: #A99BBF;
    font-size: 11px;
}
"""


class IdSetupWizard(QMainWindow):
    back_to_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("모터 ID 셋업 — RoboSEasy")
        self.setFixedSize(700, 620)
        self.setStyleSheet(STYLESHEET)

        self._controller = MotorController()
        self._current_step = 0  # 0-based index into SOARM101_MOTORS
        self._motor_ids = list(SOARM101_MOTORS.keys())
        self._completed = set()

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_connection_panel())
        root.addWidget(self._build_instruction_panel())
        root.addWidget(self._build_step_list())
        root.addStretch()

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("포트를 선택하고 연결하세요")

    # ── Header ──

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(48)
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(10)

        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "logo.png"
        )
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

        title = QLabel("모터 ID 셋업 마법사")
        title.setObjectName("headerTitle")
        h.addWidget(title)

        h.addStretch()

        back_btn = QPushButton("뒤로")
        back_btn.setObjectName("backBtn")
        back_btn.setStyleSheet(
            "color: rgba(255,255,255,0.7); border-color: rgba(255,255,255,0.3);"
        )
        back_btn.clicked.connect(self._on_back)
        h.addWidget(back_btn)

        return header

    # ── Connection Panel ──

    def _build_connection_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("connPanel")
        panel.setStyleSheet(
            f"QWidget#connPanel {{ background-color: {COLOR_CARD}; border-bottom: 1px solid {COLOR_BORDER}; }}"
        )
        h = QHBoxLayout(panel)
        h.setContentsMargins(20, 10, 20, 10)
        h.setSpacing(10)

        h.addWidget(QLabel("포트:"))

        self._port_combo = QComboBox()
        self._refresh_ports()
        h.addWidget(self._port_combo)

        refresh_btn = QPushButton("새로고침")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self._refresh_ports)
        h.addWidget(refresh_btn)

        h.addSpacing(10)

        self._connect_btn = QPushButton("연결")
        self._connect_btn.clicked.connect(self._toggle_connection)
        h.addWidget(self._connect_btn)

        self._led = QLabel()
        self._led.setFixedSize(14, 14)
        self._update_led(False)
        h.addWidget(self._led)

        h.addStretch()

        return panel

    # ── Instruction Panel ──

    def _build_instruction_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(12)

        self._step_title = QLabel()
        self._step_title.setFont(QFont("", 16, QFont.Weight.Bold))
        self._step_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._step_title)

        self._instruction = QLabel()
        self._instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._instruction.setStyleSheet("font-size: 13px; color: #A99BBF;")
        self._instruction.setWordWrap(True)
        layout.addWidget(self._instruction)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._assign_btn = QPushButton("연결 확인 && ID 할당")
        self._assign_btn.setObjectName("assignBtn")
        self._assign_btn.setEnabled(False)
        self._assign_btn.clicked.connect(self._do_assign)
        btn_row.addWidget(self._assign_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._update_step_ui()

        return panel

    # ── Step List ──

    def _build_step_list(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(6)

        self._step_rows = {}
        for motor_id, name in SOARM101_MOTORS.items():
            row = QHBoxLayout()
            row.setSpacing(10)

            icon_label = QLabel()
            icon_label.setFixedSize(22, 22)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet(
                f"background-color: {COLOR_WAITING}; border-radius: 11px;"
                f"color: white; font-size: 11px; font-weight: bold;"
            )
            icon_label.setText(str(motor_id))
            row.addWidget(icon_label)

            text_label = QLabel(f"ID {motor_id} — {name}")
            text_label.setStyleSheet("font-size: 13px;")
            row.addWidget(text_label)

            row.addStretch()

            status_label = QLabel("대기")
            status_label.setStyleSheet(f"color: {COLOR_WAITING}; font-size: 12px;")
            row.addWidget(status_label)

            layout.addLayout(row)
            self._step_rows[motor_id] = {
                "icon": icon_label,
                "text": text_label,
                "status": status_label,
            }

        self._update_step_list()
        return container

    # ── Port Handling ──

    def _refresh_ports(self):
        self._port_combo.clear()
        ports = serial.tools.list_ports.comports()
        usb_ports = []
        other_ports = []
        for p in ports:
            desc = f"{p.device} — {p.description}"
            if "USB" in p.description.upper() or "ACM" in p.device.upper():
                usb_ports.append((p.device, desc))
            elif not p.device.startswith("/dev/ttyS"):
                other_ports.append((p.device, desc))
        for dev, desc in usb_ports + other_ports:
            self._port_combo.addItem(desc, dev)

    def _toggle_connection(self):
        if self._controller.connected:
            self._controller.disconnect()
            self._connect_btn.setText("연결")
            self._assign_btn.setEnabled(False)
            self._update_led(False)
            self.statusBar().showMessage("연결 해제됨")
        else:
            port = self._port_combo.currentData()
            if not port:
                QMessageBox.warning(self, "오류", "포트를 선택하세요.")
                return
            try:
                self._controller.connect(port)
                self._connect_btn.setText("연결 해제")
                self._assign_btn.setEnabled(True)
                self._update_led(True)
                self.statusBar().showMessage(f"{port} 연결됨")
            except Exception as e:
                QMessageBox.critical(self, "연결 실패", str(e))

    def _update_led(self, connected: bool):
        color = COLOR_SUCCESS if connected else COLOR_DANGER
        self._led.setStyleSheet(
            f"background-color: {color}; border-radius: 7px; border: none;"
        )

    # ── Step Logic ──

    def _update_step_ui(self):
        if self._current_step >= len(self._motor_ids):
            self._step_title.setText("모든 모터 ID 셋업 완료!")
            self._step_title.setStyleSheet(f"color: {COLOR_SUCCESS};")
            self._instruction.setText(
                "모든 모터의 ID가 할당되었습니다.\n"
                "뒤로 가서 'SO-ARM 101 전체 모터 테스트'를 진행하세요."
            )
            self._assign_btn.setEnabled(False)
            self._assign_btn.setText("완료")
            return

        target_id = self._motor_ids[self._current_step]
        name = SOARM101_MOTORS[target_id]
        step_num = self._current_step + 1
        total = len(self._motor_ids)

        self._step_title.setText(f"Step {step_num}/{total}: ID {target_id} 할당")
        self._step_title.setStyleSheet(f"color: {COLOR_TEXT};")
        self._instruction.setText(
            f"'{name}' 모터 1대만 버스에 연결한 후 아래 버튼을 누르세요.\n"
            f"(이전에 할당한 모터는 연결된 상태로 두어도 됩니다)"
        )
        self._assign_btn.setText(f"연결 확인 && ID {target_id} 할당")
        if self._controller.connected:
            self._assign_btn.setEnabled(True)

    def _update_step_list(self):
        for motor_id, widgets in self._step_rows.items():
            idx = self._motor_ids.index(motor_id)
            if motor_id in self._completed:
                widgets["icon"].setStyleSheet(
                    f"background-color: {COLOR_SUCCESS}; border-radius: 11px;"
                    f"color: white; font-size: 11px; font-weight: bold;"
                )
                widgets["status"].setText("완료")
                widgets["status"].setStyleSheet(
                    f"color: {COLOR_SUCCESS}; font-size: 12px; font-weight: bold;"
                )
            elif idx == self._current_step:
                widgets["icon"].setStyleSheet(
                    f"background-color: {COLOR_ORANGE}; border-radius: 11px;"
                    f"color: white; font-size: 11px; font-weight: bold;"
                )
                widgets["status"].setText("진행 중")
                widgets["status"].setStyleSheet(
                    f"color: {COLOR_ORANGE}; font-size: 12px; font-weight: bold;"
                )
            else:
                widgets["icon"].setStyleSheet(
                    f"background-color: {COLOR_WAITING}; border-radius: 11px;"
                    f"color: white; font-size: 11px; font-weight: bold;"
                )
                widgets["status"].setText("대기")
                widgets["status"].setStyleSheet(
                    f"color: {COLOR_WAITING}; font-size: 12px;"
                )

    def _do_assign(self):
        if not self._controller.connected:
            QMessageBox.warning(self, "오류", "먼저 포트에 연결하세요.")
            return

        target_id = self._motor_ids[self._current_step]
        name = SOARM101_MOTORS[target_id]

        # 이미 할당된 ID 목록 (이전 스텝에서 할당한 모터들)
        already_assigned = sorted(self._completed)

        # 1) 버스 스캔 — 현재 연결된 모터 확인
        self.statusBar().showMessage("모터 스캔 중...")
        self._assign_btn.setEnabled(False)

        found = self._controller.scan_motors(range(0, 30))

        # 이전에 할당한 모터를 제외하고 새 모터 찾기
        new_motors = [mid for mid in found if mid not in self._completed]

        if len(new_motors) == 0:
            QMessageBox.warning(
                self,
                "모터 없음",
                "새로운 모터를 찾을 수 없습니다.\n"
                "모터가 버스에 연결되어 있고 전원이 켜져 있는지 확인하세요.",
            )
            self._assign_btn.setEnabled(True)
            self.statusBar().showMessage("모터를 찾을 수 없음")
            return

        if len(new_motors) > 1:
            ids_str = ", ".join(str(m) for m in new_motors)
            QMessageBox.warning(
                self,
                "모터가 여러 대 감지됨",
                f"새 모터가 {len(new_motors)}대 감지되었습니다 (ID: {ids_str}).\n"
                f"ID가 할당되지 않은 모터를 1대만 연결한 상태에서 다시 시도하세요.",
            )
            self._assign_btn.setEnabled(True)
            self.statusBar().showMessage("모터를 1대만 연결해주세요")
            return

        # 새 모터 1대 발견
        source_id = new_motors[0]

        if source_id == target_id:
            # 이미 원하는 ID — 변경 불필요
            self.statusBar().showMessage(
                f"모터가 이미 ID {target_id}입니다. 변경 불필요!"
            )
        else:
            # ID 변경
            try:
                self._controller.change_id(source_id, target_id)
                self.statusBar().showMessage(
                    f"ID {source_id} → {target_id} 변경 완료!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "ID 변경 실패",
                    f"ID 변경 중 오류가 발생했습니다:\n{e}",
                )
                self._assign_btn.setEnabled(True)
                return

        # 변경 확인 — ping
        if self._controller.ping(target_id):
            self._completed.add(target_id)
            self._current_step += 1
            self._update_step_ui()
            self._update_step_list()

            if self._current_step >= len(self._motor_ids):
                self.statusBar().showMessage("모든 모터 ID 셋업 완료!")
                QMessageBox.information(
                    self,
                    "완료",
                    "모든 모터의 ID가 성공적으로 할당되었습니다!\n"
                    "뒤로 가서 'SO-ARM 101 전체 모터 테스트'를 진행하세요.",
                )
            else:
                next_id = self._motor_ids[self._current_step]
                next_name = SOARM101_MOTORS[next_id]
                self.statusBar().showMessage(
                    f"ID {target_id} ({name}) 완료 — "
                    f"다음: ID {next_id} ({next_name}) 모터를 연결하세요"
                )
        else:
            QMessageBox.warning(
                self,
                "확인 실패",
                f"ID {target_id}으로 변경했지만 핑 응답이 없습니다.\n"
                f"모터 연결 상태를 확인하고 다시 시도하세요.",
            )
            self._assign_btn.setEnabled(True)

    # ── Navigation ──

    def _on_back(self):
        if self._controller.connected:
            self._controller.disconnect()
        self.back_to_menu.emit()

    def closeEvent(self, event):
        if self._controller.connected:
            self._controller.disconnect()
        event.accept()
