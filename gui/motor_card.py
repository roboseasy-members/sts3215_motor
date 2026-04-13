"""
모터 카드 위젯
- 모터 아이콘
- 현재 위치 표시
- 목표 위치 입력
- 위/아래 버튼
- 이동 버튼
- 삭제 버튼
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator


class MotorCard(QWidget):
    """개별 모터 제어 카드"""
    
    # 시그널
    move_requested = pyqtSignal(int, int)  # (motor_id, target_position)
    delete_requested = pyqtSignal(int)  # (motor_id)
    
    def __init__(self, motor_id: int, parent=None):
        super().__init__(parent)
        self.motor_id = motor_id
        self.current_position = 0
        self.max_position = 4095
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        # 카드 스타일
        self.setProperty("class", "motorCard")
        self.setStyleSheet("""
            .motorCard {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 15px;
            }
            .motorCard:hover {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(33, 150, 243, 0.5);
            }
        """)
        self.setFixedSize(280, 380)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # === 헤더: 제목 + 삭제 버튼 ===
        header_layout = QHBoxLayout()
        
        # 모터 제목
        title_label = QLabel(f"🔧 모터 ID {self.motor_id}")
        title_label.setProperty("class", "motorTitle")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2196F3;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 삭제 버튼
        delete_button = QPushButton("✕")
        delete_button.setProperty("class", "deleteButton")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                border: none;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
                border-radius: 15px;
                font-size: 14pt;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_button.setToolTip("모터 삭제")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.motor_id))
        header_layout.addWidget(delete_button)
        
        main_layout.addLayout(header_layout)
        
        # 구분선
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        main_layout.addWidget(line1)
        
        # === 모터 아이콘 (간단한 텍스트 아이콘) ===
        icon_label = QLabel("⚙️")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48pt;")
        main_layout.addWidget(icon_label)
        
        # === 현재 위치 섹션 ===
        current_label = QLabel("현재 위치")
        current_label.setProperty("class", "sectionLabel")
        current_label.setStyleSheet("color: #9E9E9E; font-size: 10pt;")
        current_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(current_label)
        
        self.current_value_label = QLabel("----")
        self.current_value_label.setProperty("class", "currentValueLabel")
        self.current_value_label.setStyleSheet("""
            font-size: 32pt;
            font-family: 'Consolas', 'Courier New', monospace;
            font-weight: bold;
            color: #4CAF50;
        """)
        self.current_value_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.current_value_label)
        
        # 구분선
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        main_layout.addWidget(line2)
        
        # === 목표 위치 섹션 ===
        target_label = QLabel("목표 위치")
        target_label.setProperty("class", "sectionLabel")
        target_label.setStyleSheet("color: #9E9E9E; font-size: 10pt;")
        target_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(target_label)
        
        # 목표값 입력 + 위/아래 버튼
        target_layout = QHBoxLayout()
        target_layout.setSpacing(5)
        
        # 아래 버튼 (-)
        down_button = QPushButton("▼")
        down_button.setProperty("class", "smallButton")
        down_button.setStyleSheet("""
            QPushButton {
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                font-size: 16pt;
                font-weight: bold;
                background-color: #3C3C3C;
                border: 1px solid #555555;
                border-radius: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
                border: 1px solid #2196F3;
            }
        """)
        down_button.setToolTip("-10")
        down_button.clicked.connect(lambda: self.adjust_target(-10))
        target_layout.addWidget(down_button)
        
        # 입력 필드
        self.target_input = QLineEdit("2048")
        self.target_input.setAlignment(Qt.AlignCenter)
        self.target_input.setValidator(QIntValidator(0, 4095))
        self.target_input.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C3C;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px 10px;
                color: #FFFFFF;
                font-size: 16pt;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        target_layout.addWidget(self.target_input, 1)
        
        # 위 버튼 (+)
        up_button = QPushButton("▲")
        up_button.setProperty("class", "smallButton")
        up_button.setStyleSheet("""
            QPushButton {
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                font-size: 16pt;
                font-weight: bold;
                background-color: #3C3C3C;
                border: 1px solid #555555;
                border-radius: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
                border: 1px solid #2196F3;
            }
        """)
        up_button.setToolTip("+10")
        up_button.clicked.connect(lambda: self.adjust_target(10))
        target_layout.addWidget(up_button)
        
        main_layout.addLayout(target_layout)
        
        # === 이동 버튼 ===
        move_button = QPushButton("이동 ➜")
        move_button.setProperty("class", "moveButton")
        move_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                min-height: 45px;
                font-size: 13pt;
                font-weight: bold;
                border-radius: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        move_button.clicked.connect(self.send_move_command)
        main_layout.addWidget(move_button)
        
        main_layout.addStretch()
        
    def adjust_target(self, delta: int):
        """목표값 조정"""
        try:
            current = int(self.target_input.text() or "0")
            new_value = max(0, min(current + delta, self.max_position))
            self.target_input.setText(str(new_value))
        except ValueError:
            self.target_input.setText("0")
            
    def send_move_command(self):
        """이동 명령 전송"""
        try:
            target = int(self.target_input.text())
            target = max(0, min(target, self.max_position))
            self.move_requested.emit(self.motor_id, target)
        except ValueError:
            pass
            
    def update_current_position(self, position: int):
        """현재 위치 업데이트"""
        self.current_position = position
        self.current_value_label.setText(str(position))
        
    def set_error(self):
        """에러 상태 표시"""
        self.current_value_label.setText("에러")
        self.current_value_label.setStyleSheet("""
            font-size: 24pt;
            font-family: 'Consolas', 'Courier New', monospace;
            font-weight: bold;
            color: #F44336;
        """)


class AddMotorCard(QWidget):
    """모터 추가 카드"""
    
    add_motor_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        # 카드 스타일
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 15px;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px dashed rgba(33, 150, 243, 0.7);
            }
        """)
        self.setFixedSize(280, 380)
        self.setCursor(Qt.PointingHandCursor)
        
        # 레이아웃
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # + 아이콘
        icon_label = QLabel("+")
        icon_label.setStyleSheet("""
            font-size: 72pt;
            color: rgba(255, 255, 255, 0.5);
            font-weight: bold;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # 텍스트
        text_label = QLabel("모터 추가")
        text_label.setStyleSheet("""
            font-size: 14pt;
            color: rgba(255, 255, 255, 0.7);
        """)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
    def mousePressEvent(self, event):
        """클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.add_motor_clicked.emit()
