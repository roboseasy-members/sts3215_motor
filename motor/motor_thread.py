"""
모터 모니터링 스레드
- 백그라운드에서 모터 위치 실시간 읽기
- PyQt5 Signal으로 UI 업데이트
"""

from PyQt5.QtCore import QThread, pyqtSignal
import time


class MotorMonitorThread(QThread):
    """모터 위치를 실시간으로 모니터링하는 스레드"""
    
    # 신호
    position_updated = pyqtSignal(int, int)  # (motor_id, position)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, motor_controller, motor_ids: list, update_interval: float = 0.1):
        """
        Args:
            motor_controller: MotorController 인스턴스
            motor_ids: 모니터링할 모터 ID 리스트
            update_interval: 업데이트 간격 (초, 기본값: 0.1 = 100ms = 10Hz)
        """
        super().__init__()
        self.motor_controller = motor_controller
        self.motor_ids = motor_ids
        self.update_interval = update_interval
        self.is_running = False
    
    def run(self):
        """스레드 실행"""
        self.is_running = True
        
        while self.is_running:
            try:
                # 연결 확인
                if not self.motor_controller.is_connected:
                    time.sleep(0.1)
                    continue
                
                # 모든 모터의 현재 위치 읽기
                for motor_id in self.motor_ids:
                    try:
                        position = self.motor_controller.read_position(motor_id)
                        if position is not None:
                            self.position_updated.emit(motor_id, position)
                    except Exception as e:
                        self.error_occurred.emit(f"모터 {motor_id} 읽기 실패: {str(e)}")
                
                # 지정된 간격만큼 대기
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.error_occurred.emit(f"모니터 스레드 오류: {str(e)}")
                time.sleep(1)
    
    def stop(self):
        """스레드 중지"""
        self.is_running = False
        self.wait()  # 스레드가 완료될 때까지 대기
    
    def update_motor_ids(self, motor_ids: list):
        """모니터링할 모터 ID 업데이트"""
        self.motor_ids = motor_ids
