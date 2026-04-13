"""
상단 제어 패널
- COM 포트 선택
- 연결/해제 버튼
- 연결 상태 표시
- 긴급 정지 버튼
"""
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                              QComboBox, QPushButton, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from utils import get_available_ports


class ControlPanel(QWidget):
    """상단 제어 패널 위젯"""
    
    # 시그널 정의
    connect_requested = pyqtSignal(str)  # 연결 요청 (포트 이름)
    disconnect_requested = pyqtSignal()  # 연결 해제 요청
    emergency_stop_requested = pyqtSignal()  # 긴급 정지 요청
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setObjectName("controlPanel")
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(20)
        
        # === 왼쪽: 포트 선택 영역 ===
        port_layout = QHBoxLayout()
        
        # 포트 라벨
        port_label = QLabel("포트:")
        port_label.setStyleSheet("font-weight: bold;")
        port_layout.addWidget(port_label)
        
        # 포트 콤보박스
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        
        # 새로고침 버튼
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.setToolTip("포트 목록 새로고침")
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(port_layout)
        
        # 구분선
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setStyleSheet("color: #555555;")
        main_layout.addWidget(separator1)
        
        # === 중앙: 연결 버튼 및 상태 ===
        connection_layout = QHBoxLayout()
        
        # 연결 버튼
        self.connect_button = QPushButton("연결")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_button)
        
        # 상태 인디케이터
        self.status_indicator = QLabel()
        self.status_indicator.setObjectName("statusIndicator")
        self.status_indicator.setProperty("class", "status-disconnected")
        self.status_indicator.setStyleSheet(
            "background-color: #9E9E9E; border-radius: 10px; "
            "min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;"
        )
        connection_layout.addWidget(self.status_indicator)
        
        # 상태 텍스트
        self.status_label = QLabel("연결 안 됨")
        self.status_label.setObjectName("statusLabel")
        connection_layout.addWidget(self.status_label)
        
        main_layout.addLayout(connection_layout)
        
        # 스페이서
        main_layout.addStretch()
        
        # 구분선
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setStyleSheet("color: #555555;")
        main_layout.addWidget(separator2)
        
        # === 오른쪽: 긴급 정지 버튼 ===
        self.emergency_button = QPushButton("⛔ 긴급 정지")
        self.emergency_button.setObjectName("emergencyStopButton")
        self.emergency_button.setEnabled(False)
        self.emergency_button.clicked.connect(self.emergency_stop)
        main_layout.addWidget(self.emergency_button)
        
    def refresh_ports(self):
        """포트 목록 새로고침"""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        
        ports = get_available_ports()
        if ports:
            self.port_combo.addItems(ports)
            # 이전 선택 복원
            if current_port in ports:
                self.port_combo.setCurrentText(current_port)
        else:
            self.port_combo.addItem("포트 없음")
            self.port_combo.setEnabled(False)
            return
            
        self.port_combo.setEnabled(True)
        
    def toggle_connection(self):
        """연결/해제 토글"""
        if not self.is_connected:
            # 연결 시도
            port = self.port_combo.currentText()
            if port and port != "포트 없음":
                self.connect_requested.emit(port)
        else:
            # 연결 해제
            self.disconnect_requested.emit()
            
    def set_connected(self, connected: bool):
        """연결 상태 설정"""
        self.is_connected = connected
        
        if connected:
            # 연결됨
            self.connect_button.setText("연결 해제")
            self.status_indicator.setStyleSheet(
                "background-color: #4CAF50; border-radius: 10px; "
                "min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;"
            )
            self.status_label.setText("연결됨")
            self.port_combo.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.emergency_button.setEnabled(True)
        else:
            # 연결 안 됨
            self.connect_button.setText("연결")
            self.status_indicator.setStyleSheet(
                "background-color: #9E9E9E; border-radius: 10px; "
                "min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;"
            )
            self.status_label.setText("연결 안 됨")
            self.port_combo.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.emergency_button.setEnabled(False)
            
    def set_error(self, error_msg: str):
        """에러 상태 표시"""
        self.status_indicator.setStyleSheet(
            "background-color: #F44336; border-radius: 10px; "
            "min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;"
        )
        self.status_label.setText(f"에러: {error_msg}")
        
    def emergency_stop(self):
        """긴급 정지 버튼 클릭"""
        self.emergency_stop_requested.emit()
