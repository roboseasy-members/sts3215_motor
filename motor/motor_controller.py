"""
모터 컨트롤러
- LeRobot의 FeetechMotorsBus 래핑
- 연결/해제 관리
- 모터 값 읽기/쓰기
"""

from typing import Optional, Dict, List
from PyQt5.QtCore import QObject, pyqtSignal
import time

try:
    from lerobot.motors.feetech import FeetechMotorsBus
    from lerobot.motors.motors_bus import Motor, MotorNormMode
except ImportError:
    FeetechMotorsBus = None
    Motor = None
    MotorNormMode = None


class MotorController(QObject):
    """모터 제어 컨트롤러"""
    
    # 신호
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    position_updated = pyqtSignal(int, int)  # (motor_id, position)
    
    def __init__(self, model: str = "sts3215"):
        super().__init__()
        self.port = None
        self.model = model
        self.bus = None
        self.motors = {}  # {motor_id: Motor}
        self.motor_ids = []
        self.is_connected = False
        self._check_lerobot()
        
    def _check_lerobot(self):
        """LeRobot 라이브러리 설치 확인"""
        if FeetechMotorsBus is None:
            self.error_occurred.emit(
                "LeRobot 라이브러리가 설치되지 않았습니다.\n"
                "터미널에서 다음을 실행하세요:\n"
                "git clone https://github.com/huggingface/lerobot.git\n"
                "cd lerobot\n"
                "pip install -e ."
            )
    
    def connect(self, port: str, motor_ids: List[int] = None) -> bool:
        """
        포트에 연결
        
        Args:
            port: COM 포트 (예: "COM7")
            motor_ids: 사용할 모터 ID 리스트 (기본값: [1,2,3,4,5,6])
            
        Returns:
            성공 여부
        """
        try:
            if FeetechMotorsBus is None:
                raise RuntimeError("LeRobot 라이브러리가 설치되지 않았습니다.")
            
            if motor_ids is None:
                motor_ids = [1, 2, 3, 4, 5, 6]
            
            self.port = port
            self.motor_ids = motor_ids
            
            # 모터 딕셔너리 생성
            motors = {}
            for mid in motor_ids:
                motor_name = f"joint_{mid}"
                motors[motor_name] = Motor(
                    id=mid,
                    model=self.model,
                    norm_mode=MotorNormMode.RANGE_0_100
                )
            
            # 버스 생성 및 연결
            self.bus = FeetechMotorsBus(port=port, motors=motors)
            self.bus.connect()
            
            # 모터별 초기 설정
            for mid in motor_ids:
                self._setup_motor_runtime(f"joint_{mid}")
            
            self.is_connected = True
            self.connected.emit()
            return True
            
        except Exception as e:
            error_msg = f"연결 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """연결 해제"""
        try:
            if self.bus is not None:
                # 모든 모터 토크 OFF
                for mid in self.motor_ids:
                    self._set_torque(f"joint_{mid}", 0)
                
                # 버스 연결 해제
                self.bus.disconnect()
                self.bus = None
            
            self.is_connected = False
            self.disconnected.emit()
            return True
            
        except Exception as e:
            error_msg = f"연결 해제 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def _setup_motor_runtime(self, motor_name: str, max_pos_guess: int = 4095):
        """
        모터 런타임 설정
        - 토크 OFF → 잠금 해제 → 설정 → 잠금 → 토크 ON
        """
        try:
            self.bus.write("Torque_Enable", motor_name, 0, normalize=False)
            self.bus.write("Lock", motor_name, 0, normalize=False)
        except Exception:
            pass
        
        try:
            model = self.bus.motors[motor_name].model
            max_pos = self.bus.model_resolution_table.get(model, max_pos_guess) - 1
        except Exception:
            max_pos = max_pos_guess
        
        try:
            # 포지션 모드 설정
            self.bus.write("Operating_Mode", motor_name, 0, normalize=False)
            self.bus.write("Min_Position_Limit", motor_name, 0, normalize=False)
            self.bus.write("Max_Position_Limit", motor_name, max_pos, normalize=False)
            self.bus.write("Max_Torque_Limit", motor_name, 1023, normalize=False)
            self.bus.write("Minimum_Startup_Force", motor_name, 50, normalize=False)
        except Exception as e:
            pass
        
        # 프로파일 설정 (미지원 모델 무시)
        try:
            self.bus.write("Profile_Velocity", motor_name, 300, normalize=False)
            self.bus.write("Profile_Acceleration", motor_name, 50, normalize=False)
        except Exception:
            pass
        
        try:
            self.bus.write("Lock", motor_name, 1, normalize=False)
        except Exception:
            pass
        
        # 토크 ON
        self._set_torque(motor_name, 1)
    
    def _set_torque(self, motor_name: str, value: int):
        """토크 설정 (안전 쓰기)"""
        try:
            self.bus.write("Torque_Enable", motor_name, value, normalize=False)
            return True
        except Exception:
            pass
        
        try:
            self.bus.write("Lock", motor_name, 0, normalize=False)
            self.bus.write("Torque_Enable", motor_name, value, normalize=False)
            return True
        except Exception:
            pass
        finally:
            try:
                self.bus.write("Lock", motor_name, 1, normalize=False)
            except Exception:
                pass
        
        return False
    
    def read_position(self, motor_id: int) -> Optional[int]:
        """모터 현재 위치 읽기"""
        try:
            if self.bus is None or not self.is_connected:
                return None
            
            motor_name = f"joint_{motor_id}"
            pos = self.bus.read("Present_Position", motor_name, normalize=False)
            return int(pos)
            
        except Exception as e:
            return None
    
    def read_all_positions(self) -> Dict[int, Optional[int]]:
        """모든 모터의 현재 위치 읽기"""
        positions = {}
        for mid in self.motor_ids:
            positions[mid] = self.read_position(mid)
        return positions
    
    def move_motor(self, motor_id: int, target_position: int) -> bool:
        """모터를 목표값으로 이동"""
        try:
            if self.bus is None or not self.is_connected:
                self.error_occurred.emit("모터가 연결되지 않았습니다.")
                return False
            
            motor_name = f"joint_{motor_id}"
            
            # 토크 ON 보장
            self._set_torque(motor_name, 1)
            
            # 포지션 모드 설정
            self.bus.write("Operating_Mode", motor_name, 0, normalize=False)
            
            # 목표값 설정
            self.bus.write("Goal_Position", motor_name, target_position, normalize=False)
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"모터 이동 실패: {str(e)}")
            return False
    
    def emergency_stop(self) -> bool:
        """긴급 정지 - 모든 모터 토크 OFF"""
        try:
            if self.bus is None or not self.is_connected:
                return False
            
            for mid in self.motor_ids:
                motor_name = f"joint_{mid}"
                self._set_torque(motor_name, 0)
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"긴급 정지 실패: {str(e)}")
            return False
