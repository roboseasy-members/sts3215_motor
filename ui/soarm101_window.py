"""
SO-ARM 101 전체 모터 테스트 창
CheckFeetechMotors/CheckMotor_GUI.py 를 MotorController(st3215) + new-motor-check-gui 디자인으로 재구현
"""
import os
import serial.tools.list_ports

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from motor_controller import MotorController

# ── Design System (main_window.py 와 동일) ──
COLOR_HEADER   = "#3B1D6B"
COLOR_TEXT     = "#2D2640"
COLOR_ACCENT   = "#7C5CBF"
COLOR_ACCENT_H = "#9578D3"
COLOR_MUTED    = "#A99BBF"
COLOR_BG       = "#F5F3F8"
COLOR_CARD     = "#FFFFFF"
COLOR_BORDER   = "#E8E3F0"
COLOR_SUCCESS  = "#5BAD7A"
COLOR_DANGER   = "#E04848"

MAX_POS = 4095

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
QPushButton#quitBtn { background-color: #E04848; }
QPushButton#quitBtn:hover { background-color: #C53030; }

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #A99BBF;
    border-radius: 6px;
    padding: 6px 12px;
    padding-right: 30px;
    font-size: 12px;
    color: #2D2640;
    min-width: 200px;
}
QComboBox:focus { border-color: #7C5CBF; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    border-left: 1px solid #E8E3F0;
    margin-right: 4px;
}
QComboBox::down-arrow {
    width: 0; height: 0;
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

QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #A99BBF;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    color: #2D2640;
}
QLineEdit:focus { border-color: #7C5CBF; }

QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #A99BBF;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
    color: #2D2640;
    min-width: 90px;
}
QSpinBox:focus { border-color: #7C5CBF; }

QSlider { min-height: 28px; }
QSlider::groove:horizontal {
    background: #E8E3F0;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #7C5CBF;
    width: 16px; height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover { background: #9578D3; }
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #A78BDA,stop:1 #C4B2EC);
    border-radius: 3px;
}

QStatusBar {
    background-color: #3B1D6B;
    color: rgba(255,255,255,0.55);
    font-size: 11px;
    padding: 3px 8px;
}

QCheckBox { color: #2D2640; font-size: 12px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #A99BBF;
    border-radius: 4px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #7C5CBF;
    border-color: #7C5CBF;
}
"""


def _shadow(widget: QWidget) -> None:
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(20)
    fx.setOffset(0, 4)
    fx.setColor(QColor(0, 0, 0, 25))
    widget.setGraphicsEffect(fx)


class SoArm101Window(QMainWindow):
    back_to_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._controller = MotorController()
        self._motors_data: dict[int, dict] = {}
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_motor_values)

        self.collision_detection_enabled = True
        self.load_threshold = 1300
        self.current_threshold = 800
        self._collision_detected: dict[int, bool] = {}

        self.setWindowTitle("SO-ARM 101 전체 모터 테스트 — RoboSEasy")
        self.setMinimumSize(1100, 900)
        self.resize(1200, 1000)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_header())

        body = QVBoxLayout()
        body.setSpacing(10)
        body.setContentsMargins(16, 10, 16, 10)
        body.addWidget(self._build_input_panel())
        body.addWidget(self._build_collision_panel())

        self._monitoring_group = QGroupBox("모니터링 및 제어")
        _shadow(self._monitoring_group)
        self._monitoring_layout = QVBoxLayout(self._monitoring_group)
        self._monitoring_layout.setSpacing(12)
        self._monitoring_layout.setContentsMargins(8, 8, 8, 8)
        self._monitoring_group.setEnabled(False)
        body.addWidget(self._monitoring_group)

        body.addStretch()
        root.addLayout(body)

        status_bar = QStatusBar()
        status_bar.showMessage("SO-ARM 101 전체 모터 테스트 — RoboSEasy")
        self.setStatusBar(status_bar)

    # ── 헤더 ──

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
            logo = QLabel()
            logo.setPixmap(QPixmap(logo_path).scaledToHeight(28, Qt.TransformationMode.SmoothTransformation))
        else:
            logo = QLabel("LOGO")
            logo.setFixedSize(60, 28)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo.setStyleSheet(
                "background-color: rgba(255,255,255,0.12); border-radius: 6px;"
                "color: rgba(255,255,255,0.7); font-size: 11px; font-weight: bold;"
            )
        h.addWidget(logo)

        sep = QFrame()
        sep.setFixedSize(1, 20)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.2);")
        h.addWidget(sep)

        title = QLabel("SO-ARM 101 전체 모터 테스트")
        title.setObjectName("headerTitle")
        h.addWidget(title)

        h.addStretch()

        subtitle = QLabel("STS3215 Servo Motor — All Motors")
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

    # ── 입력 패널 ──

    def _build_input_panel(self) -> QGroupBox:
        group = QGroupBox("연결 설정")
        _shadow(group)
        h = QHBoxLayout(group)
        h.setSpacing(12)

        h.addWidget(QLabel("포트:"))
        self._port_combo = QComboBox()
        h.addWidget(self._port_combo)

        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self._refresh_ports)
        h.addWidget(refresh_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E8E3F0;")
        h.addWidget(sep)

        h.addWidget(QLabel("ID 목록:"))
        self._id_list_input = QLineEdit("1,2,3,4,5,6")
        self._id_list_input.setFixedWidth(160)
        h.addWidget(self._id_list_input)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #E8E3F0;")
        h.addWidget(sep2)

        self._apply_btn = QPushButton("🔌 연결")
        self._apply_btn.clicked.connect(self._apply_settings)
        h.addWidget(self._apply_btn)

        self._status_led = QLabel("●")
        self._status_led.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 18px;")
        h.addWidget(self._status_led)

        h.addStretch()
        self._refresh_ports()
        return group

    def _refresh_ports(self):
        current = self._port_combo.currentData()
        self._port_combo.clear()
        ports = [p for p in serial.tools.list_ports.comports() if "/dev/ttyS" not in p.device]
        if ports:
            for p in ports:
                self._port_combo.addItem(f"{p.device} — {p.description}", p.device)
            for i in range(self._port_combo.count()):
                if self._port_combo.itemData(i) == current:
                    self._port_combo.setCurrentIndex(i)
                    break
        else:
            self._port_combo.addItem("포트 없음", None)

    # ── 충돌 감지 패널 ──

    def _build_collision_panel(self) -> QGroupBox:
        group = QGroupBox("충돌 감지 설정")
        _shadow(group)
        h = QHBoxLayout(group)
        h.setSpacing(20)

        self._collision_checkbox = QCheckBox("충돌 감지 활성화")
        self._collision_checkbox.setChecked(True)
        self._collision_checkbox.stateChanged.connect(
            lambda s: setattr(self, "collision_detection_enabled", s == Qt.CheckState.Checked.value)
        )
        h.addWidget(self._collision_checkbox)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #E8E3F0;")
        h.addWidget(sep)

        h.addWidget(QLabel("부하 임계값:"))
        self._load_spinbox = QSpinBox()
        self._load_spinbox.setRange(100, 1300)
        self._load_spinbox.setValue(self.load_threshold)
        self._load_spinbox.setSuffix(" / 1300")
        self._load_spinbox.valueChanged.connect(lambda v: setattr(self, "load_threshold", v))
        h.addWidget(self._load_spinbox)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #E8E3F0;")
        h.addWidget(sep2)

        h.addWidget(QLabel("전류 임계값:"))
        self._current_spinbox = QSpinBox()
        self._current_spinbox.setRange(100, 2000)
        self._current_spinbox.setValue(self.current_threshold)
        self._current_spinbox.setSuffix(" mA")
        self._current_spinbox.valueChanged.connect(lambda v: setattr(self, "current_threshold", v))
        h.addWidget(self._current_spinbox)

        h.addStretch()

        info = QLabel("💡 임계값 초과 시 해당 모터 토크가 자동으로 꺼집니다.")
        info.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11px;")
        h.addWidget(info)

        return group

    # ── 연결 / 적용 ──

    def _apply_settings(self):
        try:
            if self._controller.connected:
                self._timer.stop()
                self._controller.disconnect()

            port = self._port_combo.currentData()
            if not port:
                QMessageBox.warning(self, "포트 없음", "연결할 포트를 선택하세요.")
                return

            id_str = self._id_list_input.text().strip()
            try:
                id_list = [int(x.strip()) for x in id_str.split(",") if x.strip()]
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "ID 목록은 숫자를 쉼표로 구분해야 합니다.\n예: 1,2,3,4,5,6")
                return
            if not id_list:
                QMessageBox.warning(self, "입력 오류", "최소 1개 이상의 모터 ID를 입력하세요.")
                return

            self._controller.connect(port)

            self._motors_data.clear()
            self._collision_detected.clear()
            self._clear_monitoring()

            for mid in id_list:
                self._monitoring_layout.addWidget(self._create_motor_widget(mid))

            self._status_led.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 18px;")
            self._apply_btn.setText("🔌 연결 해제")
            self._monitoring_group.setEnabled(True)
            self.statusBar().showMessage(f"연결됨: {port}  |  모터 {len(id_list)}개")
            self._timer.start(100)

        except Exception as e:
            QMessageBox.critical(self, "연결 오류", f"모터 연결 실패:\n{e}")
            self._status_led.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 18px;")
            self.statusBar().showMessage("연결 실패")

    # ── 모터 카드 위젯 ──

    def _create_motor_widget(self, motor_id: int) -> QGroupBox:
        card = QGroupBox(f"모터 ID {motor_id}")
        card.setMinimumHeight(110)
        _shadow(card)
        layout = QVBoxLayout(card)
        layout.setSpacing(14)
        layout.setContentsMargins(14, 20, 14, 16)

        # 상태 행
        status_row = QHBoxLayout()

        value_label = QLabel("현재 값: ----")
        value_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 13px; font-weight: bold;")
        status_row.addWidget(value_label)

        load_label = QLabel("부하: ---")
        load_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 12px;")
        status_row.addWidget(load_label)

        current_label = QLabel("전류: ---")
        current_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 12px;")
        status_row.addWidget(current_label)

        collision_warning = QLabel("")
        collision_warning.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_row.addWidget(collision_warning)

        status_row.addStretch()
        layout.addLayout(status_row)

        # 슬라이더 행
        slider_row = QHBoxLayout()
        slider_row.setSpacing(8)

        min_lbl = QLabel("0")
        min_lbl.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11px;")
        slider_row.addWidget(min_lbl)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(MAX_POS)
        slider.setValue(0)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(MAX_POS // 10)
        slider.valueChanged.connect(lambda val, mid=motor_id: self._on_slider_changed(mid, val))
        slider_row.addWidget(slider)

        max_lbl = QLabel(str(MAX_POS))
        max_lbl.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11px;")
        slider_row.addWidget(max_lbl)

        slider_value_label = QLabel("목표: 0")
        slider_value_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 600; min-width: 70px;")
        slider_row.addWidget(slider_value_label)

        layout.addLayout(slider_row)

        self._motors_data[motor_id] = {
            "value_label": value_label,
            "load_label": load_label,
            "current_label": current_label,
            "collision_warning": collision_warning,
            "slider": slider,
            "slider_value_label": slider_value_label,
            "card": card,
        }
        self._collision_detected[motor_id] = False

        return card

    # ── 슬라이더 ──

    def _on_slider_changed(self, motor_id: int, value: int):
        try:
            if self._collision_detected.get(motor_id, False):
                self._collision_detected[motor_id] = False
                d = self._motors_data[motor_id]
                d["collision_warning"].setText("")
                d["card"].setStyleSheet("")
            self._controller.set_torque(motor_id, True)
            self._controller.move_to(motor_id, value)
            if motor_id in self._motors_data:
                self._motors_data[motor_id]["slider_value_label"].setText(f"목표: {value}")
        except Exception as e:
            print(f"모터 {motor_id} 제어 오류: {e}")

    # ── 실시간 업데이트 ──

    def _update_motor_values(self):
        if not self._controller.connected:
            return

        for motor_id, data in self._motors_data.items():
            try:
                status = self._controller.read_status(motor_id)

                data["value_label"].setText(f"현재 값: {status.position}")

                load_int = int(abs(status.load)) if status.load is not None else 0
                data["load_label"].setText(f"부하: {load_int}")
                if load_int > self.load_threshold:
                    data["load_label"].setStyleSheet("color: #E04848; font-weight: bold; font-size: 12px;")
                elif load_int > self.load_threshold * 0.7:
                    data["load_label"].setStyleSheet("color: #D97706; font-weight: bold; font-size: 12px;")
                else:
                    data["load_label"].setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px;")

                current_int = int(abs(status.current)) if status.current is not None else 0
                data["current_label"].setText(f"전류: {current_int} mA")
                if current_int > self.current_threshold:
                    data["current_label"].setStyleSheet("color: #E04848; font-weight: bold; font-size: 12px;")
                elif current_int > self.current_threshold * 0.7:
                    data["current_label"].setStyleSheet("color: #D97706; font-weight: bold; font-size: 12px;")
                else:
                    data["current_label"].setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px;")

                if self.collision_detection_enabled:
                    over = load_int > self.load_threshold or current_int > self.current_threshold
                    if over and not self._collision_detected.get(motor_id, False):
                        self._collision_detected[motor_id] = True
                        self._handle_collision(motor_id, load_int, current_int)
                        data["collision_warning"].setText("⚠️ 충돌 감지!")
                        data["collision_warning"].setStyleSheet("color: #E04848; font-weight: bold;")
                        data["card"].setStyleSheet("QGroupBox { border: 2px solid #E04848; }")
                    elif not over and self._collision_detected.get(motor_id, False):
                        self._collision_detected[motor_id] = False
                        data["collision_warning"].setText("")
                        data["card"].setStyleSheet("")

                slider = data["slider"]
                if not slider.isSliderDown():
                    slider.blockSignals(True)
                    slider.setValue(status.position)
                    data["slider_value_label"].setText(f"목표: {status.position}")
                    slider.blockSignals(False)

            except Exception as e:
                data["value_label"].setText("현재 값: 오류")
                print(f"모터 {motor_id} 읽기 오류: {e}")

    def _handle_collision(self, motor_id: int, load: int, current: int):
        try:
            self._controller.set_torque(motor_id, False)
            print(f"⚠️ 모터 {motor_id} 충돌 감지! 부하: {load}, 전류: {current} mA — 토크 OFF")
        except Exception as e:
            print(f"모터 {motor_id} 충돌 처리 오류: {e}")

    def _clear_monitoring(self):
        while self._monitoring_layout.count():
            item = self._monitoring_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def closeEvent(self, event):
        self._timer.stop()
        if self._controller.connected:
            for mid in list(self._motors_data.keys()):
                try:
                    self._controller.set_torque(mid, False)
                except Exception:
                    pass
            self._controller.disconnect()
        event.accept()
