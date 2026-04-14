"""
모터 ID 셋업 마법사
모터를 한 대씩 연결하면서 순차적으로 ID를 할당하는 반자동 워크플로우
"""
import os
import serial.tools.list_ports

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from motor_controller import MotorController, MotorStatus

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
    font-size: 13px;
    font-weight: 700;
    padding: 7px 22px;
    border-radius: 6px;
    min-width: 220px;
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

QFrame#statusCard {
    background-color: #FFFFFF;
    border: 1px solid #E8E3F0;
    border-radius: 8px;
}
QLabel#statusTitle {
    color: #A99BBF;
    font-size: 11px;
    font-weight: 600;
}
QLabel#statusValue {
    color: #7C5CBF;
    font-size: 14px;
    font-weight: bold;
}
QLabel#statusUnit {
    color: #A99BBF;
    font-size: 10px;
    margin-top: -2px;
}
QFrame#monitorPanel {
    background-color: #F9F7FC;
    border: 1px solid #E8E3F0;
    border-radius: 8px;
}
"""


class ScanWorker(QThread):
    """단일 모터 테스트(main_window.py)와 동일한 스캔 워커 — UI 블로킹 방지"""
    found = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, controller: MotorController, id_range: range):
        super().__init__()
        self._controller = controller
        self._id_range = id_range

    def run(self):
        found = []
        total = len(self._id_range)
        for i, motor_id in enumerate(self._id_range):
            try:
                if self._controller.ping(motor_id):
                    found.append(motor_id)
            except Exception:
                pass
            self.progress.emit(int((i + 1) / total * 100))
        self.found.emit(found)


class CenteringDialog(QDialog):
    """커스텀 중앙 정렬 진행 다이얼로그 — QProgressDialog보다 안정적으로 리페인트"""

    def __init__(self, parent, title_text: str):
        super().__init__(parent)
        self.setWindowTitle("중앙 정렬 진행 중")
        self.setModal(True)
        self.setFixedSize(440, 170)
        # 닫기 버튼 비활성화 (중간에 닫지 못하게)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        self.label = QLabel(title_text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 12px; color: #2D2640;")
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFixedHeight(22)
        self.progress.setStyleSheet(
            "QProgressBar { border: 1px solid #E8E3F0; border-radius: 4px;"
            " background-color: #F5F3F8; text-align: center; color: #2D2640;"
            " font-weight: 600; font-size: 11px; }"
            "QProgressBar::chunk { background-color: #7C5CBF; border-radius: 3px; }"
        )
        layout.addWidget(self.progress)

    def update_progress(self, value: int, text: str):
        self.progress.setValue(max(0, min(100, value)))
        self.label.setText(text)
        # 강제 리페인트 (타이머 콜백 중에도 UI가 즉시 갱신되도록)
        self.progress.repaint()
        self.label.repaint()


class IdSetupWizard(QMainWindow):
    back_to_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("모터 ID 셋업 — RoboSEasy")
        self.setMinimumSize(760, 760)
        self.resize(760, 780)
        self.setStyleSheet(STYLESHEET)

        self._controller = MotorController()
        self._current_step = 0  # 0-based index into _motor_ids
        # 할당 순서: 6 → 5 → 4 → 3 → 2 → 1 (공장기본 ID=1 충돌 방지)
        self._motor_ids = list(reversed(list(SOARM101_MOTORS.keys())))
        self._completed = set()

        # 실시간 상태 모니터링
        self._monitor_id: int | None = None
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_status)

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

        # 1단계: 스캔 버튼 + 발견된 모터 콤보
        scan_row = QHBoxLayout()
        scan_row.addStretch()
        scan_row.addWidget(QLabel("1. 모터 스캔:"))
        self._scan_btn = QPushButton("🔍 모터 스캔")
        self._scan_btn.setEnabled(False)
        self._scan_btn.clicked.connect(self._do_scan)
        scan_row.addWidget(self._scan_btn)

        self._found_combo = QComboBox()
        self._found_combo.setEnabled(False)
        scan_row.addWidget(self._found_combo)
        scan_row.addStretch()
        layout.addLayout(scan_row)

        # 2단계: ID 할당 버튼
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._assign_btn = QPushButton("연결 확인 && ID 할당")
        self._assign_btn.setObjectName("assignBtn")
        self._assign_btn.setEnabled(False)
        self._assign_btn.clicked.connect(self._do_assign)
        btn_row.addWidget(self._assign_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 상태 모니터 패널 (스캔 완료 시 자동으로 표시/시작)
        self._monitor_panel = self._build_monitor_panel()
        self._monitor_panel.setVisible(False)
        layout.addWidget(self._monitor_panel)

        self._update_step_ui()

        return panel

    def _build_monitor_panel(self) -> QFrame:
        """단일 모터 테스트의 '상태 모니터'와 동일한 카드형 디스플레이"""
        panel = QFrame()
        panel.setObjectName("monitorPanel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(8)

        # 제목 + 대상 모터 표시
        header = QHBoxLayout()
        title = QLabel("📊 상태 모니터")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {COLOR_TEXT};"
        )
        header.addWidget(title)
        header.addStretch()
        self._monitor_target_label = QLabel("— 모터: —")
        self._monitor_target_label.setStyleSheet(
            f"font-size: 12px; color: {COLOR_ACCENT}; font-weight: 600;"
        )
        header.addWidget(self._monitor_target_label)
        v.addLayout(header)

        # 상태 카드 그리드 — 값과 단위를 한 줄에 합쳐서 세로 공간 절약
        grid = QHBoxLayout()
        grid.setSpacing(6)
        self._status_labels: dict[str, QLabel] = {}
        self._status_units: dict[str, str] = {
            "위치": "",
            "속도": "",
            "온도": "°C",
            "전압": "V",
            "전류": "mA",
            "부하": "%",
        }
        for name, unit in self._status_units.items():
            frame = QFrame()
            frame.setObjectName("statusCard")
            frame.setMinimumWidth(95)
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(6, 6, 6, 6)
            fl.setSpacing(2)

            header_txt = f"{name} ({unit})" if unit else name
            t = QLabel(header_txt)
            t.setObjectName("statusTitle")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(t)

            val = QLabel("--")
            val.setObjectName("statusValue")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(val)

            self._status_labels[name] = val
            grid.addWidget(frame)
        v.addLayout(grid)

        return panel

    # ── Step List ──

    def _build_step_list(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(6)

        self._step_rows = {}
        for motor_id in self._motor_ids:
            name = SOARM101_MOTORS[motor_id]
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

            value_label = QLabel("")
            value_label.setStyleSheet(
                f"color: {COLOR_ACCENT}; font-size: 12px; font-weight: 600;"
            )
            row.addWidget(value_label)

            row.addStretch()

            status_label = QLabel("대기")
            status_label.setStyleSheet(f"color: {COLOR_WAITING}; font-size: 12px;")
            row.addWidget(status_label)

            layout.addLayout(row)
            self._step_rows[motor_id] = {
                "icon": icon_label,
                "text": text_label,
                "value": value_label,
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
            self._stop_monitoring()
            self._monitor_panel.setVisible(False)
            self._monitor_id = None
            self._controller.disconnect()
            self._connect_btn.setText("연결")
            self._scan_btn.setEnabled(False)
            self._assign_btn.setEnabled(False)
            self._found_combo.setEnabled(False)
            self._found_combo.clear()
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
                self._scan_btn.setEnabled(True)
                self._update_led(True)
                self.statusBar().showMessage(
                    f"{port} 연결됨 — 모터를 1대 연결하고 '모터 스캔' 버튼을 누르세요"
                )
            except Exception as e:
                msg = str(e)
                hint = ""
                if "PermissionError" in msg or "액세스" in msg or "Access" in msg:
                    hint = (
                        "\n\n포트가 이미 열려 있거나 다른 프로세스가 점유 중입니다.\n"
                        "• 수 초 후 다시 연결 버튼을 눌러주세요 (자동 재시도 중).\n"
                        "• 다른 시리얼 프로그램(PuTTY, Arduino IDE 등)이 있다면 종료하세요.\n"
                        "• 그래도 안 되면 USB 케이블을 뺏다 다시 꽂아주세요."
                    )
                QMessageBox.critical(self, "연결 실패", f"{msg}{hint}")

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
            self._scan_btn.setEnabled(False)
            self._assign_btn.setEnabled(False)
            self._assign_btn.setText("완료")
            self._found_combo.setEnabled(False)
            self._found_combo.clear()
            return

        target_id = self._motor_ids[self._current_step]
        name = SOARM101_MOTORS[target_id]
        step_num = self._current_step + 1
        total = len(self._motor_ids)

        self._step_title.setText(f"Step {step_num}/{total}: ID {target_id} 할당")
        self._step_title.setStyleSheet(f"color: {COLOR_TEXT};")
        self._instruction.setText(
            f"'{name}' 모터 1대만 버스에 연결한 후\n"
            f"① '모터 스캔' → ② 할당 버튼 순서로 진행하세요.\n"
            f"(이전 스텝의 모터는 분리해주세요)"
        )
        self._assign_btn.setText(f"✨ ID {target_id} 할당")
        # 할당 버튼은 스캔 결과가 나와야 활성화됨
        self._assign_btn.setEnabled(False)
        self._found_combo.clear()
        self._found_combo.setEnabled(False)
        # 스캔 버튼은 연결되어 있으면 다시 활성화
        self._scan_btn.setEnabled(self._controller.connected)
        # 다음 스텝 진입 시 모니터 중지/숨김
        if hasattr(self, "_monitor_panel"):
            self._stop_monitoring()
            self._monitor_panel.setVisible(False)

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

    # ── 스캔 (단일 모터 테스트 방식) ──

    def _do_scan(self):
        """단일 모터 테스트(main_window.py)와 동일한 ScanWorker 기반 스캔"""
        if not self._controller.connected:
            QMessageBox.warning(self, "오류", "먼저 포트에 연결하세요.")
            return

        self._scan_btn.setEnabled(False)
        self._assign_btn.setEnabled(False)
        self._found_combo.clear()
        self._found_combo.setEnabled(False)

        progress = QProgressDialog("모터 스캔 중...", "취소", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        # SO-ARM 101은 ID 1~6만 사용하므로 1~7 범위로 한정 (29까지 스캔하던 기존 대비 ~4배 빠름)
        self._scan_worker = ScanWorker(self._controller, range(1, 8))
        self._scan_worker.progress.connect(progress.setValue)

        def on_found(ids: list[int]):
            progress.close()
            self._on_scan_found(ids)

        self._scan_worker.found.connect(on_found)
        self._scan_worker.start()

    def _on_scan_found(self, ids: list[int]):
        self._scan_btn.setEnabled(True)

        if not ids:
            self.statusBar().showMessage("스캔 완료: 모터를 찾을 수 없음")
            # 모터 없음 — 모니터 숨김
            self._stop_monitoring()
            self._monitor_panel.setVisible(False)
            QMessageBox.warning(
                self,
                "모터 없음",
                "모터를 찾을 수 없습니다.\n"
                "모터가 버스에 연결되어 있고 전원이 켜져 있는지 확인하세요.",
            )
            return

        self._found_combo.clear()
        for mid in ids:
            self._found_combo.addItem(f"ID: {mid}", mid)
        # 콤보 선택 변경 시 모니터 대상도 갱신
        try:
            self._found_combo.currentIndexChanged.disconnect()
        except TypeError:
            pass
        self._found_combo.currentIndexChanged.connect(self._on_found_combo_changed)

        self._found_combo.setEnabled(True)
        self._found_combo.setCurrentIndex(0)
        self._assign_btn.setEnabled(True)

        target_id = self._motor_ids[self._current_step]
        if len(ids) == 1:
            self.statusBar().showMessage(
                f"스캔 완료: ID {ids[0]} 발견 — ID {target_id}로 할당하세요"
            )
        else:
            ids_str = ", ".join(str(m) for m in ids)
            self.statusBar().showMessage(
                f"⚠ 모터 {len(ids)}대 감지됨 [{ids_str}] — 1대만 연결한 뒤 재스캔 권장"
            )

        # 스캔 완료 → 상태 모니터 자동 표시 및 폴링 시작
        source_id = self._found_combo.currentData()
        self._monitor_id = source_id
        self._monitor_target_label.setText(f"ID {source_id}")
        self._monitor_target_label.setStyleSheet(
            f"font-size: 13px; color: {COLOR_ACCENT}; font-weight: 600;"
        )
        self._monitor_panel.setVisible(True)
        self._start_monitoring()

    def _on_found_combo_changed(self, idx: int):
        if idx < 0:
            return
        mid = self._found_combo.itemData(idx)
        if mid is None:
            return
        self._monitor_id = mid
        self._monitor_target_label.setText(f"ID {mid}")

    # ── 모니터링 (단일 모터 테스트 _start/_stop/_poll 과 동일 패턴) ──

    def _start_monitoring(self):
        if self._monitor_id is None:
            return
        self._poll_timer.start(200)

    def _stop_monitoring(self):
        self._poll_timer.stop()
        # 상태 라벨 초기화
        if hasattr(self, "_status_labels"):
            for lbl in self._status_labels.values():
                lbl.setText("--")

    def _poll_status(self):
        if self._monitor_id is None or not self._controller.connected:
            return
        try:
            status = self._controller.read_status(self._monitor_id)
            self._update_status_display(status)
        except Exception:
            pass

    def _update_status_display(self, status: MotorStatus):
        def safe_val(v, fmt="d"):
            if isinstance(v, tuple):
                v = v[0] if v else 0
            if fmt == "d":
                return str(int(v)) if v is not None else "--"
            elif fmt == ".1f":
                return f"{float(v):.1f}" if v is not None else "--"
            return str(v) if v is not None else "--"

        self._status_labels["위치"].setText(safe_val(status.position))
        self._status_labels["속도"].setText(safe_val(status.speed))
        self._status_labels["온도"].setText(safe_val(status.temperature))
        self._status_labels["전압"].setText(safe_val(status.voltage, ".1f"))
        self._status_labels["전류"].setText(safe_val(status.current))
        self._status_labels["부하"].setText(safe_val(status.load))

    def _do_assign(self):
        """스캔된 모터의 ID를 target_id로 변경. 재스캔으로 검증."""
        if not self._controller.connected:
            QMessageBox.warning(self, "오류", "먼저 포트에 연결하세요.")
            return

        if self._found_combo.count() == 0:
            QMessageBox.warning(self, "오류", "먼저 '모터 스캔'을 실행하세요.")
            return

        source_id = self._found_combo.currentData()
        target_id = self._motor_ids[self._current_step]
        name = SOARM101_MOTORS[target_id]

        # 확인 다이얼로그
        if source_id == target_id:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("ID 확인")
            msg.setText(
                f"모터가 이미 ID {target_id}입니다.\n"
                f"이 모터를 '{name}'로 확정하시겠습니까?"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if msg.exec() != QMessageBox.StandardButton.Yes:
                return
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("ID 변경")
            msg.setText(
                f"모터 ID를 변경하시겠습니까?\n"
                f"현재 ID: {source_id} → 새 ID: {target_id} ({name})"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            if msg.exec() != QMessageBox.StandardButton.Yes:
                return

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
                return

        # 모니터링 대상 ID를 새 ID로 전환
        self._monitor_id = target_id
        self._monitor_target_label.setText(f"ID {target_id} — {name}")
        self._monitor_target_label.setStyleSheet(
            f"font-size: 13px; color: {COLOR_SUCCESS}; font-weight: 700;"
        )

        # ID 변경 직후 — 토크 활성화 + 적응형 센터링 시작
        # 속도를 1000으로 시작, 2048에 가까워질수록 점점 감속, 오차 ±1 이내 도달 시 다음 스텝 진행
        self._assign_btn.setEnabled(False)
        self._scan_btn.setEnabled(False)
        self.statusBar().showMessage(
            f"ID {target_id} ({name}) — 중앙 위치(2048)로 이동 중..."
        )
        try:
            self._controller.set_torque(target_id, True)
        except Exception as e:
            QMessageBox.warning(
                self,
                "토크 활성화 실패",
                f"ID 변경은 완료됐지만 토크 활성화에 실패했습니다:\n{e}",
            )

        self._start_adaptive_centering(target_id, name)

    # ── 적응형 센터링 (2048 ±3 정밀 도달) ──

    _TARGET_POS = 2048
    _TARGET_TOLERANCE = 3           # 오차 ±3 이내면 완료 (STS3215 실제 정밀도 반영)
    _CENTERING_TICK_MS = 80         # 폴링 주기
    _CENTERING_MAX_TICKS = 75       # 안전장치: 75 × 80ms = 6초
    _STALL_MAX = 15                 # 15 tick(1.2초) 동안 개선 없으면 조기 종료

    def _start_adaptive_centering(self, target_id: int, name: str):
        """ID 할당 모터를 2048 위치로 적응형 속도로 정밀 이동.

        Fast-path: 이미 목표 허용오차 이내면 이동 명령 생략하고 즉시 다음 단계로.
        """
        # ── Fast-path: 이미 세팅된 모터면 바로 통과 ────────────────────
        try:
            status = self._controller.read_status(target_id)
            pos_now = status.position
            if isinstance(pos_now, tuple):
                pos_now = pos_now[0] if pos_now else 0
            pos_now = int(pos_now)
            if abs(pos_now - self._TARGET_POS) <= self._TARGET_TOLERANCE:
                # 이미 중앙에 있음 → 다이얼로그 없이 바로 _finish_step
                self._centering_id = target_id
                self._centering_name = name
                self._centering_last_speed = 0
                self._finish_step(target_id, name)
                return
        except Exception:
            pass

        # ── 일반 경로: 진행 다이얼로그 + 적응형 이동 ──────────────────
        self._centering_id = target_id
        self._centering_name = name
        self._centering_tick = 0
        self._centering_last_speed = None
        self._centering_best_error = None       # 지금까지 관찰된 최소 오차
        self._centering_stall_count = 0         # 개선 없이 지난 tick 수

        self._centering_dialog = CenteringDialog(
            self,
            f"ID {target_id} ({name}) — 중앙 위치(2048)로 이동 중..."
        )
        self._centering_dialog.show()

        self._centering_timer = QTimer(self)
        self._centering_timer.timeout.connect(self._centering_tick_fn)

        # 초기 이동 (최대 속도)
        self._issue_centering_move(1000)
        self._centering_timer.start(self._CENTERING_TICK_MS)

    def _issue_centering_move(self, speed: int):
        """2048로 이동 명령 재발행 (속도만 바뀜)"""
        try:
            self._controller.move_to(self._centering_id, self._TARGET_POS, speed=speed)
            self._centering_last_speed = speed
        except Exception:
            pass

    def _centering_tick_fn(self):
        """주기적으로 현재 위치를 읽어 속도를 동적으로 조절하고 도달 여부 판정"""
        self._centering_tick += 1

        # 현재 위치 읽기
        try:
            status = self._controller.read_status(self._centering_id)
            pos = status.position
            if isinstance(pos, tuple):
                pos = pos[0] if pos else 0
            pos = int(pos)
        except Exception:
            if self._centering_tick >= self._CENTERING_MAX_TICKS:
                self._stop_centering()
            return

        error = abs(pos - self._TARGET_POS)

        # 진행률 계산 — 절대 기준 (현재 위치가 2048에 얼마나 가까운지)
        # 2048±2048 범위를 0~100%로 매핑 (최대 이탈 2048 → 0%, 2048 도달 → 100%)
        progress = max(0, min(100, int(100 - (error / 2048) * 100)))
        self._centering_dialog.update_progress(
            progress,
            f"ID {self._centering_id} ({self._centering_name}) — 중앙 정렬\n\n"
            f"현재 위치: {pos}  /  목표: 2048\n"
            f"오차: {error}  |  속도: {self._centering_last_speed}"
        )

        # 완료 조건 (허용 오차 이내)
        if error <= self._TARGET_TOLERANCE:
            self._centering_dialog.update_progress(100, "완료!")
            self._stop_centering()
            return

        # 조기 종료 1: 타임아웃
        if self._centering_tick >= self._CENTERING_MAX_TICKS:
            self._stop_centering()
            return

        # 조기 종료 2: 개선 정체 감지 (stall)
        # 현재 오차가 지금까지 최소보다 크거나 같으면 stall 카운트 증가
        if self._centering_best_error is None or error < self._centering_best_error:
            self._centering_best_error = error
            self._centering_stall_count = 0
        else:
            self._centering_stall_count += 1
            if self._centering_stall_count >= self._STALL_MAX:
                # 개선 안 됨 → 현재 위치 수용하고 진행
                self._stop_centering()
                return

        # 오차에 따라 속도 결정 — 멀면 빠르게, 가까우면 정밀하게
        # (Tolerance가 ±3이므로 error ≤ 3 구간은 위의 완료 분기에서 처리됨)
        if error > 50:
            target_speed = 1000
        elif error > 10:
            target_speed = 400
        else:
            target_speed = 150   # 최소 이동 가능 속도 (정지 마찰 극복)

        # 속도가 바뀔 때만 move_to 재발행
        if target_speed != self._centering_last_speed:
            self._issue_centering_move(target_speed)

        self.statusBar().showMessage(
            f"ID {self._centering_id} — 위치 {pos} (오차 {error}, 속도 {target_speed})"
        )

    def _stop_centering(self):
        """센터링 타이머 중지 + 다이얼로그 닫기 + 다음 스텝으로 진행"""
        if hasattr(self, "_centering_timer") and self._centering_timer is not None:
            self._centering_timer.stop()
            self._centering_timer = None
        if hasattr(self, "_centering_dialog") and self._centering_dialog is not None:
            self._centering_dialog.close()
            self._centering_dialog = None
        self._finish_step(self._centering_id, self._centering_name)

    def _finish_step(self, target_id: int, name: str):
        """ID 할당 + 이동 완료 후 호출 — 다음 스텝으로 진행"""
        # 이동 완료 시점의 최종 위치/속도 값을 읽어서 스텝 리스트에 보라색으로 표시
        try:
            status = self._controller.read_status(target_id)
            pos = status.position
            spd = status.speed
            if isinstance(pos, tuple):
                pos = pos[0] if pos else 0
            if isinstance(spd, tuple):
                spd = spd[0] if spd else 0
            value_text = f"위치: {int(pos)}, 속도: {int(spd)}"
        except Exception:
            value_text = "위치: 2048, 속도: --"

        if target_id in self._step_rows:
            self._step_rows[target_id]["value"].setText(value_text)

        self._completed.add(target_id)
        self._current_step += 1
        self._update_step_list()

        if self._current_step >= len(self._motor_ids):
            self._update_step_ui()
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
            self._update_step_ui()
            QMessageBox.information(
                self,
                f"Step {self._current_step} 완료",
                f"ID {target_id} ({name}) 할당 + 중앙(2048) 이동 완료!\n\n"
                f"다음 단계: ID {next_id} ({next_name})\n"
                f"현재 모터를 분리하고 다음 모터를 연결한 뒤\n"
                f"'모터 스캔' 버튼을 누르세요.",
            )
            self.statusBar().showMessage(
                f"ID {target_id} ({name}) 완료 — 다음: ID {next_id} ({next_name})"
            )

    # ── Navigation ──

    def _cleanup_centering(self):
        if hasattr(self, "_centering_timer") and self._centering_timer is not None:
            self._centering_timer.stop()
            self._centering_timer = None
        if hasattr(self, "_centering_dialog") and self._centering_dialog is not None:
            self._centering_dialog.close()
            self._centering_dialog = None

    def _on_back(self):
        self._stop_monitoring()
        self._cleanup_centering()
        if self._controller.connected:
            self._controller.disconnect()
        self.back_to_menu.emit()

    def closeEvent(self, event):
        self._stop_monitoring()
        self._cleanup_centering()
        if self._controller.connected:
            self._controller.disconnect()
        event.accept()
