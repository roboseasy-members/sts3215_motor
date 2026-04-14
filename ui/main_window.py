import os
import serial.tools.list_ports
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIntValidator, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSlider,
    QSpinBox,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from motor_controller import MotorController, MotorStatus

# ── Design System Colors ──
COLOR_HEADER = "#3B1D6B"
COLOR_TEXT = "#2D2640"
COLOR_ACCENT = "#7C5CBF"
COLOR_ACCENT_HOVER = "#9578D3"
COLOR_MUTED = "#A99BBF"
COLOR_BG = "#F5F3F8"
COLOR_CARD = "#FFFFFF"
COLOR_CARD_BORDER = "#E8E3F0"
COLOR_BAR_START = "#A78BDA"
COLOR_BAR_END = "#C4B2EC"
COLOR_SUCCESS = "#5BAD7A"
COLOR_DANGER = "#E04848"

# ── Global Stylesheet ──
STYLESHEET = """
/* ── Global ── */
QMainWindow {
    background-color: #F5F3F8;
}
QWidget#centralWidget {
    background-color: #F5F3F8;
}

/* ── Header bar ── */
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

/* ── Card panels (QGroupBox) ── */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E8E3F0;
    border-radius: 10px;
    margin-top: 8px;
    padding: 14px 12px 10px 12px;
    font-size: 12px;
    font-weight: 600;
    color: #2D2640;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 12px;
    background-color: #7C5CBF;
    color: rgba(255,255,255,0.92);
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}

/* ── Labels ── */
QLabel {
    color: #2D2640;
    font-size: 12px;
}
QLabel#statusTitle {
    color: #A99BBF;
    font-size: 11px;
    font-weight: 600;
}
QLabel#statusValue {
    color: #7C5CBF;
    font-size: 16px;
    font-weight: bold;
}
QLabel#statusUnit {
    color: #A99BBF;
    font-size: 10px;
}

/* ── Buttons ── */
QPushButton {
    background-color: #7C5CBF;
    color: rgba(255,255,255,0.92);
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #9578D3;
}
QPushButton:pressed {
    background-color: #3B1D6B;
}
QPushButton:disabled {
    background-color: #E8E3F0;
    color: #A99BBF;
}
QPushButton#connectBtn {
    padding: 7px 24px;
    font-size: 13px;
}
QPushButton#refreshBtn {
    background-color: transparent;
    color: #7C5CBF;
    border: 1px solid #A99BBF;
}
QPushButton#refreshBtn:hover {
    background-color: #7C5CBF;
    color: white;
    border-color: #7C5CBF;
}
QPushButton#refreshBtn:disabled {
    background-color: transparent;
    color: #E8E3F0;
    border-color: #E8E3F0;
}
QPushButton#dangerBtn {
    background-color: #E04848;
}
QPushButton#dangerBtn:hover {
    background-color: #C53030;
}
QPushButton#quitBtn {
    background-color: #E04848;
}
QPushButton#quitBtn:hover {
    background-color: #C53030;
}

/* ── ComboBox ── */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #A99BBF;
    border-radius: 6px;
    padding: 6px 12px;
    padding-right: 30px;
    font-size: 12px;
    color: #2D2640;
    min-width: 140px;
}
QComboBox:focus {
    border-color: #7C5CBF;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    border-left: 1px solid #E8E3F0;
    margin-right: 4px;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #7C5CBF;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E8E3F0;
    border-radius: 4px;
    selection-background-color: #7C5CBF;
    selection-color: white;
}
QComboBox:disabled {
    background-color: #F5F3F8;
    color: #A99BBF;
    border-color: #E8E3F0;
}
QComboBox:disabled::down-arrow {
    border-top-color: #A99BBF;
}

/* ── SpinBox ── */
QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #A99BBF;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
    color: #2D2640;
    min-width: 70px;
}
QSpinBox:focus {
    border-color: #7C5CBF;
}
QSpinBox:disabled {
    background-color: #F5F3F8;
    color: #A99BBF;
    border-color: #E8E3F0;
}

/* ── Slider ── */
QSlider {
    min-height: 28px;
}
QSlider::groove:horizontal {
    background: #E8E3F0;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #7C5CBF;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #9578D3;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #A78BDA, stop:1 #C4B2EC);
    border-radius: 3px;
}
QSlider::groove:horizontal:disabled {
    background: #F5F3F8;
}
QSlider::handle:horizontal:disabled {
    background: #E8E3F0;
}

/* ── Status card frames ── */
QFrame#statusCard {
    background-color: #FFFFFF;
    border: 1px solid #E8E3F0;
    border-radius: 8px;
}

/* ── Log text ── */
QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #E8E3F0;
    border-radius: 6px;
    padding: 6px;
    font-size: 11px;
    color: #2D2640;
    font-family: monospace;
}

/* ── Status bar ── */
QStatusBar {
    background-color: #3B1D6B;
    color: rgba(255,255,255,0.55);
    font-size: 11px;
    padding: 3px 8px;
}

/* ── Message Box ── */
QMessageBox {
    background-color: #F5F3F8;
}
QMessageBox QLabel {
    color: #2D2640;
    font-size: 13px;
    padding: 0px;
    margin: 0px;
}
"""


