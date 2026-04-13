"""
메인 윈도우
- 상단 제어 패널
- 모터 카드 그리드
- 모터 컨트롤러 연동
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QScrollArea, QMessageBox, QInputDialog, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from gui.control_panel import ControlPanel
from gui.motor_card import MotorCard, AddMotorCard
from gui.styles import MAIN_STYLE
from motor import MotorController, MotorMonitorThread


class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.motor_cards = {}  # {motor_id: MotorCard}
        self.motor_controller = MotorController()
        self.monitor_thread = None  # 모터 모니터링 스레드
        self.init_ui()
        self.setup_signals()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Feetech 모터 제어")
        self.setMinimumSize(1000, 700)
        
        # 스타일 적용
        self.setStyleSheet(MAIN_STYLE)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === 상단 제어 패널 ===
        self.control_panel = ControlPanel()
        self.control_panel.connect_requested.connect(self.on_connect_requested)
        self.control_panel.disconnect_requested.connect(self.on_disconnect_requested)
        self.control_panel.emergency_stop_requested.connect(self.on_emergency_stop)
        main_layout.addWidget(self.control_panel)
        
        # === 스크롤 영역 (모터 카드들) ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # 스크롤 컨텐츠 위젯
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        
        # 그리드 레이아웃 (모터 카드들)
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # 모터 추가 카드
        self.add_card = AddMotorCard()
        self.add_card.add_motor_clicked.connect(self.on_add_motor)
        self.grid_layout.addWidget(self.add_card, 0, 0)
        
        main_layout.addWidget(scroll_area)
        
        # 상태바
        self.statusBar().showMessage("준비")
    
    def setup_signals(self):
        """모터 컨트롤러 신호 연결"""
        self.motor_controller.connected.connect(self.on_motor_connected)
        self.motor_controller.disconnected.connect(self.on_motor_disconnected)
        self.motor_controller.error_occurred.connect(self.on_motor_error)
        
    def on_connect_requested(self, port: str):
        """연결 요청 처리"""
        try:
            self.statusBar().showMessage(f"{port}에 연결 중...")
            
            # 모터 버스에 연결
            success = self.motor_controller.connect(port)
            
            if success:
                self.control_panel.set_connected(True)
                self.statusBar().showMessage(f"{port}에 연결됨")
                
                # 모니터링 스레드 시작
                if self.monitor_thread is None:
                    self.monitor_thread = MotorMonitorThread(
                        self.motor_controller,
                        self.motor_controller.motor_ids,
                        update_interval=0.1
                    )
                    self.monitor_thread.position_updated.connect(self.on_position_updated)
                    self.monitor_thread.error_occurred.connect(self.on_motor_error)
                    self.monitor_thread.start()
                
                QMessageBox.information(self, "연결 성공", 
                                      f"{port}에 성공적으로 연결되었습니다.\n"
                                      "모터를 추가하여 제어를 시작하세요.")
            else:
                self.control_panel.set_error("연결 실패")
                self.statusBar().showMessage("연결 실패")
            
        except Exception as e:
            self.control_panel.set_error(str(e))
            self.statusBar().showMessage("연결 실패")
            QMessageBox.critical(self, "연결 실패", 
                               f"포트 연결에 실패했습니다:\n{str(e)}")
            
    def on_disconnect_requested(self):
        """연결 해제 요청 처리"""
        try:
            # 모니터링 스레드 중지
            if self.monitor_thread is not None:
                self.monitor_thread.stop()
                self.monitor_thread = None
            
            # 모터 버스에서 연결 해제
            self.motor_controller.disconnect()
            
            self.control_panel.set_connected(False)
            self.statusBar().showMessage("연결 해제됨")
            
        except Exception as e:
            QMessageBox.warning(self, "연결 해제 실패", str(e))
            
    def on_emergency_stop(self):
        """긴급 정지 처리"""
        reply = QMessageBox.warning(
            self, "긴급 정지", 
            "모든 모터의 토크를 끕니다.\n계속하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.motor_controller.emergency_stop()
                if success:
                    self.statusBar().showMessage("긴급 정지 실행됨")
                    QMessageBox.information(self, "긴급 정지", 
                                          "모든 모터의 토크가 꺼졌습니다.")
            except Exception as e:
                QMessageBox.critical(self, "에러", f"긴급 정지 실패:\n{str(e)}")
                
    def on_add_motor(self):
        """모터 추가"""
        if not self.control_panel.is_connected:
            QMessageBox.warning(self, "연결 필요", 
                              "먼저 모터 버스에 연결해주세요.")
            return
            
        # 최대 6개 제한
        if len(self.motor_cards) >= 6:
            QMessageBox.warning(self, "최대 개수 도달", 
                              "최대 6개의 모터만 추가할 수 있습니다.")
            return
            
        # 사용 가능한 ID 목록
        all_ids = list(range(1, 7))
        used_ids = list(self.motor_cards.keys())
        available_ids = [i for i in all_ids if i not in used_ids]
        
        if not available_ids:
            QMessageBox.warning(self, "모터 추가 불가", 
                              "모든 모터 ID가 사용 중입니다.")
            return
            
        # ID 선택 다이얼로그
        motor_id, ok = QInputDialog.getItem(
            self, "모터 추가", 
            "모터 ID를 선택하세요:",
            [str(i) for i in available_ids],
            0, False
        )
        
        if ok and motor_id:
            motor_id = int(motor_id)
            self.add_motor_card(motor_id)
            
    def add_motor_card(self, motor_id: int):
        """모터 카드 추가"""
        if motor_id in self.motor_cards:
            return
            
        # 카드 생성
        card = MotorCard(motor_id)
        card.move_requested.connect(self.on_motor_move)
        card.delete_requested.connect(self.on_motor_delete)
        
        self.motor_cards[motor_id] = card
        
        # 그리드에 추가
        self.rearrange_cards()
        
        self.statusBar().showMessage(f"모터 ID {motor_id} 추가됨")
        
    def on_motor_delete(self, motor_id: int):
        """모터 삭제"""
        reply = QMessageBox.question(
            self, "모터 삭제", 
            f"모터 ID {motor_id}를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            card = self.motor_cards.pop(motor_id, None)
            if card:
                card.deleteLater()
                self.rearrange_cards()
                self.statusBar().showMessage(f"모터 ID {motor_id} 삭제됨")
                
    def rearrange_cards(self):
        """카드 재배치"""
        # 기존 위젯 모두 제거
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        # 모터 카드들을 ID 순서대로 배치
        sorted_ids = sorted(self.motor_cards.keys())
        row, col = 0, 0
        max_cols = 3
        
        for motor_id in sorted_ids:
            card = self.motor_cards[motor_id]
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        # 추가 카드를 마지막에 배치
        self.grid_layout.addWidget(self.add_card, row, col)
        
    def on_motor_move(self, motor_id: int, target_position: int):
        """모터 이동 명령"""
        try:
            success = self.motor_controller.move_motor(motor_id, target_position)
            if success:
                self.statusBar().showMessage(
                    f"모터 ID {motor_id} → {target_position} 이동 명령"
                )
            else:
                QMessageBox.warning(self, "이동 실패", 
                                  f"모터 ID {motor_id} 이동 명령 실패")
                
        except Exception as e:
            QMessageBox.critical(self, "이동 실패", 
                               f"모터 이동 실패:\n{str(e)}")
            
    def on_motor_connected(self):
        """모터 연결됨 신호 처리"""
        pass
    
    def on_motor_disconnected(self):
        """모터 연결 해제됨 신호 처리"""
        pass
    
    def on_motor_error(self, error_msg: str):
        """모터 에러 신호 처리"""
        self.statusBar().showMessage(f"에러: {error_msg}")
    
    def on_position_updated(self, motor_id: int, position: int):
        """모터 위치 업데이트"""
        card = self.motor_cards.get(motor_id)
        if card:
            card.update_current_position(position)
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 모니터링 스레드 중지
        if self.monitor_thread is not None:
            self.monitor_thread.stop()
        
        # 모터 연결 해제
        if self.control_panel.is_connected:
            reply = QMessageBox.question(
                self, "종료", 
                "모터 연결이 활성화되어 있습니다.\n종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.motor_controller.disconnect()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
