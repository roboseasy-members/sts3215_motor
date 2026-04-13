"""
PyQt5 스타일시트 정의
다크 테마 + 반투명 카드 스타일
"""

MAIN_STYLE = """
QMainWindow {
    background-color: #2C2C2C;
}

QWidget {
    color: #FFFFFF;
    font-family: 'Segoe UI', Arial;
    font-size: 11pt;
}

/* 상단 제어 패널 */
#controlPanel {
    background-color: #1E1E1E;
    border-bottom: 2px solid #404040;
    padding: 10px;
}

/* 콤보박스 (포트 선택) */
QComboBox {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    border-radius: 5px;
    padding: 5px 10px;
    min-width: 120px;
    color: #FFFFFF;
}

QComboBox:hover {
    border: 1px solid #2196F3;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #FFFFFF;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    selection-background-color: #2196F3;
    color: #FFFFFF;
}

/* 버튼 공통 */
QPushButton {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    border-radius: 5px;
    padding: 8px 15px;
    color: #FFFFFF;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #4C4C4C;
    border: 1px solid #2196F3;
}

QPushButton:pressed {
    background-color: #2C2C2C;
}

QPushButton:disabled {
    background-color: #2C2C2C;
    color: #666666;
    border: 1px solid #3C3C3C;
}

/* 연결 버튼 */
#connectButton {
    background-color: #2196F3;
    border: none;
    min-width: 100px;
}

#connectButton:hover {
    background-color: #1976D2;
}

#connectButton:pressed {
    background-color: #0D47A1;
}

/* 긴급 정지 버튼 */
#emergencyStopButton {
    background-color: #F44336;
    border: none;
    font-size: 14pt;
    font-weight: bold;
    min-width: 150px;
    min-height: 50px;
}

#emergencyStopButton:hover {
    background-color: #D32F2F;
}

#emergencyStopButton:pressed {
    background-color: #B71C1C;
}

/* 새로고침 버튼 */
#refreshButton {
    min-width: 40px;
    max-width: 40px;
    padding: 8px;
}

/* 상태 인디케이터 */
#statusIndicator {
    border-radius: 10px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
}

.status-disconnected {
    background-color: #9E9E9E;
}

.status-connected {
    background-color: #4CAF50;
}

.status-error {
    background-color: #F44336;
}

/* 상태 텍스트 */
#statusLabel {
    font-size: 12pt;
    font-weight: bold;
    margin-left: 10px;
}

/* 스크롤 영역 */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #2C2C2C;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 모터 카드 */
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

/* 추가 버튼 카드 */
.addMotorCard {
    background-color: rgba(255, 255, 255, 0.05);
    border: 2px dashed rgba(255, 255, 255, 0.3);
    border-radius: 15px;
}

.addMotorCard:hover {
    background-color: rgba(255, 255, 255, 0.1);
    border: 2px dashed rgba(33, 150, 243, 0.7);
}

/* 모터 제목 */
.motorTitle {
    font-size: 14pt;
    font-weight: bold;
    color: #2196F3;
}

/* 현재값 라벨 */
.currentValueLabel {
    font-size: 24pt;
    font-family: 'Consolas', 'Courier New', monospace;
    font-weight: bold;
    color: #4CAF50;
}

/* 목표값 입력 */
QLineEdit {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    border-radius: 5px;
    padding: 5px 10px;
    color: #FFFFFF;
    font-size: 12pt;
    font-family: 'Consolas', 'Courier New', monospace;
}

QLineEdit:focus {
    border: 2px solid #2196F3;
}

QLineEdit:disabled {
    background-color: #2C2C2C;
    color: #666666;
}

/* 작은 버튼 (위/아래 화살표) */
.smallButton {
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    font-size: 16pt;
    font-weight: bold;
    padding: 0px;
}

/* 이동 버튼 */
.moveButton {
    background-color: #4CAF50;
    border: none;
    min-height: 40px;
}

.moveButton:hover {
    background-color: #45A049;
}

.moveButton:pressed {
    background-color: #388E3C;
}

/* 삭제 버튼 */
.deleteButton {
    background-color: #F44336;
    border: none;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    border-radius: 15px;
    font-size: 12pt;
    font-weight: bold;
}

.deleteButton:hover {
    background-color: #D32F2F;
}

/* 라벨 */
QLabel {
    color: #FFFFFF;
}

.sectionLabel {
    color: #9E9E9E;
    font-size: 10pt;
}
"""