def _add_shadow(widget: QWidget) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(20)
    shadow.setOffset(0, 4)
    shadow.setColor(QColor(0, 0, 0, 25))
    widget.setGraphicsEffect(shadow)


class ScanWorker(QThread):
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


class MainWindow(QMainWindow):
    back_to_menu = pyqtSignal()

    def __init__(self, mode: str = "single"):
        super().__init__()
        self._mode = mode
        if mode == "soarm101":
            self.setWindowTitle("SO-ARM 101 전체 모터 테스트 — RoboSEasy")
        else:
            self.setWindowTitle("단일 모터 테스트 — RoboSEasy")
        self.setMinimumSize(900, 900)
        self.setStyleSheet(STYLESHEET)

        self._controller = MotorController()
        self._current_motor_id: int | None = None
        self._monitoring = False

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        layout.addWidget(self._build_header())

        # Body with margins
        body = QVBoxLayout()
        body.setSpacing(8)
        body.setContentsMargins(16, 8, 16, 8)

        body.addWidget(self._build_connection_panel())
        body.addWidget(self._build_motor_select_panel())
        body.addWidget(self._build_id_setup_panel())
        body.addWidget(self._build_control_panel())
        body.addWidget(self._build_status_panel())
        body.addWidget(self._build_log_panel())

        layout.addLayout(body)
        layout.addStretch()

        # Status bar
        status_bar = QStatusBar()
        status_bar.showMessage("Motor Test & ID Setup — RoboSEasy")
        self.setStatusBar(status_bar)

        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_status)

        self._set_controls_enabled(False)

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
            logo_pixmap = QPixmap(logo_path).scaledToHeight(
                28, Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label = QLabel("LOGO")
            logo_label.setFixedSize(60, 28)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setStyleSheet(
                "background-color: rgba(255,255,255,0.12); border-radius: 6px; "
                "color: rgba(255,255,255,0.7); font-size: 11px; font-weight: bold;"
            )
        h.addWidget(logo_label)

        sep = QFrame()
        sep.setFixedSize(1, 20)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.2);")
        h.addWidget(sep)

        if self._mode == "soarm101":
            title_text = "SO-ARM 101 전체 모터 테스트"
            subtitle_text = "STS3215 — All Motors"
        else:
            title_text = "단일 모터 테스트"
            subtitle_text = "STS3215 Servo Motor Test & ID Setup"

        title = QLabel(title_text)
        title.setObjectName("headerTitle")
        h.addWidget(title)

        h.addStretch()

        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("headerSubtitle")
        h.addWidget(subtitle)

        h.addStretch()

        back_btn = QPushButton("◀ 뒤로")
        back_btn.setObjectName("refreshBtn")
        back_btn.clicked.connect(self.back_to_menu.emit)
        h.addWidget(back_btn)

        quit_btn = QPushButton("Quit")
        quit_btn.setObjectName("quitBtn")
        quit_btn.clicked.connect(self.close)
        h.addWidget(quit_btn)

        return header

    # ── Connection Panel ──

    def _build_connection_panel(self) -> QGroupBox:
        group = QGroupBox("연결")
        _add_shadow(group)
        h = QHBoxLayout(group)

        h.addWidget(QLabel("포트:"))
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(250)
        h.addWidget(self._port_combo)

        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self._refresh_ports)
        h.addWidget(refresh_btn)

        self._connect_btn = QPushButton("🔌 연결")
        self._connect_btn.setObjectName("connectBtn")
        self._connect_btn.clicked.connect(self._toggle_connection)
        h.addWidget(self._connect_btn)

        self._status_led = QLabel("●")
        self._status_led.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 18px;")
        h.addWidget(self._status_led)

        h.addStretch()
        self._refresh_ports()
        return group

    # ── Motor Select Panel ──

    def _build_motor_select_panel(self) -> QGroupBox:
        group = QGroupBox("모터 선택")
        _add_shadow(group)
        h = QHBoxLayout(group)

        self._scan_btn = QPushButton("🔍 모터 스캔")
        self._scan_btn.clicked.connect(self._scan_motors)
        h.addWidget(self._scan_btn)

        h.addWidget(QLabel("스캔된 모터:"))
        self._motor_combo = QComboBox()
        self._motor_combo.setMinimumWidth(120)
        self._motor_combo.currentTextChanged.connect(self._on_motor_selected)
        h.addWidget(self._motor_combo)

        self._ping_btn = QPushButton("📡 핑 테스트")
        self._ping_btn.clicked.connect(self._ping_motor)
        h.addWidget(self._ping_btn)

        h.addStretch()
        return group

    # ── ID Setup Panel ──

    def _build_id_setup_panel(self) -> QGroupBox:
        group = QGroupBox("모터 ID 설정")
        _add_shadow(group)
        h = QHBoxLayout(group)

        h.addWidget(QLabel("선택된 모터"))
        self._id_current_label = QLabel("--")
        self._id_current_label.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: bold; font-size: 14px;")
        h.addWidget(self._id_current_label)

        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 16px; font-weight: bold;")
        h.addWidget(arrow)

        h.addWidget(QLabel("새 ID:"))
        self._id_new_input = QSpinBox()
        self._id_new_input.setRange(0, 253)
        self._id_new_input.setValue(1)
        h.addWidget(self._id_new_input)

        self._id_change_btn = QPushButton("✏️ ID 변경")
        self._id_change_btn.clicked.connect(self._change_motor_id)
        h.addWidget(self._id_change_btn)

        self._id_save_btn = QPushButton("💾 ID 저장")
        self._id_save_btn.clicked.connect(self._change_and_save_motor_id)
        h.addWidget(self._id_save_btn)

        h.addStretch()
        return group

    # ── Control Panel ──

    def _build_control_panel(self) -> QGroupBox:
        group = QGroupBox("모터 제어")
        _add_shadow(group)
        v = QVBoxLayout(group)

        # Position
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("위치 (0~4095):"))
        self._pos_slider = QSlider(Qt.Orientation.Horizontal)
        self._pos_slider.setRange(0, 4095)
        self._pos_slider.setValue(2048)
        self._pos_slider.valueChanged.connect(self._on_pos_slider_changed)
        row1.addWidget(self._pos_slider)
        self._pos_input = QSpinBox()
        self._pos_input.setRange(0, 4095)
        self._pos_input.setValue(2048)
        self._pos_input.valueChanged.connect(self._on_pos_input_changed)
        row1.addWidget(self._pos_input)
        v.addLayout(row1)

        # Speed
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("속도 (0~3400):"))
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(0, 3400)
        self._speed_slider.setValue(1000)
        self._speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        row2.addWidget(self._speed_slider)
        self._speed_input = QSpinBox()
        self._speed_input.setRange(0, 3400)
        self._speed_input.setValue(1000)
        self._speed_input.valueChanged.connect(self._on_speed_input_changed)
        row2.addWidget(self._speed_input)
        v.addLayout(row2)

        # Buttons
        btn_row = QHBoxLayout()
        self._torque_btn = QPushButton("⚡ 토크 ON")
        self._torque_btn.setCheckable(True)
        self._torque_btn.clicked.connect(self._toggle_torque)
        btn_row.addWidget(self._torque_btn)

        self._move_btn = QPushButton("▶ 이동")
        self._move_btn.clicked.connect(self._move_motor)
        btn_row.addWidget(self._move_btn)
        btn_row.addStretch()
        v.addLayout(btn_row)

        return group

    # ── Status Panel ──

    def _build_status_panel(self) -> QGroupBox:
        group = QGroupBox("상태 모니터")
        _add_shadow(group)
        v = QVBoxLayout(group)

        grid = QHBoxLayout()
        grid.setSpacing(8)
        self._status_labels: dict[str, QLabel] = {}
        for name, unit in [
            ("위치", ""),
            ("속도", ""),
            ("온도", "°C"),
            ("전압", "V"),
            ("전류", "mA"),
            ("부하", "%"),
        ]:
            frame = QFrame()
            frame.setObjectName("statusCard")
            frame.setMinimumWidth(100)
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(8, 8, 8, 8)
            fl.setSpacing(2)

            title = QLabel(name)
            title.setObjectName("statusTitle")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(title)

            val = QLabel("--")
            val.setObjectName("statusValue")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(val)

            if unit:
                unit_label = QLabel(unit)
                unit_label.setObjectName("statusUnit")
                unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fl.addWidget(unit_label)

            self._status_labels[name] = val
            grid.addWidget(frame)
        v.addLayout(grid)

        btn_row = QHBoxLayout()
        self._monitor_btn = QPushButton("📊 모니터링 시작")
        self._monitor_btn.clicked.connect(self._toggle_monitoring)
        btn_row.addWidget(self._monitor_btn)
        btn_row.addStretch()
        v.addLayout(btn_row)

        return group

    # ── Log Panel ──

    def _build_log_panel(self) -> QGroupBox:
        group = QGroupBox("로그")
        _add_shadow(group)
        v = QVBoxLayout(group)
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(120)
        v.addWidget(self._log_text)
        return group

    # ── Helpers ──

    def _log(self, msg: str):
        if hasattr(self, "_log_text"):
            self._log_text.append(msg)

    def _set_controls_enabled(self, enabled: bool):
        for w in [
            self._scan_btn, self._ping_btn, self._move_btn,
            self._torque_btn, self._monitor_btn,
            self._pos_slider, self._pos_input,
            self._speed_slider, self._speed_input,
            self._motor_combo,
            self._id_new_input, self._id_change_btn,
        ]:
            w.setEnabled(enabled)

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

    def _update_id_setup_label(self):
        if self._current_motor_id is not None:
            self._id_current_label.setText(f"ID: {self._current_motor_id}")
        else:
            self._id_current_label.setText("--")

    # ── Slots ──

    def _refresh_ports(self):
        self._port_combo.clear()
        ports = serial.tools.list_ports.comports()
        # 내장 시리얼 포트(ttyS*) 제외, USB 시리얼만 표시
        usb_ports = [p for p in ports if "/dev/ttyS" not in p.device]
        for p in usb_ports:
            self._port_combo.addItem(f"{p.device} - {p.description}", p.device)
        if usb_ports:
            self._port_combo.setCurrentIndex(0)
            self._log(f"USB 시리얼 포트 발견: {len(usb_ports)}개")
        else:
            self._log("USB 시리얼 포트를 찾을 수 없습니다.")

    def _toggle_connection(self):
        if self._controller.connected:
            self._controller.disconnect()
            self._connect_btn.setText("🔌 연결")
            self._status_led.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 18px;")
            self._set_controls_enabled(False)
            self._stop_monitoring()
            self._log("연결 해제됨")
        else:
            port = self._port_combo.currentData()
            if not port:
                self._log("포트를 선택하세요.")
                return
            try:
                self._controller.connect(port)
                self._connect_btn.setText("🔌 연결 해제")
                self._status_led.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 18px;")
                self._set_controls_enabled(True)
                self._log(f"연결 성공: {port}")

                # 내장 시리얼 포트(ttyS*)는 장치 없이도 열리므로 경고
                if "/dev/ttyS" in port:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Warning)
                    msg.setWindowTitle("포트 확인 필요")
                    msg.setText(
                        f"'{port}'는 내장 시리얼 포트입니다.\n\n"
                        "USB 시리얼 어댑터(ttyUSB*, ttyACM*)가 연결되어 있는지 확인하세요.\n"
                        "장치가 없어도 포트가 열릴 수 있습니다."
                    )
                    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg.exec()
            except Exception as e:
                emsg = str(e)
                self._log(f"연결 실패: {emsg}")
                if "PermissionError" in emsg or "액세스" in emsg or "Access" in emsg:
                    self._log(
                        "→ 포트가 점유 중입니다. 수 초 후 재연결을 시도하거나, "
                        "다른 시리얼 프로그램을 닫고 USB를 재연결해보세요."
                    )

    def _scan_motors(self):
        if not self._controller.connected:
            return
        self._scan_btn.setEnabled(False)

        progress = QProgressDialog("모터 스캔 중...", "취소", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        # SO-ARM 101은 ID 1~6만 사용하므로 1~7 범위로 한정 (모터 ID 셋업과 동일)
        self._scan_worker = ScanWorker(self._controller, range(1, 8))
        self._scan_worker.progress.connect(progress.setValue)

        def on_found(ids: list[int]):
            progress.close()
            self._motor_combo.clear()
            for mid in ids:
                self._motor_combo.addItem(f"ID: {mid}", mid)
            self._log(f"스캔 완료: {len(ids)}개 모터 발견 {ids}")
            self._scan_btn.setEnabled(True)
            # 첫 번째 모터 자동 선택
            if ids:
                self._motor_combo.setCurrentIndex(0)

        self._scan_worker.found.connect(on_found)
        self._scan_worker.start()

    def _on_motor_selected(self, text: str):
        idx = self._motor_combo.currentIndex()
        if idx >= 0:
            self._current_motor_id = self._motor_combo.currentData()
            self._update_id_setup_label()
            self._log(f"모터 선택: ID {self._current_motor_id}")

    def _change_motor_id(self):
        # 스캔된 모터가 없으면 경고
        if self._current_motor_id is None:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("모터 미선택")
            msg.setText("모터가 선택되지 않았습니다.\n\n먼저 모터 스캔을 실행하여 모터를 선택하세요.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)

            msg.exec()
            return

        current_id = self._current_motor_id
        new_id = self._id_new_input.value()

        if current_id == new_id:
            self._log("현재 ID와 새 ID가 동일합니다.")
            return

        # 확인 다이얼로그
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("ID 변경")
        msg.setText(f"모터 ID를 변경하시겠습니까?\n현재 ID: {current_id} → 새 ID: {new_id}\nID 변경 후, 모터 재스캔이 필요합니다. \t\n\n")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        if msg.exec() != QMessageBox.StandardButton.Yes:
            return

        try:
            self._controller.change_id(current_id, new_id)
            self._log(f"ID 변경 성공: {current_id} → {new_id}")
            self._current_motor_id = new_id
            self._update_id_setup_label()
            # 모터 콤보 갱신 권장
            self._log("모터 재스캔을 권장합니다.")
        except Exception as e:
            self._log(f"ID 변경 실패: {e}")

    def _change_and_save_motor_id(self):
        """ID 변경 후 자동으로 모터 콤보박스를 갱신하여 새 ID로 셋업"""
        if self._current_motor_id is None:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("모터 미선택")
            msg.setText("모터가 선택되지 않았습니다.\n\n먼저 모터 스캔을 실행하여 모터를 선택하세요.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return

        current_id = self._current_motor_id
        new_id = self._id_new_input.value()

        if current_id == new_id:
            self._log("현재 ID와 새 ID가 동일합니다.")
            return

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("ID 변경 및 저장")
        msg.setText(f"모터 ID를 변경하고 저장하시겠습니까?\n현재 ID: {current_id} → 새 ID: {new_id}\n\n변경 후 자동으로 모터를 재셋업합니다.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        if msg.exec() != QMessageBox.StandardButton.Yes:
            return

        try:
            self._controller.change_id(current_id, new_id)
            self._log(f"ID 변경 성공: {current_id} → {new_id}")

            # 콤보박스에서 기존 ID를 새 ID로 교체
            for i in range(self._motor_combo.count()):
                if self._motor_combo.itemData(i) == current_id:
                    self._motor_combo.setItemText(i, f"ID: {new_id}")
                    self._motor_combo.setItemData(i, new_id)
                    break

            self._current_motor_id = new_id
            self._update_id_setup_label()
            self._log(f"모터 ID {new_id}번으로 저장 및 셋업 완료.")
        except Exception as e:
            self._log(f"ID 변경 실패: {e}")

    def _ping_motor(self):
        if self._current_motor_id is None:
            self._log("모터를 먼저 선택하세요.")
            return
        mid = self._current_motor_id
        try:
            result = self._controller.ping(mid)
            self._log(f"핑 ID {mid}: {'응답 있음 ✓' if result else '응답 없음 ✗'}")
        except Exception as e:
            self._log(f"핑 실패: {e}")

    # Slider <-> Input sync
    def _on_pos_slider_changed(self, val):
        self._pos_input.blockSignals(True)
        self._pos_input.setValue(val)
        self._pos_input.blockSignals(False)

    def _on_pos_input_changed(self, val):
        self._pos_slider.blockSignals(True)
        self._pos_slider.setValue(val)
        self._pos_slider.blockSignals(False)

    def _on_speed_slider_changed(self, val):
        self._speed_input.blockSignals(True)
        self._speed_input.setValue(val)
        self._speed_input.blockSignals(False)

    def _on_speed_input_changed(self, val):
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(val)
        self._speed_slider.blockSignals(False)

    def _move_motor(self):
        if self._current_motor_id is None:
            self._log("모터를 먼저 선택하세요.")
            return
        pos = self._pos_input.value()
        speed = self._speed_input.value()
        try:
            self._controller.move_to(self._current_motor_id, pos, speed)
            self._log(f"ID {self._current_motor_id} → 위치 {pos} (속도={speed})")
        except Exception as e:
            self._log(f"이동 실패: {e}")

    def _toggle_torque(self):
        if self._current_motor_id is None:
            return
        enable = self._torque_btn.isChecked()
        try:
            self._controller.set_torque(self._current_motor_id, enable)
            self._torque_btn.setText("⚡ 토크 OFF" if enable else "⚡ 토크 ON")
            self._log(f"ID {self._current_motor_id} 토크 {'ON' if enable else 'OFF'}")
        except Exception as e:
            self._log(f"토크 설정 실패: {e}")
            self._torque_btn.setChecked(not enable)

    def _toggle_monitoring(self):
        if self._monitoring:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        if self._current_motor_id is None:
            self._log("모터를 먼저 선택하세요.")
            return
        self._monitoring = True
        self._monitor_btn.setText("📊 모니터링 중지")
        self._poll_timer.start(200)
        self._log("모니터링 시작")

    def _stop_monitoring(self):
        self._monitoring = False
        self._monitor_btn.setText("📊 모니터링 시작")
        self._poll_timer.stop()
        self._log("모니터링 중지")

    def _poll_status(self):
        if self._current_motor_id is None:
            return
        try:
            status = self._controller.read_status(self._current_motor_id)
            self._update_status_display(status)
        except Exception:
            pass

    def closeEvent(self, event):
        self._poll_timer.stop()
        if self._controller.connected:
            self._controller.disconnect()
        event.accept()

