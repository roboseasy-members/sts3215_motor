import threading
from dataclasses import dataclass

from st3215 import ST3215


@dataclass
class MotorStatus:
    position: int = 0
    speed: int = 0
    temperature: int = 0
    voltage: float = 0.0
    current: float = 0.0
    load: int = 0
    is_moving: bool = False


class MotorController:
    def __init__(self):
        self._servo: ST3215 | None = None
        self._lock = threading.Lock()
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self, port: str) -> None:
        with self._lock:
            self._servo = ST3215(port)
            self._connected = True

    def disconnect(self) -> None:
        with self._lock:
            self._servo = None
            self._connected = False

    def scan_motors(self, id_range: range = range(1, 30)) -> list[int]:
        found = []
        with self._lock:
            if not self._servo:
                return found
            for motor_id in id_range:
                try:
                    if self._servo.PingServo(motor_id):
                        found.append(motor_id)
                except Exception:
                    continue
        return found

    def ping(self, motor_id: int) -> bool:
        with self._lock:
            if not self._servo:
                return False
            try:
                return bool(self._servo.PingServo(motor_id))
            except Exception:
                return False

    def move_to(self, motor_id: int, position: int, speed: int = 1000, acceleration: int = 50) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            self._servo.SetSpeed(motor_id, speed)
            self._servo.SetAcceleration(motor_id, acceleration)
            self._servo.MoveTo(motor_id, position)

    def read_status(self, motor_id: int) -> MotorStatus:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            s = self._servo
            return MotorStatus(
                position=s.ReadPosition(motor_id),
                speed=s.ReadSpeed(motor_id),
                temperature=s.ReadTemperature(motor_id),
                voltage=s.ReadVoltage(motor_id),
                current=s.ReadCurrent(motor_id),
                load=s.ReadLoad(motor_id),
                is_moving=s.IsMoving(motor_id),
            )

    def stop(self, motor_id: int) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            self._servo.StopServo(motor_id)

    def set_torque(self, motor_id: int, enable: bool) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            if enable:
                self._servo.StartServo(motor_id)
            else:
                self._servo.StopServo(motor_id)

    def change_id(self, current_id: int, new_id: int) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            result = self._servo.ChangeId(current_id, new_id)
            if result is not None:
                raise RuntimeError(str(result))

    def change_id_broadcast(self, new_id: int) -> None:
        """브로드캐스트로 버스에 연결된 모터의 ID를 변경한다.
        모터가 1대만 연결된 상태에서 사용해야 한다."""
        BROADCAST_ID = 0xFE
        STS_ID = 5
        STS_LOCK = 55
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            s = self._servo
            s.write1ByteTxOnly(BROADCAST_ID, STS_LOCK, 0)   # EPROM 잠금 해제
            s.write1ByteTxOnly(BROADCAST_ID, STS_ID, new_id) # ID 변경
            s.write1ByteTxOnly(BROADCAST_ID, STS_LOCK, 1)   # EPROM 잠금
